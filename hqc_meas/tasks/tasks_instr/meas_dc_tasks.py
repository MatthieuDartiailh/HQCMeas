# -*- coding: utf-8 -*-
"""
"""
from atom.api import Float, set_default
from time import sleep

from hqc_meas.tasks.api import InstrumentTask
from hqc_meas.tasks.tools.task_decorator import smooth_instr_crash


class MeasDCVoltageTask(InstrumentTask):
    """Measure a dc voltage.

    Wait for any parallel operation before execution and then wait the
    specified time before perfoming the measure.

    """
    # Time to wait before the measurement.
    wait_time = Float().tag(pref=True)

    driver_list = ['Agilent34410A', 'Keithley2000']
    task_database_entries = set_default({'voltage': 1.0})

    def __init__(self, **kwargs):
        super(MeasDCVoltageTask, self).__init__(**kwargs)
        self.make_wait(wait=['instr'])

    @smooth_instr_crash
    def process(self):
        """
        """
        if not self.driver:
            self.start_driver()

        sleep(self.wait_time)

        value = self.driver.read_voltage_dc()
        self.write_in_database('voltage', value)

        return True

KNOWN_PY_TASKS = [MeasDCVoltageTask]
