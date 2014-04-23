# -*- coding: utf-8 -*-
from enaml.qt.qt_application import QtApplication
from enaml.widgets.api import Window
from time import sleep


def complete_line(string, char, length=79):
    str_len = len(string)
    if str_len < length-1:
        return string + ' ' + ''.join([char for i in range(length-1-str_len)])
    else:
        return string


def process_app_events():
    qapp = QtApplication.instance()._qapp
    qapp.flush()
    qapp.processEvents()


def close_all_windows():
    qapp = QtApplication.instance()._qapp
    qapp.flush()
    qapp.processEvents()
    sleep(0.1)
    for window in Window.windows:
        window.close()
    qapp.flush()
    qapp.processEvents()
