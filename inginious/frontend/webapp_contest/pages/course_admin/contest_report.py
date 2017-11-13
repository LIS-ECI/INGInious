from collections import OrderedDict
import copy
from datetime import datetime, timedelta

import pymongo
import web

from inginious.frontend.webapp_contest.pages.utils import INGIniousAuthPage
from inginious.frontend.webapp_contest.pages.course_admin.utils import make_csv, INGIniousAdminPage
from inginious.frontend.webapp_contest.accessible_time import AccessibleTime

class ContestReportPage(INGIniousAdminPage):
    """ Contest settings for a course """

    def save_contest_data(self, course, contest_data):
        """ Saves updated contest data for the course """

    def GET_AUTH(self, courseid, contestid):  # pylint: disable=arguments-differ
        """ GET request: simply display the form """
        course, _ = self.get_course_and_check_rights(courseid)
        contests_data = self.contest_manager.get_all_contest_data(course)
        course, start, end, blackout, tasks, results, activity, contestid, contest_name = self.contest_manager.get_data(
            courseid, contestid, False)
        for username, data in results.items():
            for d,value in data['tasks'].items():
                if value.get('time','') != '':
                    value['time'] = value.get('time','').strftime("%Y-%m-%d %H:%M:%S")
                else:
                    value['time'] = ''
        if "csv" in web.input():
            return make_csv(results)
        #return self.template_helper.get_custom_renderer('frontend/webapp_contest/plugins/contests').admin(course, contest_data, None, False)
        self.template_helper.add_javascript(web.ctx.homepath + '/static/webapp/js/Blob.min.js', "header")
        self.template_helper.add_javascript(web.ctx.homepath + '/static/webapp/js/xlsx.core.min.js', "header")
        self.template_helper.add_javascript(web.ctx.homepath + '/static/webapp/js/FileSaver.min.js', "header")
        self.template_helper.add_javascript(web.ctx.homepath + '/static/webapp/js/tableexport.min.js', "header")
        self.template_helper.add_css(web.ctx.homepath + '/static/webapp/css/tableexport.min.css')
        return self.template_helper.get_renderer().course_admin.contest_report(course, tasks, results, None, AccessibleTime)

    def POST_AUTH(self, courseid, contestid):  # pylint: disable=arguments-differ
        """ POST request: update the settings """
        return web.notfound()