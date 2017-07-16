# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" An algorithm contest plugin for INGInious. Based on the same principles than contests like ACM-ICPC. """

from collections import OrderedDict
from datetime import datetime, timedelta

import web
import json
import re

from inginious.frontend.webapp_contest.pages.utils import INGIniousAuthPage
from inginious.frontend.webapp_contest.pages.course_admin.utils import INGIniousAdminPage
from inginious.frontend.webapp_contest.accessible_time import AccessibleTime


def add_admin_menu(course): # pylint: disable=unused-argument
    """ Add a menu for the contest settings in the administration """
    return ('contest', '<i class="fa fa-trophy fa-fw"></i>&nbsp; Contest')


"""def task_accessibility(course, task, default): # pylint: disable=unused-argument
    contest_data = self.get_contest_data(course)
    if contest_data['enabled']:
        return AccessibleTime(contest_data['start'] + '/')
    else:
        return default
"""

def additional_headers():
    """ Additional HTML headers """
    return '<link href="' + web.ctx.homepath \
           + '/static/webapp/plugins/contests/scoreboard.css" rel="stylesheet">' \
             '<script src="' + web.ctx.homepath + '/static/webapp/plugins/contests/jquery.countdown.min.js"></script>' \
             '<script src="' + web.ctx.homepath + '/static/webapp/plugins/contests/contests.js"></script>'


class ContestScoreboard(INGIniousAuthPage):
    """ Displays the scoreboard of the contest """

    def GET_AUTH(self, courseid, contestid):  # pylint: disable=arguments-differ

        course, start, end, blackout, tasks, results, activity, contestid, contest_name = self.contest_manager.get_data(courseid, contestid, False)
        return self.template_helper.get_custom_renderer('frontend/webapp_contest/plugins/contests'). \
            scoreboard(course, start, end, blackout, tasks, results, activity, contestid, contest_name)

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
        if int(contestid)==len(course_content["contest"]):
            course_content["contest"].append(contest_data)
        else:
            course_content["contest"][int(contestid)] = contest_data
        self.course_factory.update_course_descriptor_content(course.get_id(), course_content)

    def GET_AUTH(self, courseid, contestid):  # pylint: disable=arguments-differ
        """ GET request: simply display the form """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        contest_data = self.contest_manager.get_contest_data(course, contestid)
        problems = [self.task_factory.get_task(self.course_factory.get_course('bank'), x) for x in self.course_factory.get_course('bank').get_tasks()]
        problemdump = json.dumps({x: {"id": x} for x in contest_data["content"]})
        #return self.template_helper.get_custom_renderer('frontend/webapp_contest/plugins/contests').admin(course, contest_data, None, False)
        return self.template_helper.get_renderer().course_admin.contest_edit(course, contest_data, None, False, AccessibleTime, problems, problemdump)

    def POST_AUTH(self, courseid, contestid):  # pylint: disable=arguments-differ
        """ POST request: update the settings """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        contest_data = self.contest_manager.get_contest_data(course, contestid)
        new_data = web.input()

        # Delete task ?
        if "delete" in new_data:
            self.contest_manager.delete_contest(courseid, contestid)
            raise web.seeother("/admin/"+courseid+"/contest")
        try:
            contest_data['enabled'] = new_data.get('enabled', '0') == '1'
            contest_data['start'] = new_data["start"]
            contest_data['end'] = new_data["end"]
            contest_data['name'] = new_data["name"]
            try:
                problems = [key for key, val in self.dict_from_prefix("problem", new_data).items()]
            except:
                return json.dumps({"status": "error", "message": "You cannot create a contest without problems"})

            # Order the problems (this line also deletes @order from the result)
            contest_data["content"] = problems

            try:
                start = datetime.strptime(contest_data['start'], "%Y-%m-%d %H:%M:%S")
            except:
                return json.dumps({"status": "error", "message": "Invalid start date"})
            try:
                end = datetime.strptime(contest_data['end'], "%Y-%m-%d %H:%M:%S")
            except:
                return json.dumps({"status": "error", "message": "Invalid end date"})

            if start >= end:
                return json.dumps({"status": "error", "message": "Start date should be before end date"})
                    
            try:
                contest_data['penalty'] = int(new_data["penalty"])
                if contest_data['penalty'] < 0:
                    return json.dumps({"status": "error", "message": "Invalid number of minutes for the penalty: should be greater than 0"})
            except:
                return json.dumps({"status": "error", "message": "Invalid number of minutes for the penalty"})
        except:
            return json.dumps({"status": "error", "message": "User returned an invalid form"})

        self.save_contest_data(course, contest_data, contestid)
        return json.dumps({"status": "ok"})


def init(plugin_manager, course_factory, client, config):  # pylint: disable=unused-argument
    """
        Init the contest plugin.
        Available configuration:
        ::

            {
                "plugin_module": "inginious.frontend.webapp_contest.plugins.contests"
            }
    """

    plugin_manager.add_page('/contest/([^/]+)/([^/]+)/scoreboard', ContestScoreboard)
    plugin_manager.add_page('/admin/([^/]+)/([^/]+)/contest', ContestAdmin)
    plugin_manager.add_hook('course_admin_menu', add_admin_menu)
    #plugin_manager.add_hook('task_accessibility', task_accessibility)
    plugin_manager.add_hook('header_html', additional_headers)
