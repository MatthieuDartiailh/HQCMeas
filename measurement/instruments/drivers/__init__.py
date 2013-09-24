# -*- coding: utf-8 -*-

from .driver_tools import (VisaInstrument, InstrIOError)
from .yokogawa import YokogawaGS200, Yokogawa7651
from .agilent_multimeter import Agilent34410A
from .lock_in_sr72_series import LockInSR72Series
from .lock_in_sr830 import LockInSR830
from .agilent_psg_signal_generator import AgilentPSGSignalGenerator

DRIVERS = {'YokogawaGS200' : YokogawaGS200,
           'Yokogawa7651' : Yokogawa7651,
           'SR7265-LI' : LockInSR72Series,
           'SR7270-LI' : LockInSR72Series,
           'SR830' : LockInSR830,
           'Agilent34410A' : Agilent34410A,
           'AgilentE8257D' : AgilentPSGSignalGenerator}

DRIVER_TYPES = {'Visa' : VisaInstrument}