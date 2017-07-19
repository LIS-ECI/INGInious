# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Course page """

from collections import OrderedDict


import web

from inginious.frontend.webapp_contest.pages.utils import INGIniousAuthPage


class CoursePage(INGIniousAuthPage):
    """ Course page """

    def get_course(self, courseid):
        """ Return the course """
        try:
            course = self.course_factory.get_course(courseid)
        except:
            raise web.notfound()

        return course

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        course = self.get_course(courseid)

        user_input = web.input()
        if "unregister" in user_input and course.allow_unregister():
            self.user_manager.course_unregister_user(course, self.user_manager.session_username())
            raise web.seeother('/index')

        return self.show_page(course)

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course = self.get_course(courseid)
        return self.show_page(course)

    def show_page(self, course):
        """ Prepares and shows the course page """
        username = self.user_manager.session_username()
        if not self.user_manager.course_is_open_to_user(course):
            return self.template_helper.get_renderer().course_unavailable()
        else:
            username = self.user_manager.session_username()
            realname = self.user_manager.session_realname()
            email = self.user_manager.session_email()

            scoreboard = course.get_descriptor().get('contest', [])
            names = {i: val for i, val in enumerate(scoreboard)}

            return self.template_helper.get_renderer().course(course, names)
