from inspect import cleandoc
from time import sleep
from ..driver_tools import (secure_communication, instrument_property)
from ..visa_tools import VisaInstrument


_GET_HEATER_DICT = {'0': 'Off',
                    '1': 'On'}

_ACTIVITY_DICT = {'To zero': 'SWEEP ZERO'}

FIELD_CURRENT_RATIO = 0.043963
OUT_FLUC = 3e-4


class CS4(VisaInstrument):

    @secure_communication()
    def make_ready(self):
        """
        """
        self.write('UNITS T')
        self.write('RANGE 0 100')

    def go_to_field(self, value, rate, auto_stop_heater=True,
                    post_switch_wait=30):
        """
        """
        # sweeping rate is converted from T/min to A/sec
        self.field_sweep_rate = rate / (60 * FIELD_CURRENT_RATIO)

        if self.target_field != value:

            if self.heater_state == 'Off':
                self.target_field = self.persistent_field
                self.heater_state = 'On'
                sleep(1)

            self.target_field = value

        if auto_stop_heater:
            self.heater_state = 'Off'
            sleep(post_switch_wait)
            self.activity = 'To zero'
            sleep(1)
            while self.target_field >= OUT_FLUC:
                sleep(1)

    @instrument_property
    def heater_state(self):
        """
        """
        heat = self.ask('PSHTR?').strip()
        try:
            return _GET_HEATER_DICT[heat]
        except KeyError:
            raise ValueError(cleandoc('''The switch is in fault or absent'''))

    @heater_state.setter
    @secure_communication()
    def heater_state(self, state):
        """
        """
        if state in ['On', 'Off']:
            self.write('PSHTR {}'.format(state))

    @instrument_property
    def field_sweep_rate(self):
        """
        """
        return float(self.ask('RATE? 0'))

    @field_sweep_rate.setter
    @secure_communication()
    def field_sweep_rate(self, rate):
        """
        """
        self.write("RATE 0 {}".format(rate))

    @instrument_property
    def target_field(self):
        """
        """
        return float(self.ask('IOUT?'))

    @target_field.setter
    @secure_communication()
    def target_field(self, target):
        """
        sweep the output intensity to reach the specified ULIM (in A)
        at a rate depending on the intensity, as defined in the range(s)
        """
        wait = abs(self.target_field - target) * 60 / self.field_sweep_rate
        self.write("ULIM {}".format(target))
        self.write("SWEEP UP")
        sleep(wait)
        while abs(self.target_field - target) <= OUT_FLUC:
            sleep(1)

    @instrument_property
    def persistent_field(self):
        """
        """
        return float(self.ask('IMAG?'))

    @instrument_property
    def activity(self):
        """
        """
        return self.ask('SWEEP?').strip()

    @activity.setter
    @secure_communication()
    def activity(self, value):
        """
        """
        par = _ACTIVITY_DICT.get(value, None)
        if par:
            self.write(par)
        else:
            raise ValueError(cleandoc(''' Invalid parameter {} sent to
                IPS120-10 set_activity method'''.format(value)))
