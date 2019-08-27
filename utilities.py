from importlib import import_module

def parse_app_location_string (app_location_string):
    module_and_variable = app_location_string.split (':')
    assert len (module_and_variable) == 2, "None or too many variables (required 1, specified {})".format (len (module_and_variable) - 1)
    module = import_module (module_and_variable[0], package = __file__)
    variable = getattr (module, module_and_variable[1])
    return module, variable

from urllib.parse import urlparse

def get_url_hostname (url):
    return urlparse (url).hostname

from os.path import join

from flask import render_template_string, Response, send_file

def fixed_render_template (wm, appid, filename):
    if "template_base_path" not in wm.wm_config["apps"][appid].keys ():
        return None
    file_base_path = wm.wm_config["apps"][appid]["template_base_path"]
    filepath = join (file_base_path, filename)
    with open (filepath, "r") as file:
        filetext = file.read ()
    return render_template_string (filetext)

def fixed_send_file (wm, appid, filename, **kwargs):
    file_base_path = wm.wm_config["apps"][appid]["base_path"]
    filepath = join (file_base_path, filename)
    return send_file (filepath, **kwargs)
