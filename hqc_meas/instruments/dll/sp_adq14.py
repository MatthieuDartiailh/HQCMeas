# -*- coding: utf-8 -*-
# =============================================================================
# module : alazar935x.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""

This module defines drivers for SP devices cards using the ADQAPI.dll.

:Contains:
    SPADQ14

"""
import os
import time
import atexit
import ctypes
import timeit
import numpy as np

from pyclibrary import CLibrary, build_array, cast_to

from ..dll_tools import DllInstrument


class ADQControlUnit(object):
    """Control unit for the ADQ devices.

    """

    _instance = None

    def __new__(cls, library):
        if cls._instance is not None:
            return cls._instance

        self = super(ADQControlUnit, cls).__new__(cls)
        self.library = library
        self.id = library.CreateADQControlUnit()()
        self._boards = []
        atexit.register(self._cleanup)
        cls._instance = self
        return self

    def list_boards(self):
        """List the detected boards.

        """
        res = self.library.ControlUnit_ListDevices(self.id)
        assert res()
        arr = [res[1][i] for i in range(res[2])]
        return arr

    def setup_board(self, board_id):
        """Prepare a board for communication and return its index.

        """
        if board_id not in self._boards:
            assert self.library.ControlUnit_OpenDeviceInterface(self.id,
                                                                board_id)()
            assert self.library.ControlUnit_SetupDevice(self.id,
                                                        board_id)()
            self._boards.append(board_id)
        return self._boards.index(board_id) + 1
        
    def destroy_board(self, b_id):
        """
        """
        self.library.ControlUnit_DeleteADQ(self.id, b_id)
        del self._boards[b_id-1]

    def _cleanup(self):
        """Make sure we disconnect all the boards and destroy the unit.

        """
        for i, b_id in enumerate(self._boards):
            self.library.ControlUnit_DeleteADQ(self.id, i)

        self.library.DeleteADQControlUnit(self.id)


class SPADQ14(DllInstrument):

    library = 'ADQAPI.dll'

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(SPADQ14, self).__init__(connection_info, caching_allowed,
                                      caching_permissions, auto_open)

        cache_path = unicode(os.path.join(os.path.dirname(__file__),
                                          'cache/adq14.pycctypes.libc'))
        self._dll = CLibrary('ADQAPI.dll', ['ADQAPI.h'],
                             cache=cache_path, prefix=['ADQ_', 'ADQ'],
                             convention='cdll')
        self._infos = connection_info
        self._id = None
        
        if auto_open:
            self.open_connection()

    def open_connection(self):
        """Setup the right card based on the vendor id.

        """
        cu = ADQControlUnit(self._dll)
        boards = cu.list_boards()
        board_id = None
        for i, b in enumerate(boards):
            if b.ProductID == self._dll.PID_ADQ14:
                # Setup the communication.
                # Far from ideal but I do not know how to link serail number 
                # and Vendor ID, should ask !
                b_id = cu.setup_board(i)
                serial = self._dll.GetBoardSerialNumber(cu.id, b_id)()
                if serial == self._infos['instr_id']:
                    board_id = b_id
                    break

        if board_id is None:
            raise ValueError('No ADQ14 with id %s' % self._infos['instr_id'])

        assert self._dll.IsStartedOK(cu.id, board_id)()
        self._cu_id = cu.id
        self._id = board_id
        
        import os
        self._dll.ADQControlUnit_EnableErrorTrace(cu.id, 3, os.path.dirname(__file__))

    def close_connection(self):
        """Do not explicitly close the board as it may re-arrange the boards
        indexes.

        """
        cu = ADQControlUnit(self._dll)
        cu.destroy_board(self._id)

    def configure_board(self):
        """Set the usual settings for the card.

        """

        # Use the internal clock with an external 10MHz reference.
        self._dll.SetClockSource(self._cu_id, self._id,
                                 self._dll.ADQ_CLOCK_INT_EXTREF)

        # Set trigger to external source.
        self._dll.SetTriggerMode(self._cu_id, self._id,
                                 self._dll.ADQ_EXT_TRIGGER_MODE)

        # Set external trigger to triger on rising edge.
        self._dll.SetExternTrigEdge(self._cu_id, self._id, 1)

    def get_traces(self, duration, delay, records_per_capture):
        """Acquire the average signal on both channels.

        Parameters
        ----------
        duration : float
            Time during which to acquire the data (in seconds)

        delay : float
            Time to wait after a trigger before starting next measure
            (in seconds).

        records_per_capture : int
            Number of records to acquire (per channel)

        """
        # Set trigger delay
        n = int(round(delay/2e-9))
        assert 0 <= n < 62, 'Delay must be at most 61 cycles (%d)' % n
        assert self._dll.SetTriggerHoldOffSamples(self._cu_id, self._id, n)()

        # Number of samples per record.
        samples_per_sec = 500e6
        samples_per_record = int(samples_per_sec*duration)

        assert self._dll.MultiRecordSetup(self._cu_id, self._id, 
                                          records_per_capture,
                                          samples_per_record)()

        # Alloc memory for both channels (using numpy arrays) 
        buffer_size = samples_per_record*records_per_capture
        ch1_buff = np.ascontiguousarray(np.empty(buffer_size, dtype=np.int16))
        ch2_buff = np.ascontiguousarray(np.empty(buffer_size, dtype=np.int16))
        buffers = (ctypes.c_void_p*2)(ch1_buff.ctypes.data_as(ctypes.c_void_p),
                                      ch2_buff.ctypes.data_as(ctypes.c_void_p))
#        buffers = (ctypes.c_void_p*2)(cast_to(self._dll, ch1_buff.ctypes.data,
#                                              ctypes.c_void_p),
#                                      cast_to(self._dll, ch1_buff.ctypes.data,
#                                              ctypes.c_void_p))
#        buffers = build_array(self._dll, ctypes.c_void_p, 2,
#                              [cast_to(self._dll, ch1_buff.ctypes.data,
#                                       ctypes.c_void_p),
#                               cast_to(self._dll, ch2_buff.ctypes.data,
#                                       ctypes.c_void_p)
#                               ])
        
        ch1_avg = np.zeros(samples_per_record)        
        
        cu = self._cu_id
        id_ = self._id
        bytes_per_sample = self._dll.GetNofBytesPerSample(cu, id_)[2]
        
        assert self._dll.DisarmTrigger(self._cu_id, self._id)()
        while not self._dll.ArmTrigger(self._cu_id, self._id)():
            time.sleep(0.0001)
            
        # Wait for all records to be acquired.
        retrieved_records = 0
        acq_records = self._dll.GetAcquiredRecords.func
        get_data = self._dll.GetData.func
        while retrieved_records < records_per_capture:
            # Wait for a record to be acquired.
            n_records = (acq_records(cu, id_) - retrieved_records)
            if not n_records:
                continue
            
            assert get_data(cu, id_, buffers, 
                            n_records*samples_per_record, 
                            bytes_per_sample, 
                            retrieved_records, 
                            n_records,
                            0x3,
                            0,
                            samples_per_record, 
                            0x00)
                                     
            ch1_avg += np.sum(np.reshape(ch1_buff, 
                                         (-1, samples_per_record))[:n_records],
                              0)
            retrieved_records += n_records
            
        ch1_avg /= records_per_capture
 
        self._dll.DisarmTrigger(self._cu_id, self._id)
        self._dll.MultiRecordClose(self._cu_id, self._id)

        ch1_avg = np.mean(np.reshape(ch1_buff, (records_per_capture, 
                                                samples_per_record)), 0)

        # Get the offset in volt for each channel (range is 1 V)
        ch1_offset = float(self._dll.GetAdjustableBias(cu, id_, 1)[3])/2**15*1
#        ch2_offset = float(self._dll.GetAdjustableBias(cu, id_, 2)[3])/2**15*1

        # Get the real values in volt
        ch1_avg -= 2**15
        ch1_avg /= 65535
        ch1_avg += ch1_offset
#        ch2_avg -= 2**15
#        ch2_avg /= 65535
#        ch2_avg += ch2_offset

        return ch1_avg, None
        
# Pseudo streaming version
## Alloc memory for both channels (using numpy arrays) so that we get
## records one by one and average them in numpy arrays (float)
#ch1_buff = np.empty(samples_per_record, dtype=np.int16)
#ch2_buff = np.empty(samples_per_record, dtype=np.int16)
#buffers = build_array(self._dll, ctypes.c_void_p, 2,
#                      [cast_to(self._dll, ch1_buff.ctypes.data,
#                               ctypes.c_void_p),
#                       cast_to(self._dll, ch2_buff.ctypes.data,
#                               ctypes.c_void_p)
#                       ])
#ch1_avg = np.zeros(samples_per_record)
#ch2_avg = np.zeros(samples_per_record)
#
#
#retrieved_records = 0
#cu = self._cu_id
#id_ = self._id
#t = 1.* samples_per_record/samples_per_sec/3
#bytes_per_sample = self._dll.GetNofBytesPerSample(cu, id_)[2]
#
#self._dll.DisarmTrigger(self._cu_id, self._id)
#while not self._dll.ArmTrigger(self._cu_id, self._id)():
#    time.sleep(0.0001)
#    
#while retrieved_records < records_per_capture:
#    # Wait for a record to be acquired.
#    total_time = 0
#    while not self._dll.GetAcquiredAll(cu, id_)():
#        time.sleep(t)
#        total_time += t
#        if total_time > 1:
#            raise Exception('Timeout')
#    self._dll.GetData(cu, id_, buffers, 
#                      samples_per_record, bytes_per_sample, 0,
#                      1, 0x3, 0, samples_per_record, 0x00)
#    ch1_avg += ch1_buff
#    ch2_avg += ch2_buff
#    retrieved_records += 1
#
#self._dll.DisarmTrigger(self._cu_id, self._id)
#self._dll.MultiRecordClose(self._cu_id, self._id)
#
#ch1_avg /= records_per_capture
#ch2_avg /= records_per_capture
#
## Get the offset in volt for each channel (range is 1 V)
#ch1_offset = float(self._dll.GetAdjustableBias(cu, id_, 1)[3])/2**15*1
#ch2_offset = float(self._dll.GetAdjustableBias(cu, id_, 2)[3])/2**15*1
#
## Get the real values in volt
#ch1_avg -= 2**15
#ch1_avg /= 65535
#ch1_avg += ch1_offset
#ch2_avg -= 2**15
#ch2_avg /= 65535
#ch2_avg += ch2_offset
#
#return ch1_avg, ch2_avg

DRIVERS = {'ADQ14': SPADQ14}
