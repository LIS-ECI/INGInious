import web

from inginious.frontend.webapp_contest.pages.utils import INGIniousAuthPage
from inginious.frontend.webapp_contest.pages.utils import INGIniousPage

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
                scoreboard(course, start, end, blackout, tasks, results, activity, contestid, contest_name, False)


class PublicContestScoreboard(INGIniousPage):
    """ Displays the scoreboard of the contest """

    def GET(self, courseid, contestid):  # pylint: disable=arguments-differ
        course = self.course_factory.get_course(courseid)
        contestid = self.contest_manager.get_last_contest_id(courseid)
        if not self.contest_manager.exists_contest(courseid, contestid):
            ret = self.template_helper.get_renderer().contest_unavailable()
        elif not self.contest_manager.exists_contest(courseid, contestid):
            ret = self.template_helper.get_renderer().contest_unavailable()
        elif not self.contest_manager.contest_is_enabled(courseid, contestid):
            ret = self.template_helper.get_renderer().contest_unavailable()
        else:
            self.contest_manager.add_headers()
            course, start, end, blackout, tasks, results, activity, contestid, contest_name = self.contest_manager.get_data(courseid, contestid, False)
            ret = self.template_helper.get_renderer(). \
                scoreboard(course, start, end, blackout, tasks, results, activity, contestid, contest_name, True)
        return ret