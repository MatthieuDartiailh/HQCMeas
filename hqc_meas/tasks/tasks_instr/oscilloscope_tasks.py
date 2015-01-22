# -*- coding: utf-8 -*-
# =============================================================================
# module : oscilloscope_tasks.py
# author : Benjamin Huard
# license : MIT license
# =============================================================================
"""

"""
from atom.api import (Str, Bool, set_default, Enum)
from inspect import cleandoc
import numpy as np

from hqc_meas.tasks.api import InstrumentTask


class OscilloGetTraceTask(InstrumentTask):
    """ Get the trace displayed on the oscilloscope.

    """
    trace = Enum('1', '2', '3', '4', 'TA', 'TB', 'TC', 'TD').tag(pref=True)

    average_nb = Str().tag(pref=True)

    highres = Bool(True).tag(pref=True)

    driver_list = ['LeCroy64Xi']
    task_database_entries = set_default({'trace_data': np.array([1.0]),
                                         'oscillo_config': ''})

    def perform(self):
        """
        """
        if not self.driver:
            self.start_driver()

        if self.driver.owner != self.task_name:
            self.driver.owner = self.task_name

        data = self.driver.get_channel(self.trace). \
            read_data_complete(self.highres)

        oscillo_config = 'Coupling {}, Average number {}'. \
            format(self.driver.get_channel(self.trace).sweep,
                   data['VERT_COUPLING'])
        self.write_in_database('oscillo_config', oscillo_config)

        # if the TrigArray lentgh is null, it's a simple single sweep waveform
        if data['TRIGTIME_ARRAY'][0] == 0:
            arr = np.rec.fromarrays([data['SingleSweepTimesValuesArray'],
                                     data['Volt_Value_array']],
                                    names=['Time (s)', 'Voltage (V)'])
            self.write_in_database('trace_data', arr)
        else:
            arr = np.rec.fromarrays([data['SEQNCEWaveformTimesValuesArray'],
                                     data['Volt_Value_array']],
                                    names=['Time (s)', 'Voltage (V)'])
            self.write_in_database('trace_data', )

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(OscilloGetTraceTask, self).check(*args,
                                                                 **kwargs)
        if self.average_nb:
            try:
                val = self.format_and_eval_string(self.average_nb)
                self.write_in_database('Average number', val)
            except Exception as e:
                test = False
                traceback[self.task_path + '/' + self.task_name + '-avgnb'] = \
                    cleandoc('''Failed to eval the avg nb field formula
                        {}: {}'''.format(self.average_nb, e))

        return test, traceback

KNOWN_PY_TASKS = [OscilloGetTraceTask]
