# -*- coding: utf-8 -*-

from .yokogawa import YokogawaGS200
from .agilent_multimeter import Agilent34410A
from .lock_in_sr72_series import LockInSR72Series
from .agilent_psg_signal_generator import AgilentPSGSignalGenerator

drivers = {'YokogawaGS200' : YokogawaGS200,
           'SR7265-LI' : LockInSR72Series,
           'SR7270-LI' : LockInSR72Series,
           'Agilent34410A' : Agilent34410A,
           'AgilentE8257D' : AgilentPSGSignalGenerator}