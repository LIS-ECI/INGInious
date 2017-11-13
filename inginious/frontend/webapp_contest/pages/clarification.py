# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Course page """

from collections import OrderedDict

import datetime
import web
from bson import ObjectId
from inginious.frontend.webapp_contest.accessible_time import AccessibleTime

from inginious.frontend.webapp_contest.pages.utils import INGIniousAuthPage
from pymongo import DESCENDING


class ClarificationListPage(INGIniousAuthPage):
    """ Clarifications list for a contest """

    def GET_AUTH(self, courseid, contestid):  # pylint: disable=arguments-differ
        """ GET request: simply display the form """
        username = self.user_manager.session_username()
        course = self.course_factory.get_course(courseid)
        if not self.contest_manager.exists_contest(courseid, contestid):
            return self.template_helper.get_renderer().contest_unavailable()
        elif not self.user_manager.course_is_open_to_user(course):
            return self.template_helper.get_renderer().contest_unavailable()
        else:
            data = list(self.database.clarifications.find({"$or":
                                                        [
                                                            {"to": username},
                                                            {"to":"*"},
                                                            {"from": username}
                                                        ],
                                                           "contest": contestid, "course": courseid}).sort([("time", DESCENDING)]))
            for clarification in data:
                if len(clarification["text"]) > 40:
                    clarification["text"] =clarification["text"][:min(40,len(clarification["text"]))]+"..."
            self.template_helper.add_javascript(web.ctx.homepath + '/static/webapp/js/studio_contest.js', 'header')
            course, start, end, blackout, tasks, results, activity, contestid, contest_name = self.contest_manager.get_data(courseid, contestid, False)
            return self.template_helper.get_renderer().clarifications(course, data, None, AccessibleTime, contestid, contest_name)

    def POST_AUTH(self, courseid, contestid):  # pylint: disable=arguments-differ
        """ POST request: update the settings """
        return web.notfound()


class ClarificationDetailPage(INGIniousAuthPage):
    """ Clarifications detail for a contest """

    def GET_AUTH(self, courseid, contestid, clarificationid):  # pylint: disable=arguments-differ
        """ GET request: simply display the form """
        username = self.user_manager.session_username()
        course = self.course_factory.get_course(courseid)
        if not self.contest_manager.exists_contest(courseid, contestid):
            return self.template_helper.get_renderer().contest_unavailable()
        elif not self.user_manager.course_is_open_to_user(course):
            return self.template_helper.get_renderer().contest_unavailable()
        else:
            try:
                data = self.database.clarifications.find_one(
                    ({"contest": contestid, "course": courseid, "_id": ObjectId(clarificationid)}))
                if data["response"] == "":
                    data["response"] = "Not answered yet."

            except:
                raise web.notfound()
            if data is None:
                raise web.notfound()
            self.template_helper.add_javascript(web.ctx.homepath + '/static/webapp/js/studio_contest.js', 'header')
            course, start, end, blackout, tasks, results, activity, contestid, contest_name = self.contest_manager.get_data(courseid, contestid, False)
            return self.template_helper.get_renderer().clarifications_detail(course, data, None, AccessibleTime, clarificationid, contestid, contest_name)

    def POST_AUTH(self, courseid, contestid):  # pylint: disable=arguments-differ
        """ POST request: update the settings """
        return web.notfound()


class ClarificationRequestPage(INGIniousAuthPage):
    """ Clarification request for a contest """

    def GET_AUTH(self, courseid, contestid):  # pylint: disable=arguments-differ
        """ GET request: simply display the form """
        username = self.user_manager.session_username()
        course = self.course_factory.get_course(courseid)
        if not self.contest_manager.exists_contest(courseid, contestid):
            return self.template_helper.get_renderer().contest_unavailable()
        elif not self.user_manager.course_is_open_to_user(course):
            return self.template_helper.get_renderer().contest_unavailable()
        else:
            contest_data = self.contest_manager.get_contest_data(course, contestid)
            tasks = self.course_factory.get_course(self.bank_name).get_tasks()
            tasks = [y for x,y in tasks.items() if x in (contest_data.get("content", []))]
            self.template_helper.add_javascript(web.ctx.homepath + '/static/webapp/js/studio_contest.js', 'header')
            course, start, end, blackout, tasks, results, activity, contestid, contest_name = self.contest_manager.get_data(courseid, contestid, False)
            return self.template_helper.get_renderer().clarifications_new(course, tasks, None, AccessibleTime, contestid, contest_name)

    def POST_AUTH(self, courseid, contestid):  # pylint: disable=arguments-differ
        """ POST request: update the settings """
        course = self.course_factory.get_course(courseid)
        if not self.contest_manager.exists_contest(courseid, contestid):
            return self.template_helper.get_renderer().contest_unavailable()
        elif not self.user_manager.course_is_open_to_user(course):
            return self.template_helper.get_renderer().contest_unavailable()
        else:
            data = web.input()
            username = self.user_manager.session_username()
            if len(data["text"])<=200 and len(data["subject"])<=200:
                new_clarification = {
                    "time": datetime.datetime.now(),
                    "from": username,
                    "subject": data["subject"],
                    "text": data["text"],
                    "contest": contestid,
                    "course": course.get_id(),
                    "response": "",
                    "answered_by": -1
                }
                self.database.clarifications.insert(new_clarification)
                raise web.seeother("/contest/" + courseid + "/" + contestid + "/clarifications")
            else:
                raise web.notfound()
