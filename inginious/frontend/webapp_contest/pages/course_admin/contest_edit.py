from collections import OrderedDict
from datetime import datetime, timedelta

import web
import json
import re
import shutil

from inginious.frontend.webapp_contest.pages.course_admin.utils import INGIniousAdminPage
from inginious.frontend.webapp_contest.accessible_time import AccessibleTime

class ContestAdmin(INGIniousAdminPage):
    """ Contest settings for a course """

    @classmethod
    def dict_from_prefix(cls, prefix, dictionary):
        """
            >>> from collections import OrderedDict
            >>> od = OrderedDict()
            >>> od["problem[q0][a]"]=1
            >>> od["problem[q0][b][c]"]=2
            >>> od["problem[q1][first]"]=1
            >>> od["problem[q1][second]"]=2
            >>> AdminCourseEditTask.dict_from_prefix("problem",od)
            OrderedDict([('q0', OrderedDict([('a', 1), ('b', OrderedDict([('c', 2)]))])), ('q1', OrderedDict([('first', 1), ('second', 2)]))])
        """
        o_dictionary = OrderedDict()
        for key, val in dictionary.items():
            if key.startswith(prefix):
                o_dictionary[key[len(prefix):].strip()] = val
        dictionary = o_dictionary

        if len(dictionary) == 0:
            return None
        elif len(dictionary) == 1 and "" in dictionary:
            return dictionary[""]
        else:
            return_dict = OrderedDict()
            for key, val in dictionary.items():
                ret = re.search(r"^\[([^\]]+)\](.*)$", key)
                if ret is None:
                    continue
                return_dict[ret.group(1)] = cls.dict_from_prefix("[{}]".format(ret.group(1)), dictionary)
            return return_dict

    def save_contest_data(self, course, contest_data, contestid):
        """ Saves updated contest data for the course """
        course_content = self.course_factory.get_course_descriptor_content(course.get_id())
        if course_content.get("contest",None) is None:
            course_content.update({'contest': []})
        if int(contestid) == len(course_content.get("contest",{})):
            course_content["contest"].append(contest_data)
        else:
            course_content["contest"][int(contestid)] = contest_data
        self.course_factory.update_course_descriptor_content(course.get_id(), course_content)

    def GET_AUTH(self, courseid, contestid):  # pylint: disable=arguments-differ
        """ GET request: simply display the form """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        contest_data = self.contest_manager.get_contest_data(course, contestid)
        problems = [self.task_factory.get_task(self.course_factory.get_course(self.bank_name), x) for x in
                    self.course_factory.get_course(self.bank_name).get_tasks()]
        problemdump = json.dumps({x: {"id": x} for x in contest_data.get("content",[])})
        if problemdump is None:
            problemdump = json.dumps({})
        self.template_helper.add_javascript(web.ctx.homepath + '/static/webapp/js/studio_contest.js', 'header')
        self.template_helper.add_javascript(web.ctx.homepath + '/static/webapp/js/selectize.min.js', "header")
        self.template_helper.add_css(web.ctx.homepath + '/static/webapp/css/selectize.bootstrap3.css')


        techniques = self.contest_manager.get_all_techniques(self.bank_name)
        structures = self.contest_manager.get_all_structures(self.bank_name)
        return self.template_helper.get_renderer().course_admin.contest_edit(course, contest_data, None, False,
                                                                             AccessibleTime, problems, problemdump, self.bank_name, techniques, structures)

    def migrate_data(self, course, dest_course, dest_tasks):
        """ migrate tasks """

        for task in dest_tasks:
            try:
                path = self.task_factory.get_directory_path(course, task)
                dest_path = self.task_factory.get_directory_path(dest_course, task)
                shutil.copytree(path, dest_path)
            except Exception as e:
                continue
        return 0

    def POST_AUTH(self, courseid, contestid):  # pylint: disable=arguments-differ
        """ POST request: update the contest settings """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        contest_data = self.contest_manager.get_contest_data(course, contestid)
        new_data = web.input()

        # Delete contest ?
        if "delete" in new_data:
            self.contest_manager.delete_contest(courseid, contestid)
            raise web.seeother("/admin/" + courseid + "/contest")

        #web.debug(new_data)

        if "generate" in new_data and new_data["generate"]=="1":
            data = [value for key, value in self.dict_from_prefix("type", new_data).items()]
            other_problems = [value for key, value in self.dict_from_prefix("problem", new_data).items()]
            #web.debug(data)
            try:
                new_problems = self.contest_manager.get_random_contest(data, other_problems)
                #web.debug(new_problems)
                return json.dumps({"status": "ok", "message": str(new_problems)})
            except Exception as e:
                return json.dumps({"status": "error", "message": str(e)})

        if "get_problems" in new_data and new_data["get_problems"]=="1":
            other_problems = [value for key, value in self.dict_from_prefix("problem", new_data).items()]
            try:

                diff = new_data.get("add-difficulty_cloned")
                if len(diff) == 0:
                    diff = 1
                new_problems = len(self.contest_manager.get_problems(new_data["add-technique_cloned"], new_data["add-structure_cloned"], diff, other_problems))
                #web.debug(new_problems)
                return json.dumps({"status": "ok", "message": new_problems})
            except Exception as e:
                return json.dumps({"status": "error", "message": str(e)})

        try:
            contest_data['enabled'] = new_data.get('enabled', '0') == '1'
            contest_data['start'] = new_data["start"]
            contest_data['end'] = new_data["end"]
            contest_data['name'] = new_data["name"]
            contest_data['description'] = new_data["description"]
            try:
                problems = [key for key, val in self.dict_from_prefix("problem", new_data).items()]
            except:
                return json.dumps({"status": "error", "message": "You cannot create a contest without problems"})

            # Save the problems
            contest_data["content"] = problems

            # Copy problems
            self.migrate_data(self.bank_name, course.get_id(), problems)

            # Save start date
            try:
                start = datetime.strptime(contest_data['start'], "%Y-%m-%d %H:%M:%S")
            except:
                return json.dumps({"status": "error", "message": "Invalid start date"})

            # Save end date
            try:
                end = datetime.strptime(contest_data['end'], "%Y-%m-%d %H:%M:%S")
            except:
                return json.dumps({"status": "error", "message": "Invalid end date"})

            if start >= end:
                return json.dumps({"status": "error", "message": "Start date should be before end date"})

            # Save penalty
            try:
                contest_data['penalty'] = int(new_data["penalty"])
                if contest_data['penalty'] < 0:
                    return json.dumps({"status": "error",
                                       "message": "Invalid number of minutes for the penalty: should be greater than 0"})
            except:
                return json.dumps({"status": "error", "message": "Invalid number of minutes for the penalty"})


        except:
            return json.dumps({"status": "error", "message": "User returned an invalid form"})

        # Save data
        self.save_contest_data(course, contest_data, contestid)
        return json.dumps({"status": "ok"})
