# -*- coding: utf-8 -*-
"""

"""

from driver_tools import (VisaInstrument, InstrIOError,
                          secure_communication)

class LockInSR830(VisaInstrument):
    """
    """

    def __init__(self, *args, **kwargs):

        super(LockInSR830, self).__init__(*args, **kwargs)
        bus = kwargs.get('bus','GPIB')
        if bus == 'GPIB':
            self.write('OUTX1')
        elif bus == 'RS232':
            self.write('OUTX0')
        else:
            raise InstrIOError('In invalib bus was specified')

    @secure_communication
    def read_x(self):
        """
        """
        value = self.ask_for_values('OUTP?1')
        if not value:
            raise InstrIOError('The command did not complete correctly')
        else:
            return value[0]

    @secure_communication
    def read_y(self):
        """
        """
        value = self.ask_for_values('OUTP?2')
        if not value:
            raise InstrIOError('The command did not complete correctly')
        else:
            return value[0]

    @secure_communication
    def read_xy(self):
        """
        """
        values = self.ask_for_values('SNAP?1,2')
        if not values:
            raise InstrIOError('The command did not complete correctly')
        else:
            return values

    @secure_communication
    def read_amplitude(self):
        """
        """
        value = self.ask_for_values('OUTP?3')
        if not value:
            return InstrIOError('The command did not complete correctly')
        else:
            return value[0]

    @secure_communication
    def read_phase(self):
        """
        """
        value = self.ask_for_values('OUTP?4')
        if not value:
            raise InstrIOError('The command did not complete correctly')
        else:
            return value[0]

    @secure_communication
    def read_amp_and_phase(self):
        """
        """
        values = self.ask_for_values('SNAP?3,4')
        if not values:
            raise InstrIOError('The command did not complete correctly')
        else:
            return values