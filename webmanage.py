from utilities import parse_app_location_string, get_url_hostname, fixed_render_template, fixed_send_file
from debug_utils import print_object

from traceback import print_exc, format_exc
from os import getcwd, chdir
from os.path import join, relpath

from flask import Flask as _Flask, request as _request, abort as _abort, redirect as _redirect, Response as _Response_class, make_response as _make_response
from werkzeug.test import Client
from werkzeug.exceptions import HTTPException
from werkzeug.routing import NotFound, MethodNotAllowed, RequestRedirect
from werkzeug.debug import DebuggedApplication

wm_config_default = "default xd"
wm_config_test = {
    "debug_log_enable": True,
    "debug_log_func": print,
    "debug_log_format_string": "### {} ###",
    "apps": {
        "testapp": {
            "hostnames": ["192.168.1.95"],
            "location": "testapp.app:app"
        },
        "musicserver": {
            "hostnames": ["173.90.241.120"],
            "location": "musicserver.app:app"
        }
    },
    "not_found_response": "[WebManage] This is the default page shown when an app has not been configured. Please contact the webmaster.",
    "autostartup": True
}

# Fix for absolute imports: see https://stackoverflow.com/a/19190695/5037905
from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

# Flask app that acts as a proxy, handling redirections.
class RedirectApp (_Flask):
    def __init__ (self, *args, **kwargs):
        if "wm_config" not in kwargs.keys ():
            self.wm_config = wm_config_test
        else:
            self.wm_config = kwargs["wm_config"]
            del kwargs["wm_config"]
        super (RedirectApp, self).__init__ (*args, **kwargs)
        print ("{}".format (self.wm_config))

        self.wm_enableds = {}

        # Assign the wm_on_startup function to be called before this app's first request.
        self.before_first_request_funcs.append (self.wm_on_startup)

        # any path
        self.route ("/<path:path>") (self.wm_INTERNAL_redir)
        # fix for no path
        self.route ("/", defaults = {"path": ""}) (self.wm_INTERNAL_redir)
    def wm_debug_log (self, message):
        if "debug_log_enable" in self.wm_config.keys () and self.wm_config["debug_log_enable"] != None and self.wm_config["debug_log_enable"]:
            # if debug logging has been enabled, it's not None, and it's True:
            if "debug_log_func" in self.wm_config.keys () and callable (self.wm_config["debug_log_func"]):
                # if a custom log function has been passed, and it's not None, call it with the message
                self.wm_config["debug_log_func"] (self.wm_config["debug_log_format_string"].format (message))
            else:
                # otherwise, just call print with the message
                print (self.wm_config ["debug_log_format_string"].format (message))
    def wm_force_sync_start (self):
        self.before_first_request_funcs.remove (self.wm_on_startup)
        self.wm_on_startup ()
    def wm_on_startup (self):
        self.wm_debug_log ("starting up")
        self.wm_debug_log ("automatically starting up apps: {}".format (self.wm_config["autostartup"]))
        if self.wm_config["autostartup"]:
            for appid in self.wm_config["apps"].keys ():
                try:
                    self.wm_debug_log ("starting app {}".format (appid))
                    self.wm_start (appid)
                    self.wm_debug_log ("app {} started".format (appid))
                except Exception as exc:
                    self.wm_debug_log ("app {} failed to start".format (appid))
                    self.wm_debug_log ("start error log")
                    self.wm_debug_log (format_exc (exc))
                    self.wm_debug_log ("end error log")
    def wm_start (self, appid):
        self.wm_debug_log ("inner start for app {} started".format (appid))
        assert self.wm_app_exists (appid), "App ID does not exist"
        target = self.wm_config["apps"][appid]
        self.wm_debug_log ("parsing app location string")
        module, app = parse_app_location_string (target["location"])
        self.wm_debug_log ("parsed app location string, adding to enabled dictionary")
        self.wm_enableds[appid] = {
            "module": module,
            "app": app,
            "first_request": True
        }
        self.wm_enableds[appid]["module"].render_template = lambda filename: fixed_render_template (self, appid, filename)
        self.wm_enableds[appid]["module"].send_file = lambda filename, **kwargs: fixed_send_file (self, appid, filename, **kwargs)
        self.wm_debug_log ("added to enabled dictionary, finished")
        self.wm_debug_log ("inner start for app {} finished".format (appid))
    def wm_stop (self, appid, ignore_if_not_running = False):
        self.wm_debug_log ("inner stop for app {} started".format (appid))
        assert self.wm_app_exists (appid), "App ID does not exist"
        try:
            assert self.wm_app_is_running (appid), "App is not running"
            del self.wm_enableds[appid]
        except:
            if ignore_if_not_running:
                # Ignores AssertionError and KeyError
                pass
            else:
                raise
        self.wm_debug_log ("inner stop for app {} finished".format (appid))
    def wm_restart (self, appid, ignore_if_not_running = False):
        self.wm_debug_log ("inner restart for app {} started".format (appid))
        self.wm_stop (appid, ignore_if_not_running = ignore_if_not_running)
        self.wm_start (appid)
        self.wm_debug_log ("inner restart for app {} finished".format (appid))
    def wm_app_exists (self, appid):
        return appid in self.wm_config["apps"].keys ()
    def wm_app_is_running (self, appid):
        return appid in self.wm_enableds.keys ()
    def wm_INTERNAL_redir (self, path):
        self.wm_debug_log ("--- redirect received ---")

        self.wm_debug_log ("checking hostname")
        hostname = get_url_hostname (_request.base_url)
        self.wm_debug_log ("target hostname is {}".format (hostname))

        found_app = False
        for appid in self.wm_enableds.keys ():
            if hostname in self.wm_config["apps"][appid]["hostnames"]:
                found_app = True
                app = self.wm_enableds[appid]
                self.wm_debug_log ("hostname {0} matches app {1}".format (hostname, app))
                break

        if not found_app:
            self.wm_debug_log ("hostname {} doesn't match any app!".format (hostname))
            ret = self.wm_config["not_found_response"]
            return ret

        base_path = self.wm_config["apps"][appid]["base_path"]
        old_abspath = getcwd ()
        self.wm_debug_log ("changing cwd to {}".format (base_path))
        chdir (base_path)
        self.wm_debug_log ("cwd is now {}".format (getcwd ()))
        old_path = relpath (old_abspath)

        if app["first_request"]:
            app["first_request"] = False
            for before_first_request_func in app["app"].before_first_request_funcs:
                before_first_request_func ()

        # TODO add blueprint support
        for blueprint, before_request_func_list in app["app"].before_request_funcs.items ():
            for before_request_func in before_request_func_list:
                before_request_func ()

        self.wm_debug_log ("done calling before functions")

        # print (print_object (app.url_map))

        # set the module's request object to the actual request object
        # so the route function can access the actual request information
        app["module"].request = _request
        self.wm_debug_log ("bound to actual request")

        # bind the app's url map to the actual request
        urls = app["app"].url_map.bind_to_environ (_request)
        self.wm_debug_log ("bound to real environment")

        # get the endpoint and arguments for the actual request
        self.wm_debug_log ("matching")
        error = False
        try:
            endpoint, args = urls.match ()
        except NotFound:
            print_exc ()
            error = True
            ret = "Not Found", 404
            endpoint, args = None, None
        except MethodNotAllowed:
            print_exc ()
            error = True
            ret = "Method Not Allowed", 405
            endpoint, args = None, None
        except RequestRedirect as redir:
            print_exc ()
            error = True
            ret = _redirect (redir.new_url)
            endpoint, args = None, None
        except:
            print_exc ()
            error = True
            endpoint, args = None, None
        if error:
            self.wm_debug_log ("error return value is {}".format (ret))
        self.wm_debug_log ("matched")
        print ("### ENDPOINT: {0}, ARGS: {1}".format (endpoint, args))

        if not error:
            for function_name, view_function in app["app"].view_functions.items ():
                if function_name == endpoint:
                    self.wm_debug_log ("calling {}".format (function_name))
                    try:
                        ret = _make_response (view_function (**args))
                    except HTTPException as exc:
                        print_exc ()
                        self.wm_debug_log (
                            "error when calling view function -- code: {0}, desc: {1}, name: {2}, response: {3} ###".format (
                            exc.code, exc.description, exc.name, exc.response)
                        )
                        ret = exc.get_response (environ = _request)
                    # WARNING: any other non-abort () exceptions will be raised
                    # and will call the Flask debugger without calling the below code!
                else:
                    self.wm_debug_log ("not calling view function {}".format (function_name))
        
        # TODO also add blueprint support
        for blueprint, after_request_func_list in app["app"].after_request_funcs.items ():
            for after_request_func in after_request_func_list:
                self.wm_debug_log ("Response before calling {0}: {1}".format (after_request_func.__name__, ret))
                after_request_ret = after_request_func (_make_response (ret))
                self.wm_debug_log ("Response after calling {0}: {1}".format (after_request_func.__name__, after_request_ret))
                ret = after_request_ret

        self.wm_debug_log ("changing dir back to {}".format (old_path))
        chdir (old_path)

        self.wm_debug_log ("--- redirect completed, returning ---")
        return ret

# Flask app designed to allow you to control a RedirectApp instance from the web.
class ManageApp (_Flask):
    def __init__ (self, *args, **kwargs):
        raise NotImplementedError ("will work on this once i finish redirectapp")
