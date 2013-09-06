# -*- coding: utf-8 -*-
"""
"""
from visa import Instrument, VisaIOError

class YokogawaGS200(Instrument):
    """
    """

    def __init__(self, connection_str):

        super(YokogawaGS200, self).__init__(connection_str)

    def set_voltage(self, set_point):
        """
        """
        self.write(":SOURce:LEVel {}".format(set_point))
        value = self.ask_for_values('SOURce:LEVel?')[0]
        if value != set_point:
            raise VisaIOError('Instrument did not set correctly the voltage')

    def get_voltage(self):
        """
        """
        return self.ask_for_values(":SOURce:LEVel?")[0]

    def set_function(self, mode):
        """
        """
        if mode == 'VOLT':
            self.write(':SOURce:FUNCtion VOLT')
            value = self.ask('SOURce:FUNCtion?')
            if value != 'VOLT':
                raise VisaIOError('Instrument did not set correctly the mode')
        elif mode == 'CURR':
            self.write(':SOURce:FUNCtion CURR')
            value = self.ask('SOURce:FUNCtion?')
            if value != 'CURR':
                raise VisaIOError('Instrument did not set correctly the mode')
        else:
            print 'Mode unsupported for the YokogawaGS200'
