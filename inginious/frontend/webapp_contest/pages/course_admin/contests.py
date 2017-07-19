from collections import OrderedDict
import copy
from datetime import datetime, timedelta

import pymongo
import web

from inginious.frontend.webapp_contest.pages.utils import INGIniousAuthPage
from inginious.frontend.webapp_contest.pages.course_admin.utils import INGIniousAdminPage
from inginious.frontend.webapp_contest.accessible_time import AccessibleTime

class ContestsPageAdmin(INGIniousAdminPage):
    """ Contest settings for a course """

    def save_contest_data(self, course, contest_data):
        """ Saves updated contest data for the course """
        course_content = self.course_factory.get_course_descriptor_content(course.get_id())
        course_content["contest_settings"] = contest_data
        self.course_factory.update_course_descriptor_content(course.get_id(), course_content)

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request: simply display the form """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        contests_data = self.contest_manager.get_all_contest_data(course)
        #return self.template_helper.get_custom_renderer('frontend/webapp_contest/plugins/contests').admin(course, contest_data, None, False)
        self.template_helper.add_javascript(web.ctx.homepath + '/static/webapp/js/studio_contest.js', 'header')
        return self.template_helper.get_renderer().course_admin.contest_list(course, contests_data, None, AccessibleTime)

    def POST_AUTH(self, courseid, contestid):  # pylint: disable=arguments-differ
        """ POST request: update the settings """
        return web.notfound()