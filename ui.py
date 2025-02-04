#!/usr/bin/env python
# -*- coding: utf-8 -*-
__license__ = "GPL v3"
__copyright__ = "2023-2025, Cirn09(古明地小板)"


# pulls in translation files for _() strings
try:
    load_translations()
except NameError:
    pass  # load_translations() added in calibre 1.9

from functools import partial

from calibre.gui2.actions import InterfaceAction, menu_action_unique_name
from calibre.gui2 import question_dialog
from calibre.gui2.threaded_jobs import ThreadedJob
from qt.core import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QWidget,
    QCheckBox,
    QVBoxLayout,
    QMenu,
    QUrl,
)
from calibre_plugins.notrans.config import prefs


class ConfigWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.l = QVBoxLayout()
        self.setLayout(self.l)

        label = QLabel(_("Check to disable translation."))
        label.setWordWrap(True)
        self.l.addWidget(label)
        self.l.addSpacing(5)

        self.db = QCheckBox(_("Library"), self)
        self.db.setToolTip(_('Do not translate paths when "adding books"'))
        self.db.setChecked(prefs["db"])
        self.l.addWidget(self.db)

        self.usb = QCheckBox(_("USB Device (include local floder)"), self)
        self.usb.setToolTip(
            _(
                "Contains all system native directories (U disk, SD card, mounted directories, etc.)"
            )
        )
        self.usb.setChecked(prefs["usb"])
        self.l.addWidget(self.usb)

        self.mtp = QCheckBox(_("MTP Device"), self)
        self.mtp.setToolTip(_("Media Transfer Protocol devices, like Android devices"))
        self.mtp.setChecked(prefs["mtp"])
        self.l.addWidget(self.mtp)

        self.app = QCheckBox(_("Smart Device App"), self)
        self.app.setToolTip(_("Smart Device App... Is this thing really useful?"))
        self.app.setChecked(prefs["app"])
        self.l.addWidget(self.app)

    def save_settings(self):
        prefs["db"] = self.db.isChecked()
        prefs["usb"] = self.usb.isChecked()
        prefs["mtp"] = self.mtp.isChecked()
        prefs["app"] = self.app.isChecked()


class NoTrans(InterfaceAction):

    name = "No Trans"

    action_spec = (
        _("No Trans"),
        "images/icon.png",
        _("Configure No Trans"),
        None,
    )

    def genesis(self):
        icon = get_icons("images/icon.png", "NoTrans")  # type: ignore
        self.qaction.setIcon(icon)
        do_user_config: callable = self.interface_action_base_plugin.do_user_config  # type: ignore
        self.do_config = partial(do_user_config, parent=self.gui)
        self.qaction.triggered.connect(self.do_config)

        # Setup menu
        self.menu = QMenu()
        self.qaction.setMenu(self.menu)

        self.add_menu(
            _("Configure"),
            "config.png",
            _("Configure No Trans"),
            self.do_config,
        )
        self.add_menu(
            _("Refresh Library"),
            "view-refresh.png",
            _("Refresh the paths for all books in this library"),
            self.refresh,
        )

    def add_menu(self, text, icon, tooltip, action):
        uni_name = menu_action_unique_name(self, text)
        action = self.create_menu_action(
            menu=self.menu,
            unique_name=uni_name,
            text=text,
            icon=icon,
            description=tooltip,
            triggered=action,
        )
        self.menu.addAction(action)
        return action

    def refresh(self):
        if not question_dialog(
            parent=self.gui,
            title=_("Refresh Library"),
            msg=_(
                "Refresh the paths for all books in this library?\nThis operation may take a while to complete."
            ),
            yes_text=_("Continue"),
            no_text=_("Cancel"),
        ):
            return
        job = ThreadedJob(
            type_="refresh_library",
            description=_("NoTrans: Refreshing Library"),
            func=self.do_refresh,
            args=(self.gui.current_db,),
            kwargs={},
            callback=lambda x: None,
            killable=False,
        )
        self.gui.job_manager.run_threaded_job(job)

    def do_refresh(self, db, notifications, log, abort):
        ids = db.new_api.all_book_ids()
        for i, book_id in enumerate(ids):
            i = i + 1
            meta = db.new_api.get_metadata(book_id)
            notifications.put((i / len(ids), meta.title))
            log.info(f'{i}/{len(ids)} "{meta.title}"')
            db.new_api.set_metadata(book_id, meta)
