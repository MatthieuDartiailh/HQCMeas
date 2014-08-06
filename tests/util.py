# -*- coding: utf-8 -*-
#==============================================================================
# module : util.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
import os, stat
from enaml.qt.qt_application import QtApplication
from enaml.widgets.api import Window
from time import sleep
from nose.tools import nottest


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

# All the following functions are used to avoid permissions issues on windows.
@nottest
def create_test_dir(dir_path):
    if os.path.isdir(dir_path):
        clean_directory(dir_path)
    else:
        try:
            os.mkdir(dir_path)
        except OSError:
            pass


def clean_directory(dir_path):
    for root, dirs, files in os.walk(dir_path, topdown=False):
        for name in files:
            try:
                filename = os.path.join(root, name)
                os.chmod(filename, stat.S_IWUSR)
                os.remove(filename)
            except OSError:
                pass
        for name in dirs:
            try:
                os.rmdir(os.path.join(root, name))
            except OSError:
                pass


def remove_tree(dir_path):
    clean_directory(dir_path)
    try:
        os.rmdir(dir_path)
    except OSError:
        pass
