# -*- coding: utf-8 -*-
# =============================================================================
# module : alazar_tasks.py
# author : Benjamin Huard
# license : MIT license
# =============================================================================
"""

"""
from atom.api import (Str, Bool, set_default, Enum)
from inspect import cleandoc
import numpy as np

from hqc_meas.tasks.api import InstrumentTask


class Demod_CHA_Alazar(InstrumentTask):
    """ Get the average quadratures of the signal on CHA.

    """

    average_nb = Str().tag(pref=True)

    freq = Str().tag(pref=True)

    timebeforetrig = Str().tag(pref=True)

    timeaftertrig = Str().tag(pref=True)
    
    separateoddeventrigs = Bool(False).tag(pref=True)

    driver_list = ['Alazar935x']
    
    task_database_entries = set_default({'trace_data': np.array([1.0])})

    def perform(self):
        """
        """
        if not self.driver:
            self.start_driver()

        if self.driver.owner != self.task_name:
            self.driver.owner = self.task_name


        avg = self.average_nb

        avgA_even = 0
        avgA_odd = 0
        avgB_even = 0
        avgB_odd = 0
        recordnb = 0
        if self.separateoddeventrigs:
            while avg > 0:
                answer = self.driver.getAIQ(timebeforetrig / 2, freq, timeaftertrig / 2, Math.Min(average_nb, 1000))
                for iter = 0 To answer.record_nb / 2 - 1
                    avgA_even = avgA_even + answer.averageA(2 * iter)
                    avgB_even = avgB_even + answer.averageB(2 * iter)
                    avgA_odd = avgA_odd + answer.averageA(2 * iter + 1)
                    avgB_odd = avgB_odd + answer.averageB(2 * iter + 1)
                Next
                recordnb += answer.record_nb / 2
                avg = avg - 1000
            End While
            data_file.WriteLine(currentline & avgA_even / recordnb & vbTab & avgB_even / recordnb & vbTab & avgA_odd / recordnb & vbTab & avgB_odd / recordnb)
        else:
            While avg > 0
                answer = Alazar.getAIQ(timebeforetrig / 2, freq, timeaftertrig / 2, Math.Min(average_nb, 1000))
                For iter As Integer = 0 To answer.record_nb - 1
                    avgA_even = avgA_even + answer.averageA(iter)
                    avgB_even = avgB_even + answer.averageB(iter)

                    'avgA_even = avgA_even + Math.Sqrt(answer.averageA(iter) ^ 2 + answer.averageB(iter) ^ 2)
                    'avgB_even = avgB_even + answer.averageB(iter)
                Next
                recordnb += answer.record_nb
                avg = avg - 1000
            End While
            data_file.WriteLine(currentline & avgA_even / recordnb & vbTab & avgB_even / recordnb)
        End If











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
                traceback[self.task_path + '/' + self.task_name + '-average_nb'] = \
                    cleandoc('''Failed to eval the avg nb field formula
                        {}: {}'''.format(self.average_nb, e))

        return test, traceback

KNOWN_PY_TASKS = [OscilloGetTraceTask]





  Public Sub get_traces_Alazar(ByVal average_nb As Integer, ByVal timebeforetrig As Double, ByVal timeaftertrig As Double)
        currentline = ""
        Try
            For Each param In param_table
                currentline = currentline & param.current & vbTab
            Next
        Catch ex As Exception
        End Try

        Dim avg As Integer = average_nb

        Dim recordnb As Integer = 0

        Dim answer As Stats_to_VB = Alazar.getsumtraces(timebeforetrig / 2, timeaftertrig / 2, Math.Min(average_nb, 1000))
        Dim tracelength As Integer = answer.averageA.Length
        Dim recordsnb As Integer = answer.record_nb

        Dim avgA(tracelength) As Double
        Dim avgB(tracelength) As Double


        While avg > 0


            For i As Integer = 0 To tracelength - 1

                avgA(i) = avgA(i) + answer.averageA(i)
                avgB(i) = avgB(i) + answer.averageB(i)



            Next
            recordnb += answer.record_nb
            avg = avg - 1000

            If avg > 0 Then
                answer = Alazar.getsumtraces(timebeforetrig / 2, timeaftertrig / 2, Math.Min(average_nb, 1000))
            End If
        End While


        For i As Integer = 0 To tracelength - 1
            avgA(i) = avgA(i) / recordnb
            avgB(i) = avgB(i) / recordnb
            data_file.WriteLine(currentline & i & vbTab & avgA(i) & vbTab & avgB(i))

        Next
       
        'For iter As Integer = 0 To recordsnb - 1
        '    For i As Integer = 0 To tracelength - 1


        '        data_file.WriteLine(currentline & i & vbTab & answer.traceCHA(iter, i) & vbTab & answer.traceCHB(iter, i))
        '    Next

        'Next

    End Sub