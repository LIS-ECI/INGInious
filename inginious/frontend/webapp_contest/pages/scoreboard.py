import web

from inginious.frontend.webapp_contest.pages.utils import INGIniousAuthPage

class ContestScoreboard(INGIniousAuthPage):
    """ Displays the scoreboard of the contest """

    def GET_AUTH(self, courseid, contestid):  # pylint: disable=arguments-differ
        course = self.course_factory.get_course(courseid)
        if not self.user_manager.course_is_open_to_user(course):
            return self.template_helper.get_renderer().contest_unavailable()
        elif not self.contest_manager.contest_is_enabled(courseid, contestid):
            return self.template_helper.get_renderer().contest_unavailable()
        else:
            self.contest_manager.add_headers()
            course, start, end, blackout, tasks, results, activity, contestid, contest_name = self.contest_manager.get_data(courseid, contestid, False)
            return self.template_helper.get_renderer(). \
                scoreboard(course, start, end, blackout, tasks, results, activity, contestid, contest_name)
