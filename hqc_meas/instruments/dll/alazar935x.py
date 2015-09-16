# -*- coding: utf-8 -*-
# =============================================================================
# module : alazar935x.py
# author : Benjamin Huard & Nathanael Cottet
# license : MIT license
# =============================================================================
"""

This module defines drivers for Alazar using DLL Library.

:Contains:
    Alazar935x

To read well the Dll of the Alazar9351, Visual C++ Studio is needed.

"""
import os
import time
import math
import numpy as np
import ctypes
from inspect import cleandoc

from pyclibrary import CLibrary

from ..dll_tools import DllInstrument

class DMABuffer:
    '''Buffer suitable for DMA transfers.

    AlazarTech digitizers use direct memory access (DMA) to transfer
    data from digitizers to the computer's main memory. This class
    abstracts a memory buffer on the host, and ensures that all the
    requirements for DMA transfers are met.

    DMABuffers export a 'buffer' member, which is a NumPy array view
    of the underlying memory buffer

    Args:

      bytes_per_sample (int): The number of bytes per samples of the
      data. This varies with digitizer models and configurations.

      size_bytes (int): The size of the buffer to allocate, in bytes.

    '''
    def __init__(self, bytes_per_sample, size_bytes):
        self.size_bytes = size_bytes
        ctypes.cSampleType = ctypes.c_uint8
        npSampleType = np.uint8
        if bytes_per_sample > 1:
            ctypes.cSampleType = ctypes.c_uint16
            npSampleType = np.uint16

        self.addr = None
        if os.name == 'nt':
            MEM_COMMIT = 0x1000
            PAGE_READWRITE = 0x4
            ctypes.windll.kernel32.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_long,
                                                     ctypes.c_long, ctypes.c_long]
            ctypes.windll.kernel32.VirtualAlloc.restype = ctypes.c_void_p
            self.addr = ctypes.windll.kernel32.VirtualAlloc(
                0, ctypes.c_long(size_bytes), MEM_COMMIT, PAGE_READWRITE)
        elif os.name == 'posix':
            ctypes.libc.valloc.argtypes = [ctypes.c_long]
            ctypes.libc.valloc.restype = ctypes.c_void_p
            self.addr = ctypes.libc.valloc(size_bytes)
        else:
            raise Exception("Unsupported OS")

        ctypes.ctypes_array = (ctypes.cSampleType *
                        (size_bytes // bytes_per_sample)
                        ).from_address(self.addr)
        self.buffer = np.frombuffer(ctypes.ctypes_array, dtype=npSampleType)
        pointer, read_only_flag = self.buffer.__array_interface__['data']

    def __exit__(self):
        if os.name == 'nt':
            MEM_RELEASE = 0x8000
            ctypes.windll.kernel32.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_long, ctypes.c_long]
            ctypes.windll.kernel32.VirtualFree.restype = ctypes.c_int
            ctypes.windll.kernel32.VirtualFree(ctypes.c_void_p(self.addr), 0, MEM_RELEASE)
        elif os.name == 'posix':
            ctypes.libc.free(self.addr)
        else:
            raise Exception("Unsupported OS")


