# -*- coding: utf-8 -*-
#==============================================================================
# module : oxford_ips.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
This module defines drivers for oxford ips magnet supply

:Contains:
    IPS12010

"""
from inspect import cleandoc
from time import sleep
from ..driver_tools import (InstrIOError, secure_communication,
                            instrument_property)
from ..visa_tools import VisaInstrument

_PARAMETER_DICT = {'Demand current': 0,
                   'Supply voltage': 1,
                   'Magnet current': 2,
                   'Target current': 5,
                   'Current sweep rate': 6,
                   'Demand field': 7,
                   'Target field': 8,
                   'Field sweep rate': 9,
                   'Software voltage limit': 15,
                   'Persistent magnet current': 16,
                   'Trip current': 17,
                   'Persistent magnet field': 18,
                   'Trip field': 19,
                   'Switch heater current': 20,
                   'Positive current limit': 21,
                   'Negative current limit': 22,
                   'Lead resistance': 23,
                   'Magnet inductance': 24}

_ACTIVITY_DICT = {'Hold': 0,
                  'To set point': 1,
                  'To zero': 2,
                  'Clamp': 4}

_CONTROL_DICT = {'Local & Locked': 0,
                 'Remote & Locked': 1,
                 'Local & Unlocked': 2,
                 'Remote & Unlocked': 3}

_GET_HEATER_DICT = {0: 'Off Magnet at Zero',
                    1: 'On (switch open)',
                    2: 'Off Magnet at Field',
                    5: 'Heater Fault',
                    8: 'No Switch Fitted'}


class IPS12010(VisaInstrument):
    """
    """

    caching_permissions = {'heater_state': True,
                           'target_current': True,
                           'sweep_rate_current': True,
                           'target_field': True,
                           'sweep_rate_field': True,
                           }

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}):
        super(IPS12010, self).__init__(connection_info, caching_allowed,
                                       caching_permissions)
        self.term_chars = '\r'

    def make_ready(self):
        """
        """
        self.control = 'Remote & Unlocked'
        self.set_communications_protocol(False, True)
        self.set_mode('TESLA')

    def go_to_field(self, value, rate, auto_stop_heater=True,
                    post_switch_wait=30):
        """
        """
        if self.target_field != value:
            waiting_time = abs(value - self.target_field)/rate*60
            self.field_sweep_rate = rate

            if self.heater_state == 'OFF':
                self.target_field = self.persistent_field
                self.activity = 'To set point'
                sleep(1)
                while self.check_output() == 'Changing':
                    sleep(1)
                self.heater_state = 'ON'
                sleep(1)

            self.target_field = value
            sleep(waiting_time)
            while self.check_output() == 'Changing':
                sleep(1)

        if auto_stop_heater:
            self.heater_state = 'OFF'
            sleep(post_switch_wait)
            self.activity = 'To zero'
            sleep(1)
            while self.check_output() == 'Changing':
                sleep(1)

    def check_output(self):
        """
        """
        status = self._get_status()
        output = int(status[11])
        if not output:
            return 'Constant'
        else:
            return 'Changing'

    def get_full_heater_state(self):
        """
        """
        status = self._get_status()
        heat = int(status[8])
        return _GET_HEATER_DICT[heat]

    @secure_communication()
    def set_mode(self, mode):
        """
        """
        if mode == 'AMPS':
            result = self.ask('M8')
            if result.startswith('?'):
                raise InstrIOError(cleandoc('''IPS120-10 did not set the
                    heater mode to {}'''.format(mode)))
        elif mode == 'TESLA':
            result = self.ask('M9')
            if result.startswith('?'):
                raise InstrIOError(cleandoc('''IPS120-10 did not set the
                    heater mode to {}'''.format(mode)))
        else:
            raise ValueError(cleandoc(''' Invalid parameter {} sent to
                IPS120-10 set_mode method'''.format(mode)))

    @secure_communication()
    def set_communications_protocol(self, use_line_feed, extended_resolution):
        """
        """
        if use_line_feed:
            if extended_resolution:
                self.write('Q6')
            else:
                self.write('Q2')
        else:
            if extended_resolution:
                self.write('Q4')
            else:
                self.write('Q0')

    @secure_communication()
    def read_parameter(self, parameter):
        """
        """
        par = _PARAMETER_DICT.get(parameter, None)
        if par:
            return self.ask('R{}'.format(par))[1:]
        else:
            raise ValueError(cleandoc(''' Invalid parameter {} sent to
                IPS120-10 read_parameter method'''.format(parameter)))

    def check_connection(self):
        """
        """
        control = self.control
        if (control == 'Local & Locked' or control == 'Local & Unlocked'):
            return False
        else:
            return True

    @instrument_property
    def heater_state(self):
        """
        """
        status = self._get_status()
        heat = int(status[8])
        if heat in (0, 2):
            return 'OFF'
        elif heat == 1:
            return 'ON'
        else:
            raise ValueError(cleandoc('''The switch is in fault or absent'''))

    @heater_state.setter
    @secure_communication()
    def heater_state(self, state):
        """
        """
        if state == 'ON':
            result = self.ask('H1')
            if result.startswith('?'):
                raise InstrIOError(cleandoc('''IPS120-10 did not set the
                    heater state to {}'''.format(state)))
        elif state == 'OFF':
            result = self.ask('H0')
            if result.startswith('?'):
                raise InstrIOError(cleandoc('''IPS120-10 did not set the
                    heater state to {}'''.format(state)))
        else:
            raise ValueError(cleandoc(''' Invalid parameter {} sent to
                IPS120-10 set_heater_state method'''.format(state)))

    @instrument_property
    def control(self):
        """
        """
        status = self._get_status()
        control = int(status[6])
        state = [k for k, v in _CONTROL_DICT.iteritems() if v == control]
        if state:
            return state[0]
        else:
            return 'Auto-Run-Down'

    @control.setter
    @secure_communication()
    def control(self, control):
        """
        """
        value = _CONTROL_DICT.get(control, None)
        if value:
            result = self.ask('C{}'.format(value))
            if result.startswith('?'):
                raise InstrIOError(cleandoc('''IPS120-10 did not set the
                    control to {}'''.format(control)))
        else:
            raise ValueError(cleandoc(''' Invalid parameter {} sent to
                IPS120-10 set_control method'''.format(control)))

    @instrument_property
    def activity(self):
        """
        """
        status = self._get_status()
        act = int(status[4])
        return [k for k, v in _ACTIVITY_DICT.iteritems() if v == act][0]

    @activity.setter
    @secure_communication()
    def activity(self, value):
        """
        """
        par = _ACTIVITY_DICT.get(value, None)
        if par:
            result = self.ask('A{}'.format(par))
            if result.startswith('?'):
                raise InstrIOError(cleandoc('''IPS120-10 did not set the
                    activity to {}'''.format(value)))
        else:
            raise ValueError(cleandoc(''' Invalid parameter {} sent to
                IPS120-10 set_activity method'''.format(value)))

    @instrument_property
    def persistent_current(self):
        """
        """
        return float(self.read_parameter('Persistent magnet current'))

    @instrument_property
    def persistent_field(self):
        """
        """
        return float(self.read_parameter('Persistent magnet field'))

    @instrument_property
    def target_current(self):
        """
        """
        return float(self.read_parameter('Target current'))

    @target_current.setter
    @secure_communication()
    def target_current(self, target):
        """
        """
        result = self.ask("I{}".format(target))
        if result.startswith('?'):
            raise InstrIOError(cleandoc('''IPS120-10 did not set the
                    target current to {}'''.format(target)))

    @instrument_property
    def current_sweep_rate(self):
        """
        """
        return float(self.read_parameter('Current sweep rate'))

    @current_sweep_rate.setter
    @secure_communication()
    def current_sweep_rate(self, rate):
        """
        """
        # amps/min
        result = self.ask("S{}".format(rate))
        if result.startswith('?'):
            raise InstrIOError(cleandoc('''IPS120-10 did not set the
                    rate field to {}'''.format(rate)))

    @instrument_property
    def target_field(self):
        """
        """
        return float(self.read_parameter('Target field'))

    @target_field.setter
    @secure_communication()
    def target_field(self, target):
        """
        """
        result = self.ask("J{}".format(target))
        if result.startswith('?'):
            raise InstrIOError(cleandoc('''IPS120-10 did not set the
                    target field to {}'''.format(target)))

    @instrument_property
    def field_sweep_rate(self):
        """
        """
        return float(self.read_parameter('Field sweep rate'))

    @field_sweep_rate.setter
    @secure_communication()
    def field_sweep_rate(self, rate):
        """
        """
        # tesla/min
        result = self.ask("T{}".format(rate))
        if result.startswith('?'):
            raise InstrIOError(cleandoc('''IPS120-10 did not set the
                    rate field to {}'''.format(rate)))

    @secure_communication()
    def _get_status(self):
        """
        """
        status = self.ask('X')
        if status:
            return status.strip()
        else:
            raise InstrIOError('''IPS120-10 did not return its status''')

DRIVERS = {'IPS12010': IPS12010}
