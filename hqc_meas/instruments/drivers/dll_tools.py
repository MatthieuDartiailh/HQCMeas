#==============================================================================
# module : driver_tools.py
# author : Pierre Heidmann
# license : MIT license
#==============================================================================
"""
Created on Tue Jun 24 17:45:04 2014

@author: Pierre
"""
import ctypes
from .driver_tools import BaseInstrument
from threading import Lock


class DllInstrument(BaseInstrument):
    """

    """
    library = ''


class DllLibrary(object):
    """

    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is not None:
            return cls._instance
        else:
            return super(DllLibrary, cls).__new__(cls, *args, **kwargs)

    def __init__(self, path, **kwargs):

        if kwargs.get('type') == 'windll':
            self.dll = ctypes.windll.LoadLibrary(path)
        elif kwargs.get('type') == 'oledll':
            self.dll = ctypes.windll.LoadLibrary(path)
        else:
            self.dll = ctypes.cdll.LoadLibrary(path)
        self.lock = Lock()

DRIVER_PACKAGES = ['dll']
DRIVER_TYPES = {'Dll': DllInstrument}
