# -*- coding: utf-8 -*-
"""
"""
from atom.api import (Float, Bool, Value, Str, Int, set_default)

import time
import logging
from inspect import cleandoc

from hqc_meas.tasks.api import InstrumentTask, InstrTaskInterface


class SetDCVoltageTask(InstrumentTask):
    """Set a DC voltage to the specified value.

    The user can choose to limit the rate by choosing an appropriate back step
    (larger step allowed), and a waiting time between each step.

    """
    # Target value for the source (dynamically evaluated)
    target_value = Str().tag(pref=True)

    # Largest allowed step when changing the output of the instr.
    back_step = Float().tag(pref=True)

    # Time to wait between changes of the output of the instr.
    delay = Float(0.01).tag(pref=True)

    # Whether the current value of the instr should be checked each time.
    check_value = Bool(False).tag(pref=True)

    #Actually a Float but I don't want it to get initialised at 0
    last_value = Value()

    parallel = set_default({'activated': True, 'pool': 'instr'})
    loopable = True
    task_database_entries = set_default({'voltage': 1.0})

#    @smooth_instr_crash
#    def process(self, target_value=None):
#        """ Set the output of the instr.
#
#        """
#        if not self.driver:
#            self.start_driver()
#
#        if self.driver.owner != self.task_name:
#            self.driver.owner = self.task_name
#            if self.driver.function != 'VOLT':
#                log = logging.getLogger()
#                mes = cleandoc('''Instrument assigned to task {} is not
#                    configured to output a voltage'''.format(self.task_name))
#                log.fatal(mes)
#                self.root_task.task_stop.set()
#                return False

    def smooth_set(self, target_value, setter):
        """ Smoothly set the voltage.

        target_value : float
            Voltage to reach.

        setter : callable
            Function to set the voltage, should take as single argument the
            value.

        """
        if target_value is not None:
            value = target_value
        else:
            value = self.format_and_eval_string(self.target_value)

        if self.check_value:
            last_value = self.driver.voltage
        elif self.last_value is None:
            last_value = self.driver.voltage
        else:
            last_value = self.last_value

        if abs(last_value - value) < 1e-12:
            self.write_in_database('voltage', value)
            return True

        elif self.back_step == 0:
            self.write_in_database('voltage', value)
            setter(value)
            return True

        else:
            if (value - last_value)/self.back_step > 0:
                step = self.back_step
            else:
                step = -self.back_step

        if abs(value-last_value) > abs(step):
            while True:
                # Avoid the accumulation of rounding errors
                last_value = round(last_value + step, 9)
                setter(last_value)
                if abs(value-last_value) > abs(step):
                    time.sleep(self.delay)
                else:
                    break

        setter(value)
        self.last_value = value
        self.write_in_database('voltage', value)

        return True

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(SetDCVoltageTask, self).check(*args, **kwargs)
        val = None
        if self.target_value:
            try:
                val = self.format_and_eval_string(self.target_value)
            except Exception:
                test = False
                traceback[self.task_path + '/' + self.task_name + '-volt'] = \
                    cleandoc('''Failed to eval the target value formula
                        {}'''.format(self.target_value))
        self.write_in_database('voltage', val)
        return test, traceback

KNOWN_PY_TASKS = [SetDCVoltageTask]


class SimpleSourceInterface(InstrTaskInterface):
    """
    """

    drivers_list = ['YokogawaGS200', 'Yokogawa7651']

    def perform(self, value=None):
        """
        """
        task = self.task
        if not task.driver:
            task.start_driver()

        if task.driver.owner != task.task_name:
            task.driver.owner = task.task_name
            if hasattr(task.driver, 'function') and\
                    self.driver.function != 'VOLT':
                log = logging.getLogger()
                mes = cleandoc('''Instrument assigned to task {} is not
                    configured to output a voltage'''.format(task.task_name))
                log.fatal(mes)
                task.root_task.task_stop.set()
                return False

        setter = lambda value: setattr(task.driver, 'voltage', value)

        return task.smooth_set(value, setter)


class MultiChannelSourceInterface(InstrTaskInterface):
    """
    """
    drivers_list = ['TinyBilt']

    #: Id of the channel to use.
    channel = Int().tag(pref=True)

    #: Reference to the driver for the channel.
    channel_driver = Value()

    def perform(self, value=None):
        """
        """
        task = self.task
        if not task.driver:
            task.start_driver()



        if task.driver.owner != task.task_name:
            task.driver.owner = task.task_name
            if hasattr(task.driver, 'function') and\
                    self.driver.function != 'VOLT':
                log = logging.getLogger()
                mes = cleandoc('''Instrument assigned to task {} is not
                    configured to output a voltage'''.format(task.task_name))
                log.fatal(mes)
                task.root_task.task_stop.set()
                return False

        setter = lambda value: setattr(task.driver, 'voltage', value)

        return task.smooth_set(value, setter)
