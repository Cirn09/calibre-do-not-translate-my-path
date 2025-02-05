#!/usr/bin/env python
# -*- coding: utf-8 -*-
__license__ = "GPL v3"
__copyright__ = "2023-2025, Cirn09(古明地小板)"

from calibre.customize import InterfaceActionBase
from calibre.utils.filenames import sanitize_file_name

from calibre_plugins.notrans.config import prefs


class NoTransBase(InterfaceActionBase):

    name = "NoTrans"
    description = _("Do not translate my paths")
    supported_platforms = ["windows", "osx", "linux"]
    author = "Cirn09"
    version = (3, 1, 0)
    minimum_calibre_version = (5, 0, 0)  # first version using Python 3

    actual_plugin = "calibre_plugins.notrans.ui:NoTrans"

    def is_customizable(self):
        return True

    def config_widget(self):
        from calibre_plugins.notrans.ui import ConfigWidget

        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()

        hook.update(prefs)


class Hook(object):

    def __init__(self):
        # db
        try:
            from calibre.db import backend

            self.db = backend
            self.db_ori = backend.ascii_filename
        except ImportError:
            self.db = None

        # usb
        try:
            from calibre.devices.usbms import device

            self.usb = device
            self.usb_ori = device.sanitize
        except ImportError:
            self.usb = None

        # app
        try:
            from calibre.devices.smart_device_app import driver

            self.app = driver
            self.smart_ori = driver.sanitize
        except ImportError:
            self.app = None

        # mtp
        try:
            from calibre.devices.mtp import driver

            self.mtp = driver
            self.mtp_ori = driver.MTP_DEVICE.create_upload_path
        except ImportError:
            self.mtp = None

        # save_to_disk (实际上影响所有“发送到”)

        # import calibre.library.save_to_disk
        # old = calibre.library.save_to_disk.get_components
        # def new(*args, **keywords):
        #     keywords['sanitize_func'] = sanitize_file_name
        #     return old(*args, **keywords)
        # calibre.library.save_to_disk.get_components = new

        try:
            from calibre.library import save_to_disk

            self.s2d = save_to_disk
            self.s2d_ori = save_to_disk.get_components
        except ImportError:
            self.s2d = None

    def update(self, config: dict):
        if self.db:
            if config.get("db", True):
                self.db.ascii_filename = sanitize_file_name
                print("NoTrans: db hooked")
            else:
                self.db.ascii_filename = self.db_ori
                print("NoTrans: db unhooked")

        send = config.get("send", True)

        if self.usb:
            if send:
                self.usb.sanitize = sanitize_file_name
                print("NoTrans: usb hooked")
            else:
                self.usb.sanitize = self.usb_ori
                print("NoTrans: usb unhooked")

        if self.app:
            if send:
                self.app.sanitize = sanitize_file_name
                print("NoTrans: app hooked")
            else:
                self.app.sanitize = self.smart_ori
                print("NoTrans: app unhooked")

        if self.mtp:
            if send:
                self.mtp.MTP_DEVICE.create_upload_path = mtp_create_upload_path
                print("NoTrans: mtp hooked")
            else:
                self.mtp.MTP_DEVICE.create_upload_path = self.mtp_ori
                print("NoTrans: mtp unhooked")

        if self.s2d:
            if send:
                self.s2d.get_components = gen_s2d_hook(self.s2d_ori)
                print("NoTrans: save_to_disk hooked")
            else:
                self.s2d.get_components = self.s2d_ori
                print("NoTrans: save_to_disk unhooked")


def mtp_create_upload_path(self, path, mdata, fname, routing):
    from calibre.devices.utils import create_upload_path
    import posixpath

    ext = fname.rpartition(".")[-1].lower()
    path = routing.get(ext, path)

    filepath = create_upload_path(
        mdata,
        fname,
        self.save_template,
        sanitize_file_name,
        prefix_path=path,
        path_type=posixpath,
        maxlen=self.MAX_PATH_LEN,
        use_subdirs="/" in self.save_template,
        news_in_folder=self.NEWS_IN_FOLDER,
    )
    return tuple(x for x in filepath.split("/"))


def gen_s2d_hook(ori_func):
    def s2d_hook(*args, **keywords):
        # def get_components(template, mi, id, timefmt='%b %Y', length=250,
        #     sanitize_func=ascii_filename, replace_whitespace=False,
        #     to_lowercase=False, safe_format=True, last_has_extension=True,
        #     single_dir=False):
        if len(args) >= 6:
            args = args[:5] + (sanitize_file_name,) + args[6:]
        else:
            keywords["sanitize_func"] = sanitize_file_name
        return ori_func(*args, **keywords)

    return s2d_hook


hook = Hook()
hook.update(prefs)
