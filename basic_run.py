# basic_run.py: A basic run script for the redirect app.

# A dictionary containing configuration information for the RedirectApp.
# May contain a function for "debug_log_func",
# but otherwise should be fine to serialize.

# (I will probably implement serialization when making the frontend to the app.)
wm_config = {
    # Enables or disables logging of debug information, such as internal errors
    # and some request information. This is quite verbose and calls the debug
    # log function upwards of 15-20 times per request (may vary).
    "debug_log_enable": True,
    # A function that's called with the message to log.
    "debug_log_func": print,
    # A format string that the message to log is applied to.
    "debug_log_format_string": "### {} ###",
    # A dictionary of apps, mapping app IDs to the app information.
    "apps": {
        # App IDs are used internally and when using the debug log function.
        # There should be one per app, but otherwise there are no restrictions.
        # (Non-ASCII characters used here may break print based on your shell)
        "testapp": {
            # A list of hostnames this app should be accessible from,
            # e.g., when a request is received containing these hostnames,
            # handle the request using this app.
            "hostnames": ["192.168.1.95"],
            # An app location string following the gunicorn format.
            "location": "testapp.app:app",
            # A relative path to the template directory,
            # used to fix render_template calls in the app code.
            "template_base_path": "testapp/templates",
            # A relative path to the app's topmost directory,
            # used to fix send_file calls in the app code.
            "base_path": "testapp/"
        }
    },
    # This is sent if the server is accessed from a hostname not listed
    # in the above apps.
    "not_found_response": "[WebManage] This is the default page shown when an app has not been configured.\n\
    Put some text here!",
    # Sets whether or not to initialize/import the applications
    # on the call to (RedirectApp class instance).run ()
    # (actually runs before the first request)
    "autostartup": True
}

# Here we're just importing the app class from webmanage.py.
from webmanage import RedirectApp

# Here's where the Flask app is internally created, meaning you should pass
# all your Flask app initialization variables here.

# The configuration for the app should be passed as the wm_config keyword argument.

# "static_folder = None" is necessary for Flask to pass /static/<filename>
# requests through to an app instead of handling them directly.
# (I might implement this internally at some point.)

wm = RedirectApp (__name__, static_folder = None, wm_config = wm_config)

# Here we check if we're in the main class.
# Since I run this through Gunicorn personally for better logging
# and multithreading, this is necessary for me.
if __name__ == "__main__":
    # This calls the underlying Flask app run function.
    wm.run (
        # To disable SSL, set your port to 80 and remove the ssl_context argument.
        # I bind to all IPs on port 443 since I'm using SSL.
        host = "0.0.0.0", port = 443,
        # Here I'm passing Flask the certificate and key for SSL use.
        ssl_context = ("cert.pem", "key.pem"),
        # Here I'm enabling Flask's debugger (runs for all apps).
        debug = True,
        # Disables Flask's debug reloader because it reruns the app initialization in some cases.
        use_reloader = False
    )
