# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Database auth """

import hashlib
import random
import re
from collections import OrderedDict
import csv
import json
import urllib.request

import web

from inginious.frontend.webapp_contest.user_manager import AuthMethod
from inginious.frontend.webapp_contest.pages.utils import INGIniousPage, INGIniousAuthPage
from inginious.frontend.webapp_contest.pages.course_admin.utils import INGIniousAdminPage

from pymongo.collection import ReturnDocument

allow_deletion = True


class EciDatabaseAuthMethod(AuthMethod):
    """
    MongoDB Database auth method
    """

    def __init__(self, name, database):
        self._name = name
        self._database = database

    def get_name(self):
        return self._name

    def auth(self, login_data):
        username = login_data["login"].strip()
        password_hash = hashlib.sha512(login_data["password"].encode("utf-8")).hexdigest()

        user = self._database.users.find_one({"username": username, "password": password_hash, "activate": {"$exists": False}})

        if user is not None:
            return username, user["realname"], user["email"]
        else:
            return None

    def needed_fields(self):
        return {
            "input": OrderedDict((
                ("login", {"type": "text", "placeholder": "Login"}),
                ("password", {"type": "password", "placeholder": "Password"}))),
            "info": '<div class="text-center"><a href="' + web.ctx.home +
                    '/register#lostpasswd">Lost password?</a></div>'
        }

    def should_cache(self):
        return False

    def get_users_info(self, usernames):
        """
        :param usernames: a list of usernames
        :return: a dict containing key/pairs {username: (realname, email)} if the user is available with this auth method,
            {username: None} else
        """
        retval = {username: None for username in usernames}
        data = self._database.users.find({"username": {"$in": usernames}})

        find_data = False
        for user in data:
            retval[user["username"]] = (user["realname"], user["email"], user["flag"])
            find_data = True
        # web.debug(find_data)
        return retval if find_data else None


