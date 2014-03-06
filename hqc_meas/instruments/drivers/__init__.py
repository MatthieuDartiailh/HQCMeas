# -*- coding: utf-8 -*-
#==============================================================================
# module : __init__.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
This module gives an easy access to the driver package

It exports all the drivers defined in the driver package, the general exception
used in instrument drivers `InstrIOError` and also defines two
modules constants :
- `DRIVERS` : A dictionnary mapping driver names to the class implementing them.
- `DRIVER_TYPE` : A dictionnary mapping the driver type names to the base
            classes implementing them.

"""
#import os.path, importlib
#from .driver_tools import (BaseInstrument,
#                           InstrError, InstrIOError)
#
#if 'DRIVER_TYPES' not in globals():
#    DRIVER_TYPES = {}
#    DRIVER_PACKAGES = []
#    dir_path = os.path.dirname(__file__)
#    modules = ['.' + os.path.split(path)[1][:-3]
#               for path in os.listdir(dir_path)
#               if path.endswith('.py')]
#
#    modules.remove('.__init__')
#    modules.remove('.driver_tools')
#    for module in modules:
#        try:
#            mod = importlib.import_module(module, __name__)
#        except ImportError:
#            continue
#        if hasattr(mod, 'DRIVER_TYPES'):
#            DRIVER_TYPES.update(mod.DRIVER_TYPES)
#        if hasattr(mod, 'DRIVER_PACKAGE'):
#            DRIVER_PACKAGES.append(mod.DRIVER_PACKAGE)
#
#if 'DRIVERS' not in globals():
#
#    DRIVERS = {}
#    dir_path = os.path.dirname(__file__)
#    modules = []
#
#    for pack in DRIVER_PACKAGES:
#        add_dir = os.path.join(dir_path, pack)
#        modules += ['.' + pack + '.' + os.path.split(path)[1][:-3]
#                    for path in os.listdir(add_dir)
#                    if path.endswith('.py')
#                    and not path.endswith('__init__.py')]
#
#    modules.append('.dummy')
#    for module in modules:
#        mod = importlib.import_module(module, __name__)
#        if hasattr(mod, 'DRIVERS'):
#            DRIVERS.update(mod.DRIVERS)
