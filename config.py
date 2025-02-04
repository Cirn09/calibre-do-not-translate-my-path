#!/usr/bin/env python
# -*- coding: utf-8 -*-
__license__ = "GPL v3"
__copyright__ = "2023-2025, Cirn09(古明地小板)"

from calibre.utils.config import JSONConfig
prefs = JSONConfig("plugins/notrans")

prefs.defaults["db"] = True
prefs.defaults["usb"] = True
prefs.defaults["mtp"] = True
prefs.defaults["app"] = True

prefs.defaults["hello_world_msg"] = "Hello, World!"