class RegistrationPage(INGIniousPage):
    """ Registration page for DB authentication """

    def GET(self):
        """ Handles GET request """
        if self.user_manager.session_logged_in():
            raise web.notfound()

        error = False
        reset = None
        msg = ""
        data = web.input()

        if "activate" in data:
            msg, error = self.activate_user(data)
        elif "reset" in data:
            msg, error, reset = self.get_reset_data(data)

        return self.template_helper.get_custom_renderer('frontend/webapp_contest/plugins/auth/eci_auth').register(reset, msg, error)

    def get_reset_data(self, data):
        """ Returns the user info to reset """
        error = False
        reset = None
        msg = ""
        user = self.database.users.find_one({"reset": data["reset"]})
        if user is None:
            error = True
            msg = "Invalid reset hash."
        else:
            reset = {"hash": data["reset"], "username": user["username"], "realname": user["realname"]}

        return msg, error, reset

    def activate_user(self, data):
        """ Activates user """
        error = False
        user = self.database.users.find_one_and_update({"activate": data["activate"]}, {"$unset": {"activate": True}})
        if user is None:
            error = True
            msg = "Invalid activation hash."
        else:
            msg = "You are now activated. You can proceed to login."

        return msg, error

    def lost_passwd(self, data):
        """ Send a reset link to user to recover its password """
        error = False
        msg = ""

        # Check input format
        email_re = re.compile(
            r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
            r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'  # quoted-string
            r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', re.IGNORECASE)  # domain
        if email_re.match(data["recovery_email"]) is None:
            error = True
            msg = "Invalid email format."

        if not error:
            reset_hash = hashlib.sha512(str(random.getrandbits(256)).encode("utf-8")).hexdigest()
            user = self.database.users.find_one_and_update({"email": data["recovery_email"]}, {"$set": {"reset": reset_hash}})
            if user is None:
                error = True
                msg = "This email address was not found in database."
            else:
                try:
                    web.sendmail(web.config.smtp_sendername, data["recovery_email"], "INGInious password recovery",
                                 "Dear " + user["realname"] + """,

Someone (probably you) asked to reset your INGInious password. If this was you, please click on the following link :
""" + web.ctx.home + "/register?reset=" + reset_hash)
                    msg = "An email has been sent to you to reset your password."
                except:
                    error = True
                    msg = "Something went wrong while sending you reset email. Please contact the administrator."

        return msg, error

    def reset_passwd(self, data):
        """ Reset the user password """
        error = False
        msg = ""

        # Check input format
        if len(data["passwd"]) < 6:
            error = True
            msg = "Password too short."
        elif data["passwd"] != data["passwd2"]:
            error = True
            msg = "Passwords don't match !"

        if not error:
            passwd_hash = hashlib.sha512(data["passwd"].encode("utf-8")).hexdigest()
            user = self.database.users.find_one_and_update({"reset": data["reset_hash"]},
                                                           {"$set": {"password": passwd_hash}, "$unset": {"reset": True}})
            if user is None:
                error = True
                msg = "Invalid reset hash."
            else:
                msg = "Your password has been successfully changed."

        return msg, error

    def POST(self):
        """ Handles POST request """
        if self.user_manager.session_logged_in():
            raise web.notfound()

        reset = None
        msg = ""
        error = False
        data = web.input()
        if "lostpasswd" in data:
            msg, error = self.lost_passwd(data)
        elif "resetpasswd" in data:
            msg, error = self.reset_passwd(data)

        return self.template_helper.get_custom_renderer('frontend/webapp_contest/plugins/auth/eci_auth').register(reset, msg, error)


class AdminRegisterPage(INGIniousAdminPage):
    def GET_AUTH(self):
        return web.notfound()

    def POST_AUTH(self):
        data = web.input(users_file={})
        courseid = data["course"]
        message = ""
        try:
            users_file = data.get("users_file").file
        except:
            return json.dumps({"status": "error", "message": json.dumps({"File": "Invalid file!"})})

        users_data = users_file.read()
        users_file.close()
        list = [x for x in str(users_data,'utf-8').split('\n') if x != '']
        list = [[y for y in list[x].split(",")] for x in range(1,len(list))]
        not_imported = dict()
        real_data = []
        send_email = "email" in data
        try:
            for row in list:
                user_data = dict()
                user_data["email"] = row[0]
                user_data["realname"] = row[1]
                user_data["passwd"] = row[2]
                user_data["passwd2"] = row[2]
                user_data["username"] = row[3]
                msg, error = self.register_user(user_data, False)
                if error:
                    if msg == "existing_user":
                        user_data["existing"]=True
                        real_data.append(user_data)
                    else:
                        not_imported[row[1]]=msg
                else:
                    real_data.append(user_data)
        except:
            return json.dumps({"status": "error", "message": json.dumps({"File": "Invalid file!"})})
        for user_data in real_data:
            username_duplicated = len([x for x in real_data if x["username"] == user_data["username"]]) != 1
            if username_duplicated:
                return json.dumps({"status": "error", "message": json.dumps({user_data["username"]: "Duplicated username in file!"})})
            email_duplicated = len([x for x in real_data if x["email"] == user_data["email"]]) != 1
            if email_duplicated:
                return json.dumps({"status": "error", "message": json.dumps({user_data["username"]: "Duplicated email in file!"})})
        if len(not_imported) == 0:
            message = {}
            for user_data in real_data:
                if not user_data.get("existing",False):
                    msg, error = self.register_user(user_data, True, send_email)
                    if error:
                        message[user_data["username"]] = "Mail not sent."
                elif send_email:
                    message[user_data["username"]] = "Mail not sent (reason: user already exists)"
                course = self.course_factory.get_course(courseid)
                reg = self.user_manager.course_register_user(course, user_data["username"].strip(), '', True)
                if not reg:
                    message[user_data["username"]] = "Error while registering the user to the course. (maybe this user is already registered to the course)."
            return json.dumps({"status": "ok", "message": json.dumps(message)})
        else:
            return json.dumps({"status": "error", "message": json.dumps(not_imported)})


    def register_user(self, data, register, send_email=False):
        """ Parses input and register user """
        error = False
        msg = ""

        email_re = re.compile(
            r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
            r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'  # quoted-string
            r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', re.IGNORECASE)  # domain

        # Check input format
        if re.match(r"\w{4,}$", data["username"]) is None:
            error = True
            msg = "Invalid username format."
        elif email_re.match(data["email"]) is None:
            error = True
            msg = "Invalid email format."
        elif len(data["passwd"]) < 6:
            error = True
            msg = "Password too short."
        elif data["passwd"] != data["passwd2"]:
            error = True
            msg = "Passwords don't match !"

        if not error:
            existing_user = self.database.users.find_one({"$and": [{"username": data["username"]}, {"email": data["email"]}]})
            if existing_user is not None:
                error = True
                msg = "existing_user"
            else:
                if register:
                    flags = []
                    with urllib.request.urlopen(
                                    web.ctx.homedomain + '/static/webapp/json/countries.json') as url:
                        flags_data = json.loads(url.read().decode())
                        for d in flags_data:
                            if self.database.users.find_one({"flag": d["Code"]}) is None:
                                flags.append(d["Code"])
                    if len(flags)==0:
                        flags.append("CO")
                    flag = random.choice(flags)

                    passwd_hash = hashlib.sha512(data["passwd"].encode("utf-8")).hexdigest()
                    self.database.users.insert({"username": data["username"],
                                                "realname": data["realname"],
                                                "email": data["email"],
                                                "password": passwd_hash,
                                                "flag": flag})
                    if send_email:
                        web.sendmail(web.config.smtp_sendername, data["email"], "Welcome on INGInious",
                                 """Welcome on INGInious !

Following you have the URL and your credentials to access the platform:

Username: """ + data["username"] + """

Password: """ + data["passwd"] + """

Platform URL: """ + web.ctx.home + "/")
                    try:
                        msg = "You are succesfully registered. An email has been sent to you for activation."
                    except:
                        error = True
                        msg = "Something went wrong while sending you activation email. Please contact the administrator."

        return msg, error



class ProfilePage(INGIniousAuthPage):
    """ Profile page for DB-authenticated users"""

    def save_profile(self, userdata, data):
        """ Save user profile modifications """
        result = userdata
        error = False
        msg = ""

        # Check input format
        if len(data["oldpasswd"]) > 0 and len(data["passwd"]) < 6:
            error = True
            msg = "Password too short."
        elif len(data["oldpasswd"]) > 0 and data["passwd"] != data["passwd2"]:
            error = True
            msg = "Passwords don't match !"
        elif len(data["oldpasswd"]) > 0 :
            oldpasswd_hash = hashlib.sha512(data["oldpasswd"].encode("utf-8")).hexdigest()
            passwd_hash = hashlib.sha512(data["passwd"].encode("utf-8")).hexdigest()
            result = self.database.users.find_one_and_update({"username": self.user_manager.session_username(),
                                                              "password": oldpasswd_hash},
                                                             {"$set": {
                                                                 "password": passwd_hash}
                                                             },
                                                             return_document=ReturnDocument.AFTER)
            if not result:
                error = True
                msg = "Incorrect old pasword."
            else:
                msg = "Profile updated."
        '''
        else:
            result = self.database.users.find_one_and_update({"username": self.user_manager.session_username()},
                                                             {"$set": {"realname": data["realname"]}},
                                                             return_document=ReturnDocument.AFTER)
            if not result:
                error = True
                msg = "Incorrect username."
            else:
                self.user_manager.set_session_realname(data["realname"])
                msg = "Profile updated."
        '''

        return result, msg, error

    def delete_account(self, data):
        """ Delete account from DB """
        error = False
        msg = ""

        if not allow_deletion:
            return "Not allowed.", True

        username = self.user_manager.session_username()

        # Check input format
        result = self.database.users.find_one_and_delete({"username": username,
                                                          "email": data.get("delete_email", "")})
        if not result:
            error = True
            msg = "The specified email is incorrect."
        else:
            self.database.submissions.remove({"username": username})
            self.database.user_tasks.remove({"username": username})

            all_courses = self.course_factory.get_all_courses()

            for courseid, course in all_courses.items():
                if self.user_manager.course_is_open_to_user(course, username):
                    self.user_manager.course_unregister_user(course, username)

            self.user_manager.disconnect_user(web.ctx['ip'])
            raise web.seeother("/index")

        return msg, error

    def GET_AUTH(self):  # pylint: disable=arguments-differ
        """ GET request """
        userdata = self.database.users.find_one({"username": self.user_manager.session_username()})

        if not userdata:
            raise web.notfound()

        return self.template_helper.get_custom_renderer('frontend/webapp_contest/plugins/auth/eci_auth').profile("", False, allow_deletion)

    def POST_AUTH(self):  # pylint: disable=arguments-differ
        """ POST request """
        userdata = self.database.users.find_one({"username": self.user_manager.session_username()})

        if not userdata:
            raise web.notfound()

        msg = ""
        error = False
        data = web.input()
        if "save" in data:
            userdata, msg, error = self.save_profile(userdata, data)
        elif "delete" in data:
            msg, error = self.delete_account(data)

        return self.template_helper.get_custom_renderer('frontend/webapp_contest/plugins/auth/eci_auth').profile(msg, error, allow_deletion)


def main_menu(template_helper, database):
    """ Returns the additional main menu """
    def is_user_in_db(username):
        return True if database.users.find_one({"username": username}) else False
    return str(template_helper.get_custom_renderer('frontend/webapp_contest/plugins/auth/eci_auth', layout=False).main_menu(is_user_in_db))


def init(plugin_manager, _, _2, conf):
    """
        Allow authentication from database
    """
    global allow_deletion

    allow_deletion = conf.get("allow_deletion", False)
    plugin_manager.register_auth_method(EciDatabaseAuthMethod(conf.get('name', 'WebApp'), plugin_manager.get_database()))
    plugin_manager.add_hook("main_menu", lambda template_helper: main_menu(template_helper, plugin_manager.get_database()))
    plugin_manager.add_page('/register', RegistrationPage)
    plugin_manager.add_page('/import', AdminRegisterPage)
    plugin_manager.add_page('/profile', ProfilePage)
