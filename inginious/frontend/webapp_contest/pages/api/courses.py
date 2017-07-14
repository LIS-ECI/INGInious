# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Courses """

from inginious.frontend.webapp_contest.pages.api._api_page import APIAuthenticatedPage, APINotFound


class APICourses(APIAuthenticatedPage):
    r"""
        Endpoint /api/v0/courses(/[a-zA-Z_\-\.0-9]+)?
    """

    def API_GET(self, courseid=None):  # pylint: disable=arguments-differ
        """
            List courses available to the connected client. Returns a dict in the form

            ::

                {
                    "courseid1":
                    {
                        "name": "Name of the course",     #the name of the course
                        "require_password": False,        #indicates if this course requires a password or not
                        "is_registered": False,           #indicates if the user is registered to this course or not
                        "tasks":                          #only appears if is_registered is True
                        {
                            "taskid1": "name of task1",
                            "taskid2": "name of task2"
                            #...
                        },
                        "grade": 0.0                      #the current grade in the course. Only appears if is_registered is True
                    }
                    #...
                }

            If you use the endpoint /api/v0/courses/the_course_id, this dict will contain one entry or the page will return 404 Not Found.
        """
        output = []

        if courseid is None:
            courses = self.course_factory.get_all_courses()
        else:
            try:
                courses = {courseid: self.course_factory.get_course(courseid)}
            except:
                raise APINotFound("Course not found")

        username = self.user_manager.session_username()
        realname = self.user_manager.session_realname()
        email = self.user_manager.session_email()

        for courseid, course in courses.items():
            if self.user_manager.course_is_open_to_user(course, username) or course.is_registration_possible(username, realname, email):
                data = {
                    "id": courseid,
                    "name": course.get_name(),
                    "require_password": course.is_password_needed_for_registration(),
                    "is_registered": self.user_manager.course_is_open_to_user(course, username)
                }
                if self.user_manager.course_is_open_to_user(course, username):
                    data["tasks"] = {taskid: task.get_name() for taskid, task in course.get_tasks().items()}
                    data["grade"] = self.user_manager.get_course_cache(username, course)["grade"]
                output.append(data)

        return 200, output
