from collections import OrderedDict
import copy
from datetime import datetime, timedelta

import pymongo
import web
from bson import ObjectId

from inginious.frontend.webapp_contest.pages.utils import INGIniousAuthPage
from inginious.frontend.webapp_contest.pages.course_admin.utils import INGIniousAdminPage
from inginious.frontend.webapp_contest.accessible_time import AccessibleTime
from pymongo import ReturnDocument


class ContestClarificationsPageAdmin(INGIniousAdminPage):
    """ Clarifications list for a contest """

    def save_contest_data(self, course, contest_data):
        """ Saves updated contest data for the course """
        course_content = self.course_factory.get_course_descriptor_content(course.get_id())
        course_content["contest_settings"] = contest_data
        self.course_factory.update_course_descriptor_content(course.get_id(), course_content)

    def GET_AUTH(self, courseid, contestid):  # pylint: disable=arguments-differ
        """ GET request: simply display the form """
        course, _ = self.get_course_and_check_rights(courseid)
        data = list(self.database.clarifications.find(({"contest": contestid, "course": courseid})))
        for clarification in data:
            if len(clarification["text"]) > 40:
                clarification["text"] = clarification["text"][:min(40, len(clarification["text"]))] + "..."
        #web.debug(data, courseid, contestid)
        #return self.template_helper.get_custom_renderer('frontend/webapp_contest/plugins/contests').admin(course, contest_data, None, False)
        self.template_helper.add_javascript(web.ctx.homepath + '/static/webapp/js/studio_contest.js', 'header')
        return self.template_helper.get_renderer().course_admin.clarifications(course, data, None, AccessibleTime, contestid)

    def POST_AUTH(self, courseid, contestid):  # pylint: disable=arguments-differ
        """ POST request: update the settings """
        return web.notfound()

class AnswerClarificationPageAdmin(INGIniousAdminPage):
    """ Page to answer a clarification """

    def GET_AUTH(self, courseid, contestid, clarificationid):  # pylint: disable=arguments-differ
        """ GET request: simply display the form """
        course, _ = self.get_course_and_check_rights(courseid)

        try:
            data = self.database.clarifications.find_one(({"contest": contestid, "course": courseid, "_id" : ObjectId(clarificationid)}))
        except:
            raise web.notfound()
        if data is None:
            raise web.notfound()
        #web.debug(data, courseid, contestid, clarificationid)

        users = sorted(list(self.user_manager.get_users_info(self.user_manager.get_course_registered_users(course, False)).items()),
                       key=lambda k: k[1][0] if k[1] is not None else "")

        users = OrderedDict(sorted(list(self.user_manager.get_users_info(course.get_staff()).items()),
                                   key=lambda k: k[1][0] if k[1] is not None else "") + users)

        users = [x for x,y in users.items()]

        #web.debug(users)

        #return self.template_helper.get_custom_renderer('frontend/webapp_contest/plugins/contests').admin(course, contest_data, None, False)
        self.template_helper.add_javascript(web.ctx.homepath + '/static/webapp/js/studio_contest.js', 'header')
        return self.template_helper.get_renderer().course_admin.clarification_answer(course, data, None, AccessibleTime, clarificationid, contestid, False, users)

    def POST_AUTH(self, courseid, contestid, clarificationid):  # pylint: disable=arguments-differ
        """ POST request: update the clarification """
        course, _ = self.get_course_and_check_rights(courseid)

        data = web.input()

        clarification_data = self.database.clarifications.find_one(
            ({"contest": contestid, "course": courseid, "_id": ObjectId(clarificationid)}))
        errors = []
        saved = False
        if clarification_data.get("response","") == "":
            if data["response"]!="":
                user = self.user_manager.session_username()
                #time = datetime.datetime.now().strftime("%Y%m%d.%H%M%S")
                clarification_data = self.database.clarifications.find_one_and_update({"_id" : ObjectId(clarificationid)},
                                                           {"$set": {
                                                               "response": data["response"],
                                                               "to": data["to"],
                                                               "answered_by": user
                                                           }},return_document=ReturnDocument.AFTER)
                saved = True
            else:
                errors.append("Response cannot be empty")
        else:
            errors.append("This clarification has been previously answered")
        #web.debug(saved)

        users = sorted(list(
            self.user_manager.get_users_info(self.user_manager.get_course_registered_users(course, False)).items()),
                       key=lambda k: k[1][0] if k[1] is not None else "")

        users = OrderedDict(sorted(list(self.user_manager.get_users_info(course.get_staff()).items()),
                                   key=lambda k: k[1][0] if k[1] is not None else "") + users)

        users = [x for x, y in users.items()]

        return self.template_helper.get_renderer().course_admin.clarification_answer(course, clarification_data, errors, AccessibleTime, clarificationid, contestid, saved, users)