# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import web

from inginious.frontend.webapp_contest.accessible_time import AccessibleTime
from inginious.frontend.webapp_contest.pages.course_admin.utils import INGIniousAdminPage


class PlagiarismPage(INGIniousAdminPage):
    """ Plagiarism checker """

    def __init__(self, path):
        self._path = path

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        return self.page(course)

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)

        errors = []
        course_content = {}
        try:
            data = web.input()
            course_content = self.course_factory.get_course_descriptor_content(courseid)
            course_content['name'] = data['name']
            if course_content['name'] == "":
                errors.append('Invalid name')
            course_content['admins'] = list(map(str.strip, data['admins'].split(',')))
            if not self.user_manager.user_is_superadmin() and self.user_manager.session_username() not in course_content['admins']:
                errors.append('You cannot remove yourself from the administrators of this course')
            course_content['tutors'] = list(map(str.strip, data['tutors'].split(',')))
            if len(course_content['tutors']) == 1 and course_content['tutors'][0].strip() == "":
                course_content['tutors'] = []

            course_content['groups_student_choice'] = True if data["groups_student_choice"] == "true" else False

            if course_content.get('use_classrooms', True) != (data['use_classrooms'] == "true"):
                self.database.aggregations.delete_many({"courseid": course.get_id()})

            course_content['use_classrooms'] = True if data["use_classrooms"] == "true" else False

            if data["accessible"] == "custom":
                course_content['accessible'] = "{}/{}".format(data["accessible_start"], data["accessible_end"])
            elif data["accessible"] == "true":
                course_content['accessible'] = True
            else:
                course_content['accessible'] = False

            try:
                AccessibleTime(course_content['accessible'])
            except:
                errors.append('Invalid accessibility dates')

            course_content['allow_unregister'] = True if data["allow_unregister"] == "true" else False

            if data["registration"] == "custom":
                course_content['registration'] = "{}/{}".format(data["registration_start"], data["registration_end"])
            elif data["registration"] == "true":
                course_content['registration'] = True
            else:
                course_content['registration'] = False

            try:
                AccessibleTime(course_content['registration'])
            except:
                errors.append('Invalid registration dates')

            course_content['registration_password'] = data['registration_password']
            if course_content['registration_password'] == "":
                course_content['registration_password'] = None

            course_content['registration_ac'] = data['registration_ac']
            if course_content['registration_ac'] not in ["None", "username", "realname", "email"]:
                errors.append('Invalid ACL value')
            if course_content['registration_ac'] == "None":
                course_content['registration_ac'] = None
            course_content['registration_ac_list'] = data['registration_ac_list'].split("\n")
        except:
            errors.append('User returned an invalid form.')

        if len(errors) == 0:
            self.course_factory.update_course_descriptor_content(courseid, course_content)
            errors = None
            course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)  # don't forget to reload the modified course

        return self.page(course, errors, errors is None)

    def page(self, course, errors=None, saved=False):
        """ Get all data and display the page """
        if self._path is None:
            return "You need to provide the storage path of the plagiarism checker plugin in the configuration file"
        self.template_helper.add_javascript(web.ctx.homepath + '/static/webapp/js/selectize.min.js', "header")
        self.template_helper.add_css(web.ctx.homepath + '/static/webapp/css/selectize.bootstrap3.css')
        problems = [self.task_factory.get_task(course, x) for x in
                    course.get_tasks()]
        return self.template_helper.get_renderer().course_admin.plagiarism(course, problems, errors, saved)


def add_admin_menu(course): # pylint: disable=unused-argument
    """ Add a menu for the plagiarism checker in the administration """
    return ("plagiarism", "<i class='fa fa-check-circle-o fa-fw'></i>&nbsp; Plagiarism")


def init(plugin_manager, _, _2, conf):
    """
        Init the plugin.
        Available configuration in configuration.yaml:
        ::

            - plugin_module: "inginious.frontend.webapp_contest.plugins.plagiarism"
            - storage_path: 'path/to/storage/results'
    """
    page_pattern_course =  r'/admin/([^/]+)/plagiarism'
    plugin_manager.add_page(page_pattern_course, PlagiarismPage(conf.get('storage_path',None)))
    plugin_manager.add_hook('course_admin_menu', add_admin_menu)
    #plugin_manager.add_hook('course_menu', course_menu)
    #plugin_manager.add_hook('task_menu', task_menu)
