# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Index page """
from collections import OrderedDict

import web

from inginious.frontend.webapp_contest.pages.utils import INGIniousAuthPage


class ContestsPage(INGIniousAuthPage):
    """ Index page """

    def GET_AUTH(self):  # pylint: disable=arguments-differ
        """ Display main course list page """
        if self.user_manager.user_is_superadmin():
            web.seeother("/index_admin")
        return self.show_page(None)

    def POST_AUTH(self):  # pylint: disable=arguments-differ
        """ Parse course registration or course creation and display the course list page """

        return web.notfound()


