# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Overview page """
from collections import OrderedDict
import copy
from datetime import datetime, timedelta

import pymongo
import web

from inginious.frontend.webapp_contest.pages.utils import INGIniousAuthPage


class OverviewPage(INGIniousAuthPage):
    """ Displays the overview of the contest """

    def GET_AUTH(self, courseid, contestid):  # pylint: disable=arguments-differ
        course, start, end, blackout, tasks, results, activity, contestid, contest_name = self.contest_manager.get_data(courseid, contestid, True, allowed_users=[self.user_manager.session_username()])
        return self.template_helper.get_renderer().\
            overview(course, start, end, blackout, tasks, results, activity, contestid, contest_name)



