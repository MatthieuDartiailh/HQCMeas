# -*- coding: utf-8 -*-
"""

"""

from driver_tools import (VisaInstrument, InstrIOError,
                          secure_communication)

class LockInSR7265(VisaInstrument):
    """
    """

    @secure_communication
    def read_x(self):
        """
        """
        value = self.ask_for_values('X.')
        status = self._check_status()
        if status != 'OK' or not value:
            raise InstrIOError('The command did not complete correctly')
        else:
            return value[0]

    @secure_communication
    def read_y(self):
        """
        """
        value = self.ask_for_values('Y.')
        status = self._check_status()
        if status != 'OK' or not value:
            raise InstrIOError('The command did not complete correctly')
        else:
            return value[0]

    @secure_communication
    def read_xy(self):
        """
        """
        values = self.ask_for_values('XY.')
        status = self._check_status()
        if status != 'OK' or not values:
            raise InstrIOError('The command did not complete correctly')
        else:
            return values

    @secure_communication
    def read_amplitude(self):
        """
        """
        value = self.ask_for_values('MAG.')
        status = self._check_status()
        if status != 'OK' or not value:
            return InstrIOError('The command did not complete correctly')
        else:
            return value[0]

    @secure_communication
    def read_phase(self):
        """
        """
        value = self.ask_for_values('PHA.')
        status = self._check_status()
        if status != 'OK' or not value:
            raise InstrIOError('The command did not complete correctly')
        else:
            return value[0]

    @secure_communication
    def read_amp_and_phase(self):
        """
        """
        values = self.ask_for_values('MP.')
        status = self._check_status()
        if status != 'OK' or not values:
            raise InstrIOError('The command did not complete correctly')
        else:
            return values

    @secure_communication
    def _check_status(self):
        """
        """
        bites = self.ask('ST')
        status_byte = ('{0:08b}'.format(ord(bites[0])))[::-1]
        if not status_byte[0]:
            return 'Command went wrong'
        else:
            return 'OK'
            
class LockInSR7270(LockInSR7265):
    """
    """

    def __init__(self, *args, **kwargs):

        super(LockInSR7270, self).__init__(*args, **kwargs)
        self.term_chars = '\0'
        
    @secure_communication
    def _check_status(self):
        """
        """
        bites = self.read()
        status_byte = ('{0:08b}'.format(ord(bites[0])))[::-1]
        if not status_byte[0]:
            return 'Command went wrong'
        else:
            return 'OK'