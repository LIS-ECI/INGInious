# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Pages that allow editing of tasks """
from collections import OrderedDict
import copy
import json
import bson
import os.path
import re
from zipfile import ZipFile
import logging

import web

from inginious.common.base import id_checker
import inginious.common.custom_yaml
from inginious.frontend.webapp_contest.accessible_time import AccessibleTime
from inginious.frontend.webapp_contest.tasks import WebAppTask
from inginious.frontend.webapp_contest.pages.course_admin.task_edit_file import CourseTaskFiles
from inginious.frontend.webapp_contest.pages.course_admin.utils import INGIniousAdminPage


class CourseEditTask(INGIniousAdminPage):
    """ Edit a task """
    _logger = logging.getLogger("inginious.webapp.task_edit")

    def GET_AUTH(self, courseid, taskid):  # pylint: disable=arguments-differ
        """ Edit a task """
        if not id_checker(taskid):
            raise Exception("Invalid task id")

        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)

        try:
            task_data = self.task_factory.get_task_descriptor_content(courseid, taskid)
        except:
            try:
                courseid = self.bank_name
                task_data = self.task_factory.get_task_descriptor_content(courseid, taskid)
            except:
                task_data = None
        if task_data is None:
            task_data = {}

        environments = self.containers

        current_filetype = None
        try:
            current_filetype = self.task_factory.get_task_descriptor_extension(courseid, taskid)
        except:
            pass
        available_filetypes = self.task_factory.get_available_task_file_extensions()

        # custom problem-type:
        for pid in task_data.get("problems", {}):
            problem = task_data["problems"][pid]
            if (problem["type"] == "code" and "boxes" in problem) or problem["type"] not in (
                    "code", "code-single-line", "code-file", "match", "multiple-choice"):
                problem_copy = copy.deepcopy(problem)
                for i in ["name", "header"]:
                    if i in problem_copy:
                        del problem_copy[i]
                problem["custom"] = inginious.common.custom_yaml.dump(problem_copy)
        task_list = OrderedDict([(x, open(self.verify_path(courseid, taskid, x + ".desc"), 'r').read()) for x in
                        CourseTaskFiles.convert_to_set(
                                CourseTaskFiles.get_task_filelist(self.task_factory, courseid, taskid))])
        # web.debug(task_list)

        return self.template_helper.get_renderer().course_admin.task_edit(
            course,
            taskid,
            task_data,
            environments,
            json.dumps(
                task_data.get(
                    'problems',
                    {})),
            self.contains_is_html(task_data),
            current_filetype,
            available_filetypes,
            AccessibleTime,
            task_list)

    @classmethod
    def contains_is_html(cls, data):
        """ Detect if the problem has at least one "xyzIsHTML" key """
        for key, val in data.items():
            if key.endswith("IsHTML"):
                return True
            if isinstance(val, (OrderedDict, dict)) and cls.contains_is_html(val):
                return True
        return False

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

    def parse_problem(self, problem_content):

        # store boolean fields as booleans
        for field in ["optional", "multiple", "centralize"]:
            if field in problem_content:
                problem_content[field] = True

        if "choices" in problem_content:
            problem_content["choices"] = [val for _, val in sorted(iter(problem_content["choices"].items()), key=lambda x: int(x[0]))]
            for choice in problem_content["choices"]:
                if "valid" in choice:
                    choice["valid"] = True
                if "feedback" in choice and choice["feedback"].strip() == "":
                    del choice["feedback"]

        for message in ["error_message", "success_message"]:
            if message in problem_content and problem_content[message].strip() == "":
                del problem_content[message]

        if "limit" in problem_content:
            try:
                problem_content["limit"] = int(problem_content["limit"])
            except:
                del problem_content["limit"]

        if "allowed_exts" in problem_content:
            if problem_content["allowed_exts"] == "":
                del problem_content["allowed_exts"]
            else:
                problem_content["allowed_exts"] = problem_content["allowed_exts"].split(',')

        if "max_size" in problem_content:
            try:
                problem_content["max_size"] = int(problem_content["max_size"])
            except:
                del problem_content["max_size"]

        if problem_content["type"] == "custom":
            try:
                custom_content = inginious.common.custom_yaml.load(problem_content["custom"])
            except:
                raise Exception("Invalid YAML in custom content")
            problem_content.update(custom_content)
            del problem_content["custom"]

        return problem_content

    def wipe_task(self, courseid, taskid):
        """ Wipe the data associated to the taskid from DB"""
        submissions = self.database.submissions.find({"courseid": courseid, "taskid": taskid})
        for submission in submissions:
            for key in ["input", "archive"]:
                if key in submission and type(submission[key]) == bson.objectid.ObjectId:
                    self.submission_manager.get_gridfs().delete(submission[key])

        self.database.aggregations.remove({"courseid": courseid, "taskid": taskid})
        self.database.user_tasks.remove({"courseid": courseid, "taskid": taskid})
        self.database.submissions.remove({"courseid": courseid, "taskid": taskid})

        self._logger.info("Task %s/%s wiped.", courseid, taskid)

    def verify_path(self, courseid, taskid, path, new_path=False):
        """ Return the real wanted path (relative to the INGInious root) or None if the path is not valid/allowed """

        task_dir_path = self.task_factory.get_directory_path(courseid, taskid)
        # verify that the dir exists
        if new_path == False and not os.path.exists(task_dir_path):
            return None
        wanted_path = os.path.normpath(os.path.join(task_dir_path, path))
        rel_wanted_path = os.path.relpath(wanted_path, task_dir_path)  # normalized
        # verify that the path we want exists and is withing the directory we want
        if (os.path.islink(wanted_path) or rel_wanted_path.startswith('..')):
            return None
        # do not allow touching the task.* file
        if os.path.splitext(rel_wanted_path)[0] == "task" and os.path.splitext(rel_wanted_path)[1][1:] in \
                self.task_factory.get_available_task_file_extensions():
            return None
        # do not allow hidden dir/files
        if rel_wanted_path != ".":
            for i in rel_wanted_path.split(os.path.sep):
                if i.startswith("."):
                    return None
        return wanted_path

    def upload_pfile(self, courseid, taskid, path, fileobj):
        """ Upload the problem text file """
        wanted_path = self.verify_path(courseid, taskid, path, True)
        if wanted_path is None:
            return "Invalid new path"
        curpath = self.task_factory.get_directory_path(courseid, taskid)
        if not os.path.exists(curpath):
            os.mkdir(curpath)
        rel_path = os.path.relpath(wanted_path, curpath)

        for i in rel_path.split(os.path.sep)[:-1]:
            curpath = os.path.join(curpath, i)
            if not os.path.exists(curpath):
                os.mkdir(curpath)
            if not os.path.isdir(curpath):
                return i + " is not a directory!"

        try:
            to_write = fileobj.read()
            mode = "w+b" if path != "run" else "w+"
            f = open(wanted_path, mode)
            # web.debug(wanted_path)
            f.write(to_write)
            f.close()
            return ""
        except Exception as e:
            return "An error occurred while writing the file"

    def POST_AUTH(self, courseid, taskid):  # pylint: disable=arguments-differ
        """ Edit a task """
        if not id_checker(taskid) or not id_checker(courseid):
            raise Exception("Invalid course/problem id")

        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        data = web.input(problem_file={}, task_file={})
        previous_courseid = courseid

        # Task exists?
        try:
            self.task_factory.get_task(course, taskid)
        except:
            # If doesn't, use bank instead
            courseid = self.bank_name
            course = self.course_factory.get_course(courseid)

        # Delete task ?
        if "delete" in data:
            try:
                self.task_factory.delete_task(courseid, taskid)
            except:
                raise web.seeother("/admin/" + previous_courseid + "/tasks")
            if data.get("wipe", False):
                self.wipe_task(courseid, taskid)
            raise web.seeother("/admin/"+previous_courseid+"/tasks")

        # Else, parse content
        try:
            task_zip = data.get("task_file").file
        except:
            task_zip = None
        del data["task_file"]

        try:
            problem_file = data.get('problem_file')
        except Exception as e:
            problem_file = None
        del data["problem_file"]

        problems = self.dict_from_prefix("problem", data)
        limits = self.dict_from_prefix("limits", data)

        data = {key: val for key, val in data.items() if not key.startswith("problem") and not key.startswith("limits")}
        del data["@action"]

        if data["@filetype"] not in self.task_factory.get_available_task_file_extensions():
            return json.dumps({"status": "error", "message": "Invalid file type: {}".format(str(data["@filetype"]))})
        file_ext = data["@filetype"]
        del data["@filetype"]
        if problems is None:
            problems = {'1': {"type": "code-file", "header": "", "allowed_exts": ".py"}}
            #return json.dumps({"status": "error", "message": "You cannot create a task without subproblems"})

        # Order the problems (this line also deletes @order from the result)
        data["problems"] = OrderedDict([(key, self.parse_problem(val)) for key, val in problems.items()])
        data["limits"] = limits
        data["limits"]["time"]=30
        if "hard_time" in data["limits"] and data["limits"]["hard_time"] == "":
            del data["limits"]["hard_time"]

        if problem_file is not None:
            self.upload_pfile(courseid, taskid, "public/"+taskid+".pdf",
                              problem_file.file if not isinstance(problem_file, str) else problem_file)

        # web.debug(self.run_file)
        if self.run_file is not None:
            with open(self.run_file) as f:
                # web.debug("F",f)
                self.upload_pfile(courseid, taskid, "run", f)
            wanted_path = self.verify_path(courseid, taskid, "run", True)
            os.system("sed -i -e 's/REPLACEWITHTIME/"+str(data["real_time"])+"/g' " + wanted_path)

        # Difficulty
        try:
            data["difficulty"] = int(data["difficulty"])
            if not (data["difficulty"] > 0 and data["difficulty"] <= 10):
                return json.dumps({"status": "error", "message": "Difficulty level must be between 1 and 10"})
        except:
            return json.dumps({"status": "error", "message": "Difficulty level must be an integer number"})

        # Name
        if len(data["name"])==0:
            return json.dumps({"status": "error", "message": "Field 'name' must have non-empty."})

        # Weight
        try:
            data["weight"] = 1.0
        except:
            return json.dumps({"status": "error", "message": "Grade weight must be a floating-point number"})

        try:
            data["authenticity_percentage"] = float(data["authenticity_percentage"])
        except:
            return json.dumps({"status": "error", "message": "Authenticity percentage must be a floating-point number"})

        # Groups
        if "groups" in data:
            data["groups"] = True if data["groups"] == "true" else False

        # Submission storage
        if "store_all" in data:
            try:
                stored_submissions = data["stored_submissions"]
                data["stored_submissions"] = 0 if data["store_all"] == "true" else int(stored_submissions)
            except:
                return json.dumps(
                    {"status": "error", "message": "The number of stored submission must be positive!"})

            if data["store_all"] == "false" and data["stored_submissions"] <= 0:
                return json.dumps({"status": "error", "message": "The number of stored submission must be positive!"})
            del data['store_all']

        # Submission limits
        if "submission_limit" in data:
            if data["submission_limit"] == "none":
                result = {"amount": -1, "period": -1}
            elif data["submission_limit"] == "hard":
                try:
                    result = {"amount": int(data["submission_limit_hard"]), "period": -1}
                except:
                    return json.dumps({"status": "error", "message": "Invalid submission limit!"})

            else:
                try:
                    result = {"amount": int(data["submission_limit_soft_0"]), "period": int(data["submission_limit_soft_1"])}
                except:
                    return json.dumps({"status": "error", "message": "Invalid submission limit!"})

            del data["submission_limit_hard"]
            del data["submission_limit_soft_0"]
            del data["submission_limit_soft_1"]
            data["submission_limit"] = result

        data["accessible"] = True

        # Checkboxes
        if data.get("responseIsHTML"):
            data["responseIsHTML"] = True

        # Network grading
        data["network_grading"] = "network_grading" in data
        data["code_analysis"] = "code_analysis" in data
        if data["code_analysis"] and self.run_file is not None:
            os.system("sed -i -e 's/#STATIC//g' " + wanted_path)
        # Get the course
        try:
            course = self.course_factory.get_course(courseid)
        except:
            return json.dumps({"status": "error", "message": "Error while reading course's informations"})

        # Get original data
        try:
            orig_data = self.task_factory.get_task_descriptor_content(courseid, taskid)
            data["order"] = orig_data["order"]
        except:
            pass

        directory_path = self.task_factory.get_directory_path(courseid, taskid)
        try:
            WebAppTask(course, taskid, data, directory_path, self.plugin_manager)
        except Exception as message:
            return json.dumps({"status": "error", "message": "Invalid data: {}".format(str(message))})

        if not os.path.exists(directory_path):
            os.mkdir(directory_path)

        if task_zip:
            try:
                zipfile = ZipFile(task_zip)
            except Exception as message:
                return json.dumps({"status": "error", "message": "Cannot read zip file. Files were not modified"})

            try:
                zipfile.extractall(directory_path)
            except Exception as message:
                return json.dumps(
                    {"status": "error", "message": "There was a problem while extracting the zip archive. Some files may have been modified"})

        self.task_factory.delete_all_possible_task_files(courseid, taskid)
        self.task_factory.update_task_descriptor_content(courseid, taskid, data, force_extension=file_ext)

        return json.dumps({"status": "ok"})
