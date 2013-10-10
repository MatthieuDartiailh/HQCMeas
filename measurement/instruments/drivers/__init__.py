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

from .driver_tools import (VisaInstrument, InstrIOError)
from .yokogawa import YokogawaGS200, Yokogawa7651
from .agilent_multimeters import Agilent34410A
from .keithley_multimeters import Keithley2000
from .lock_in_sr72_series import LockInSR7270, LockInSR7265
from .lock_in_sr830 import LockInSR830
from .agilent_psg_signal_generators import AgilentPSGSignalGenerator
from .agilent_pna import AgilentPNA
from .oxford_ips import IPS12010
from .anritsu_signal_source import AnritsuMG3694

DRIVERS = {'YokogawaGS200' : YokogawaGS200,
           'Yokogawa7651' : Yokogawa7651,
           'SR7265-LI' : LockInSR7265,
           'SR7270-LI' : LockInSR7270,
           'SR830' : LockInSR830,
           'Agilent34410A' : Agilent34410A,
           'Keithley2000' : Keithley2000,
           'AgilentE8257D' : AgilentPSGSignalGenerator,
           'AgilentPNA' : AgilentPNA,
           'IPS12010' : IPS12010,
           'AnritsuMG3694' : AnritsuMG3694}

DRIVER_TYPES = {'Visa' : VisaInstrument}