class Alazar935x(DllInstrument):

    library = 'ATSApi.dll'

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(Alazar935x, self).__init__(connection_info, caching_allowed,
                                         caching_permissions, auto_open)

        cache_path = unicode(os.path.join(os.path.dirname(__file__),
                                          'cache/Alazar.pycctypes.libc'))
        self._dll = CLibrary('ATSApi.dll',
                             ['AlazarError.h', 'AlazarCmd.h', 'AlazarApi.h'],
                             cache=cache_path, prefix=['Alazar'],
                             convention='windll')

    def open_connection(self):
        """Do not need to open a connection

        """
        pass

    def close_connection(self):
        """Do not need to close a connection

        """
        pass

    def configure_board(self):
        board = self._dll.GetBoardBySystemID(1, 1)()
        # TODO: Select clock parameters as required to generate this
        # sample rate
        samplesPerSec = 500000000.0
        self._dll.SetCaptureClock(board,
                                  self._dll.EXTERNAL_CLOCK_10MHz_REF,
                                  500000000,
                                  self._dll.CLOCK_EDGE_RISING,
                                  0)
        # TODO: Select channel A input parameters as required.
        self._dll.InputControl(board,
                               self._dll.CHANNEL_A,
                               self._dll.DC_COUPLING,
                               self._dll.INPUT_RANGE_PM_400_MV,
                               self._dll.IMPEDANCE_50_OHM)

        # TODO: Select channel A bandwidth limit as required.
        self._dll.SetBWLimit(board, self._dll.CHANNEL_A, 0)


        # TODO: Select channel B input parameters as required.
        self._dll.InputControl(board, self._dll.CHANNEL_B,
                               self._dll.DC_COUPLING,
                               self._dll.INPUT_RANGE_PM_400_MV,
                               self._dll.IMPEDANCE_50_OHM)

        # TODO: Select channel B bandwidth limit as required.
        self._dll.SetBWLimit(board, self._dll.CHANNEL_B, 0)
        # TODO: Select trigger inputs and levels as required.
        self._dll.SetTriggerOperation(board, self._dll.TRIG_ENGINE_OP_J,
                                      self._dll.TRIG_ENGINE_J,
                                      self._dll.TRIG_EXTERNAL,
                                      self._dll.TRIGGER_SLOPE_POSITIVE,
                                      130,
                                      self._dll.TRIG_ENGINE_K,
                                      self._dll.TRIG_DISABLE,
                                      self._dll.TRIGGER_SLOPE_POSITIVE,
                                      128)

        # TODO: Select external trigger parameters as required.
        self._dll.SetExternalTrigger(board, self._dll.DC_COUPLING,
                                     self._dll.ETR_5V)

        # TODO: Set trigger delay as required.
        triggerDelay_sec = 0.
        triggerDelay_samples = int(triggerDelay_sec * samplesPerSec + 0.5)
        self._dll.SetTriggerDelay(board, triggerDelay_samples)

        # TODO: Set trigger timeout as required.
        #
        # NOTE: The board will wait for a for this amount of time for a
        # trigger event.  If a trigger event does not arrive, then the
        # board will automatically trigger. Set the trigger timeout value
        # to 0 to force the board to wait forever for a trigger event.
        #
        # IMPORTANT: The trigger timeout value should be set to zero after
        # appropriate trigger parameters have been determined, otherwise
        # the board may trigger if the timeout interval expires before a
        # hardware trigger event arrives.
        self._dll.SetTriggerTimeOut(board, 1000)
        # Configure AUX I/O connector as required
        self._dll.ConfigureAuxIO(board, self._dll.AUX_OUT_TRIGGER,
                                 0)

    def get_demod(self, timeaftertrig, recordsPerCapture,
                  recordsPerBuffer, freq, average):
        board = self._dll.GetBoardBySystemID(1, 1)()
        # Be sure that the acquisition is made for an integer number of periods
        timeaftertrig = int(timeaftertrig*freq)/(1.*freq)

        # Number of samples per record: must be divisible by 32
        samplesPerSec = 500000000.0
        samplesPerDemod = samplesPerSec*timeaftertrig
        if samplesPerDemod % 32 == 0:
            samplesPerRecord = int(samplesPerDemod)
        else:
            samplesPerRecord = int((samplesPerDemod)/32 + 1)*32

        retCode = self._dll.GetChannelInfo(board)()
        bitsPerSample = self._dll.GetChannelInfo(board)[1]
        if retCode != self._dll.ApiSuccess:
            raise ValueError(cleandoc(self._dll.AlazarErrorToText(retCode)))

        # Compute the number of bytes per record and per buffer
        channel_number = 2  # Acquisition on A and B
        ret, (boardhandle, memorySize_samples,
              bitsPerSample) = self._dll.GetChannelInfo(board)
        bytesPerSample = (bitsPerSample + 7) // 8
        bytesPerRecord = bytesPerSample * samplesPerRecord
        bytesPerBuffer = int(bytesPerRecord * recordsPerBuffer*channel_number)

        bufferCount = 4
        buffers = []
        for i in range(bufferCount):
            buffers.append(DMABuffer(bytesPerSample, bytesPerBuffer))
        # Set the record size
        self._dll.SetRecordSize(board, 0, samplesPerRecord)

        # Configure the number of records in the acquisition
        acquisition_timeout_sec = 10
        self._dll.SetRecordCount(board, recordsPerCapture)

        # Calculate the number of buffers in the acquisition
        buffersPerAcquisition = math.ceil(recordsPerCapture / recordsPerBuffer)

        self._dll.BeforeAsyncRead(board, 3,  # Channels A & B
                                  0,
                                  samplesPerRecord,
                                  int(recordsPerBuffer),
                                  recordsPerCapture,
                                  self._dll.ADMA_EXTERNAL_STARTCAPTURE |
                                  self._dll.ADMA_NPT)()

        # Post DMA buffers to board
        for buffer in buffers:
            self._dll.PostAsyncBuffer(board, buffer.addr, buffer.size_bytes)

        start = time.clock()  # Keep track of when acquisition started
        self._dll.StartCapture(board)  # Start the acquisition

        if time.clock() - start > acquisition_timeout_sec:
            self._dll.AbortCapture()
            raise Exception("Error: Capture timeout. Verify trigger")
            time.sleep(10e-3)

        # Preparation of the tables for the demodulation
        dem = np.arange(samplesPerDemod)
        coses = np.cos(2. * math.pi * dem * freq / samplesPerSec)
        sines = np.sin(2. * math.pi * dem * freq / samplesPerSec)

        dataA = np.empty((recordsPerCapture, samplesPerRecord))
        dataB = np.empty((recordsPerCapture, samplesPerRecord))

        buffersCompleted = 0
        while buffersCompleted < buffersPerAcquisition:
            # Wait for the buffer at the head of the list of available
            # buffers to be filled by the board.
            buffer = buffers[buffersCompleted % len(buffers)]
            self._dll.WaitAsyncBufferComplete(board, buffer.addr, 500)

            data = np.reshape(buffer.buffer,
                              (recordsPerBuffer*channel_number, -1))
            dataA[buffersCompleted*recordsPerBuffer:(buffersCompleted+1)*recordsPerBuffer] = data[:recordsPerBuffer]
            dataB[buffersCompleted*recordsPerBuffer:(buffersCompleted+1)*recordsPerBuffer] = data[recordsPerBuffer:]
            buffersCompleted += 1

            self._dll.PostAsyncBuffer(board, buffer.addr, buffer.size_bytes)

        self._dll.AbortAsyncRead(board)

        for buffer in buffers:
            buffer.__exit__()

        # Averaging and converting binary numbers into Volts
        dataA = (dataA-2**15)/65535*0.8
        dataB = (dataB-2**15)/65535*0.8

        # Re-shaping of the data for demodulation and demodulation
        if not samplesPerDemod == samplesPerRecord:
            dataA = dataA[:,1:samplesPerDemod + 1]
            dataB = dataB[:,1:samplesPerDemod + 1]

        if average:
            dataA = np.mean(dataA, axis=0)
            dataB = np.mean(dataB, axis=0)
            averageAI = 2*np.mean(dataA*coses)
            averageAQ = 2*np.mean(dataA*sines)
            averageBI = 2*np.mean(dataB*coses)
            averageBQ = 2*np.mean(dataB*sines)
        else:
            averageAI = 2*np.mean(dataA*coses, axis=1)
            averageAQ = 2*np.mean(dataA*sines, axis=1)
            averageBI = 2*np.mean(dataB*coses, axis=1)
            averageBQ = 2*np.mean(dataB*sines, axis=1)

        return (averageAI, averageAQ, averageBI, averageBQ)

    def get_traces(self, timeaftertrig, recordsPerCapture,
                   recordsPerBuffer, average):

        board = self._dll.GetBoardBySystemID(1, 1)()

        # Number of samples per record: must be divisible by 32
        samplesPerSec = 500000000.0
        samplesPerTrace = samplesPerSec*timeaftertrig
        if samplesPerTrace % 32 == 0:
            samplesPerRecord = int(samplesPerTrace)
        else:
            samplesPerRecord = int((samplesPerTrace)/32 + 1)*32

        retCode = self._dll.GetChannelInfo(board)()
        bitsPerSample = self._dll.GetChannelInfo(board)[1]
        if retCode != self._dll.ApiSuccess:
            raise ValueError(cleandoc(self._dll.AlazarErrorToText(retCode)))

        # Compute the number of bytes per record and per buffer
        channel_number = 2  # Acquisition on A and B
        ret, (boardhandle, memorySize_samples,
              bitsPerSample) = self._dll.GetChannelInfo(board)
        bytesPerSample = (bitsPerSample + 7) // 8
        bytesPerRecord = bytesPerSample * samplesPerRecord
        bytesPerBuffer = int(bytesPerRecord * recordsPerBuffer*channel_number)

        bufferCount = 4
        buffers = []
        for i in range(bufferCount):
            buffers.append(DMABuffer(bytesPerSample, bytesPerBuffer))
        # Set the record size
        self._dll.SetRecordSize(board, 0, samplesPerRecord)

        # Configure the number of records in the acquisition
        acquisition_timeout_sec = 10
        self._dll.SetRecordCount(board, recordsPerCapture)

        # Calculate the number of buffers in the acquisition
        buffersPerAcquisition = math.ceil(recordsPerCapture / recordsPerBuffer)

        self._dll.BeforeAsyncRead(board, 3,  # Channels A & B
                                  0,
                                  samplesPerRecord,
                                  int(recordsPerBuffer),
                                  recordsPerCapture,
                                  self._dll.ADMA_EXTERNAL_STARTCAPTURE |
                                  self._dll.ADMA_NPT)()

        # Post DMA buffers to board
        for buffer in buffers:
            self._dll.PostAsyncBuffer(board, buffer.addr, buffer.size_bytes)

        start = time.clock()  # Keep track of when acquisition started
        self._dll.StartCapture(board)  # Start the acquisition

        if time.clock() - start > acquisition_timeout_sec:
            self._dll.AbortCapture()
            raise Exception("Error: Capture timeout. Verify trigger")
            time.sleep(10e-3)

        # Preparation of the tables for the traces

        dataA = np.empty((recordsPerCapture, samplesPerRecord))
        dataB = np.empty((recordsPerCapture, samplesPerRecord))

        buffersCompleted = 0
        while buffersCompleted < buffersPerAcquisition:
            # Wait for the buffer at the head of the list of available
            # buffers to be filled by the board.
            buffer = buffers[buffersCompleted % len(buffers)]
            self._dll.WaitAsyncBufferComplete(board, buffer.addr, 500)

            data = np.reshape(buffer.buffer, (recordsPerBuffer*channel_number, -1))
            dataA[buffersCompleted*recordsPerBuffer:(buffersCompleted+1)*recordsPerBuffer] = data[:recordsPerBuffer]
            dataB[buffersCompleted*recordsPerBuffer:(buffersCompleted+1)*recordsPerBuffer] = data[recordsPerBuffer:]
            buffersCompleted += 1

            self._dll.PostAsyncBuffer(board, buffer.addr, buffer.size_bytes)

        self._dll.AbortAsyncRead(board)

        for buffer in buffers:
            buffer.__exit__()

        # Re-shaping of the data for demodulation and demodulation
        dataA = dataA[:,1:samplesPerTrace + 1]
        dataB = dataB[:,1:samplesPerTrace + 1]

        # Averaging if needed and converting binary numbers into Volts
        if average:
            dataA = np.mean(dataA, axis=0)
            dataB = np.mean(dataB, axis=0)

        dataA = (dataA-2**15)/65535*0.8+0.000459610322728
        dataB = (dataB-2**15)/65535*0.8+0.00154325074388

        return (dataA, dataB)


DRIVERS = {'Alazar935x': Alazar935x}
