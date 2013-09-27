# -*- coding: utf-8 -*-

from .driver_tools import (VisaInstrument, InstrIOError)
from .yokogawa import YokogawaGS200, Yokogawa7651
from .agilent_multimeter import Agilent34410A
from keithley_multimeter import Keithley2000
from .lock_in_sr72_series import LockInSR7270, LockInSR7265
from .lock_in_sr830 import LockInSR830
from .agilent_psg_signal_generator import AgilentPSGSignalGenerator

DRIVERS = {'YokogawaGS200' : YokogawaGS200,
           'Yokogawa7651' : Yokogawa7651,
           'SR7265-LI' : LockInSR7265,
           'SR7270-LI' : LockInSR7270,
           'SR830' : LockInSR830,
           'Agilent34410A' : Agilent34410A,
           'Keithley2000' : Keithley2000,
           'AgilentE8257D' : AgilentPSGSignalGenerator}

DRIVER_TYPES = {'Visa' : VisaInstrument}