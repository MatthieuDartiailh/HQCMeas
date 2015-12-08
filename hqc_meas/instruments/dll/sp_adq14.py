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
        self.id = library.CreateADQControlUnit()
        self._boards = set()
        atexit.register(self._cleanup)
        cls._instance = self
        return self

    def list_boards(self):
        """List the detectd board.

        """
        arr = build_array(self.library, self.library.InfoListEntry, 50)
        assert self.library.ControlUnit_ListDevices(self.id, arr, 50)
        return arr

    def setup_board(self, board_id):
        """Prepare a board for communication.

        """
        self.library.ControlUnit_OpenDeviceInterface(self.id, board_id)
        self.library.ControlUnit_SetupDevice(self.id, board_id)
        self._boards.add(board_id)

    def _cleanup(self):
        """Make sure we disconnect all the boards and destroy the unit.

        """
        for b_id in self._boards.items():
            self.library.ControlUnit_DeleteADQ(self.id, b_id)

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
                             cache=cache_path, prefix=['ADQ'],
                             convention='cdll')

        self._infos = connection_info
        self._id = None

    def open_connection(self):
        """Setup the right card based on the vendor id.

        """
        cu = ADQControlUnit(self._dll)
        boards = cu.list_boards()
        board_id = None
        for i, b in enumerate(boards):
            if (b.ProductID == self._dll.PID_AQD14 and
                    int(b.VendorID) == self._infos['instr_id']):
                board_id = i

        if board_id is None:
            raise ValueError('No ADQ214 with id %d' % self._infos['instr_id'])

        cu.setup_board(board_id)
        assert self._dll.IsStartedOk(cu.id, board_id)
        self._cu_id = cu.id
        self._id = board_id

    def close_connection(self):
        """Do not explicitly close the board as it may re-arrange the boards
        indexes.

        """
        pass

    def configure_board(self):
        """Set the usual settings for the card.

        """

        # Use the internal clock with an external 10MHz reference.
        self._dll.SetClockSource(self._cu_id, self._id,
                                 self.ADQ_CLOCK_INT_EXTREF)

        # Set trigger to external source.
        self._dll.SetTriggerMode(self._cu_id, self._id,
                                 self.ADQ_EXT_TRIGGER_MODE)

        # Set external trigger to triger on rising edge.
        self._dll.SetExternTrigEdge(1)

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
        assert 0 < n < 62, 'Delay must be at most 61 cycles (%d)' % n
        self._dll.SetExternalTriggerDelay(self._cu_id, self._id, n)

        # Number of samples per record.
        samples_per_sec = 500e6
        samples_per_record = int(samples_per_sec*duration)

        self._dll.MultiRecordSetup(self._cu_id, self._id, records_per_capture,
                                   samples_per_record)

        # Alloc memory for both channels (using numpy arrays) so that we get
        # records one by one and average them in numpy arrays (float)
        ch1_buff = np.empty(samples_per_record, dtype=np.int16)
        ch2_buff = np.empty(samples_per_record, dtype=np.int16)
        buffers = build_array('void *', 2,
                              [cast_to(self._dll, 'void *',
                                       ch1_buff.ctypes.data),
                               cast_to(self._dll, 'void *',
                                       ch2_buff.ctypes.data)])
        ch1_avg = np.zeros(samples_per_record)
        ch2_avg = np.zeros(samples_per_record)

        while not self._dll.ArmTrigger(self._cu_id, self._id):
            time.sleep(0.0001)

        retrieved_records = 0
        cu = self._cu_id
        id_ = self._id
        t = 1.*samples_per_sec/samples_per_record/10
        bytes_per_sample = self._dll.GetNofBytesPerSample(cu, id_)[0]
        while retrieved_records < records_per_capture:
            # Wait for a record to be acquired.
            while not self._dll.GetAcquired(cu, id_):
                time.sleep(t)
            self._dll.GetData(buffers, samples_per_record, bytes_per_sample, 0,
                              1, 0x3, 0, samples_per_record, 0x00)
            ch1_avg += ch1_buff
            ch2_avg += ch2_buff

        self._dll.MultiRecordClose(self._cu_id, self._id)

        ch1_avg /= records_per_capture
        ch2_avg /= records_per_capture

        # Get the offset in volt for each channel (range is 1 V)
        ch1_offset = float(self._dll.GetAdjustableBias(cu, id_, 1)[-1])/2**15*1
        ch2_offset = float(self._dll.GetAdjustableBies(cu, id_, 2)[-1])/2**15*1

        # Get the real values in volt
        ch1_avg -= 2**15
        ch1_avg /= 65535
        ch1_avg += ch1_offset
        ch2_avg -= 2**15
        ch2_avg /= 65535
        ch2_avg += ch2_offset

        return ch1_avg, ch2_avg

DRIVERS = {'ADQ14': SPADQ14}
