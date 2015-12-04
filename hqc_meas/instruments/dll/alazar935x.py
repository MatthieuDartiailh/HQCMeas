# -*- coding: utf-8 -*-
# =============================================================================
# module : alazar935x.py
# author : Benjamin Huard & Nathanael Cottet & Sébastien Jezouin
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
        trigLevel = 0.3 # in Volts
        trigRange = 2.5 # in Volts (Set in SetExternalTrigger() below)
        trigCode = int(128 + 127 * trigLevel / trigRange)
        self._dll.SetTriggerOperation(board, self._dll.TRIG_ENGINE_OP_J,
                                      self._dll.TRIG_ENGINE_J,
                                      self._dll.TRIG_EXTERNAL,
                                      self._dll.TRIGGER_SLOPE_POSITIVE,
                                      trigCode,
                                      self._dll.TRIG_ENGINE_K,
                                      self._dll.TRIG_DISABLE,
                                      self._dll.TRIGGER_SLOPE_POSITIVE,
                                      128)

        # TODO: Select external trigger parameters as required.
        self._dll.SetExternalTrigger(board, self._dll.DC_COUPLING,
                                     self._dll.ETR_2V5)

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
        self._dll.SetTriggerTimeOut(board, 0)
        # Configure AUX I/O connector as required
        self._dll.ConfigureAuxIO(board, self._dll.AUX_OUT_TRIGGER,
                                 0)

    def get_demod(self, startaftertrig, duration, recordsPerCapture,
                  recordsPerBuffer, freq, average, NdemodA, NdemodB, NtraceA, NtraceB):
                      
        board = self._dll.GetBoardBySystemID(1, 1)()

        # Number of samples per record: must be divisible by 32
        samplesPerSec = 500000000.0
        samplesPerTrace = int(samplesPerSec * np.max(np.array(startaftertrig) + np.array(duration)))
        if samplesPerTrace % 32 == 0:
            samplesPerRecord = int(samplesPerTrace)
        else:
            samplesPerRecord = int((samplesPerTrace)/32 + 1)*32
            
        retCode = self._dll.GetChannelInfo(board)()
        bitsPerSample = self._dll.GetChannelInfo(board)[1]
        if retCode != self._dll.ApiSuccess:
            raise ValueError(cleandoc(self._dll.AlazarErrorToText(retCode)))

        # Compute the number of bytes per record and per buffer
        channel_number = 2 if ((NdemodA or NtraceA) and (NdemodB or NtraceB)) else 1  # Acquisition on A and B
        ret, (boardhandle, memorySize_samples,
              bitsPerSample) = self._dll.GetChannelInfo(board)
        bytesPerSample = (bitsPerSample + 7) // 8
        bytesPerRecord = bytesPerSample * samplesPerRecord
        bytesPerBuffer = int(bytesPerRecord * recordsPerBuffer*channel_number)
        
        # For converting data into volts
        channelRange = 0.4 # Volts
        bitsPerSample = 12
        bitShift = 4
        code = (1 << (bitsPerSample - 1)) - 0.5

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
        buffersPerAcquisition = round(recordsPerCapture / recordsPerBuffer)

        channelSelect = 1 if not (NdemodB or NtraceB) else (2 if not (NdemodA or NtraceA) else 3)
        self._dll.BeforeAsyncRead(board, channelSelect,  # Channels A & B
                                  0,
                                  samplesPerRecord,
                                  int(recordsPerBuffer),
                                  recordsPerCapture,
                                  self._dll.ADMA_EXTERNAL_STARTCAPTURE |
                                  self._dll.ADMA_NPT)()

        # Post DMA buffers to board. ATTENTION it is very important not to do "for buffer in buffers"
        for i in range(bufferCount):
            buffer = buffers[i]
            self._dll.PostAsyncBuffer(board, buffer.addr, buffer.size_bytes)

        start = time.clock()  # Keep track of when acquisition started
        self._dll.StartCapture(board)  # Start the acquisition

        if time.clock() - start > acquisition_timeout_sec:
            self._dll.AbortCapture()
            raise Exception("Error: Capture timeout. Verify trigger")
            time.sleep(10e-3)
            
        # Preparation of the tables for the demodulation
            
        startSample = []
        samplesPerDemod = []
        samplesPerBlock = []
        NumberOfBlocks = []
        samplesMissing = []
        data = []
        dataExtended = []
        
        for i in range(NdemodA + NdemodB):
            startSample.append( int(samplesPerSec * startaftertrig[i]) )
            samplesPerDemod.append( int(samplesPerSec * duration[i]) )
            # Check wheter it is possible to cut each record in blocks of size equal
            # to an integer number of periods
            periodsPerBlock = 1
            while (periodsPerBlock * samplesPerSec < freq[i] * samplesPerDemod[i] 
                   and periodsPerBlock * samplesPerSec % freq[i]):
                periodsPerBlock += 1
                
            samplesPerBlock.append( int(np.minimum(periodsPerBlock * samplesPerSec / freq[i],
                                                  samplesPerDemod[i])) )
            NumberOfBlocks.append( np.divide(samplesPerDemod[i], samplesPerBlock[i]) )
            samplesMissing.append( (-samplesPerDemod[i]) % samplesPerBlock[i] ) 
            # Makes the table that will contain the data
            data.append( np.empty((recordsPerCapture, samplesPerBlock[i])) )
            dataExtended.append( np.zeros((recordsPerBuffer, samplesPerDemod[i] + samplesMissing[i]),
                                          dtype='uint16') )
                                        
        for i in (np.arange(NtraceA + NtraceB) + NdemodA + NdemodB):
            startSample.append( int(samplesPerSec * startaftertrig[i]) )
            samplesPerDemod.append( int(samplesPerSec * duration[i]) )
            data.append( np.empty((recordsPerCapture, samplesPerDemod[i])) )

        start = time.clock()

        buffersCompleted = 0
        while buffersCompleted < buffersPerAcquisition:

            # Wait for the buffer at the head of the list of available
            # buffers to be filled by the board.
            buffer = buffers[buffersCompleted % len(buffers)]
            self._dll.WaitAsyncBufferComplete(board, buffer.addr, 10000)

            # Process data

            dataRaw = np.reshape(buffer.buffer, (recordsPerBuffer*channel_number, -1))
            dataRaw = dataRaw >> bitShift

            for i in np.arange(NdemodA):
                dataExtended[i][:,:samplesPerDemod[i]] = dataRaw[:recordsPerBuffer,startSample[i]:startSample[i]+samplesPerDemod[i]]
                dataBlock = np.reshape(dataExtended[i],(recordsPerBuffer,-1,samplesPerBlock[i]))
                data[i][buffersCompleted*recordsPerBuffer:(buffersCompleted+1)*recordsPerBuffer] = np.sum(dataBlock, axis=1)

            for i in (np.arange(NdemodB) + NdemodA):
                dataExtended[i][:,:samplesPerDemod[i]] = dataRaw[(channel_number-1)*recordsPerBuffer:channel_number*recordsPerBuffer,startSample[i]:startSample[i]+samplesPerDemod[i]]
                dataBlock = np.reshape(dataExtended[i],(recordsPerBuffer,-1,samplesPerBlock[i]))
                data[i][buffersCompleted*recordsPerBuffer:(buffersCompleted+1)*recordsPerBuffer] = np.sum(dataBlock, axis=1)
             
            for i in (np.arange(NtraceA) + NdemodB + NdemodA):
                data[i][buffersCompleted*recordsPerBuffer:(buffersCompleted+1)*recordsPerBuffer] = dataRaw[:recordsPerBuffer,startSample[i]:startSample[i]+samplesPerDemod[i]]
            
            for i in (np.arange(NtraceB) + NtraceA + NdemodB + NdemodA):
                data[i][buffersCompleted*recordsPerBuffer:(buffersCompleted+1)*recordsPerBuffer] = dataRaw[(channel_number-1)*recordsPerBuffer:channel_number*recordsPerBuffer,startSample[i]:startSample[i]+samplesPerDemod[i]]
             
            buffersCompleted += 1

            self._dll.PostAsyncBuffer(board, buffer.addr, buffer.size_bytes)

        self._dll.AbortAsyncRead(board)

        for i in range(bufferCount):
            buffer = buffers[i]
            buffer.__exit__()
  
        # Normalize the np.sum and convert data into Volts  
        for i in range(NdemodA + NdemodB):
            normalisation = 1 if samplesMissing[i] else 0
            data[i][:,:samplesPerBlock[i]-samplesMissing[i]] /= NumberOfBlocks[i] + normalisation
            data[i][:,samplesPerBlock[i]-samplesMissing[i]:] /= NumberOfBlocks[i]
            data[i] = (data[i] / code - 1) * channelRange
        for i in (np.arange(NtraceA + NtraceB) + NdemodA + NdemodB):
            data[i] = (data[i] / code - 1) * channelRange

        # calculate demodulation tables
        if NdemodA:               
            demA = np.arange(max(samplesPerBlock[:NdemodA]))
            cosesA = np.cos(2. * math.pi * demA * freq[0] / samplesPerSec)
            sinesA = np.sin(2. * math.pi * demA * freq[0] / samplesPerSec)
        if NdemodB:
            demB = np.arange(max(samplesPerBlock[NdemodA:]))
            cosesB = np.cos(2. * math.pi * demB * freq[-1] / samplesPerSec)
            sinesB = np.sin(2. * math.pi * demB * freq[-1] / samplesPerSec)

        # prepare the structure of the answered array

        if (NdemodA or NdemodB):
            answerTypeDemod = []
            for i in range(NdemodA):
                answerTypeDemod += [('AI' + str(i), str(data[0].dtype)), ('AQ' + str(i), str(data[0].dtype))]
            for i in range(NdemodB):
                answerTypeDemod += [('BI' + str(i), str(data[0].dtype)), ('BQ' + str(i), str(data[0].dtype))]  
        else:
            answerTypeDemod = 'f'
        
        if (NtraceA or NtraceB):
            answerTypeTrace = ( [('A' + str(i), str(data[0].dtype)) for i in range(NtraceA)]
                              + [('B' + str(i), str(data[0].dtype)) for i in range(NtraceB)] )
            biggerTrace = np.max(samplesPerDemod[NdemodA+NdemodB:])
        else:
            answerTypeTrace = 'f'
            biggerTrace = 0

        if average:
            answerDemod = np.empty(1, dtype=answerTypeDemod)
            answerTrace = np.zeros(biggerTrace, dtype=answerTypeTrace)
        else:
            answerDemod = np.empty(recordsPerCapture, dtype=answerTypeDemod)
            answerTrace = np.zeros((recordsPerCapture, biggerTrace), dtype=answerTypeTrace)

        meanAxis = 0 if average else 1

        # Demodulate the data, average them if asked and return the result

        for i in np.arange(NdemodA):
            if average:
                data[i] = np.mean(data[i], axis=0)     
            ansI = 2*np.mean(data[i]*cosesA[:samplesPerBlock[i]], axis=meanAxis)
            ansQ = 2*np.mean(data[i]*sinesA[:samplesPerBlock[i]], axis=meanAxis)
            answerDemod['AI' + str(i)] = ( + ansI * np.cos(2 * np.pi * freq[0] * startSample[i]/samplesPerSec)
                                      - ansQ * np.sin(2 * np.pi * freq[0] * startSample[i]/samplesPerSec) )
            answerDemod['AQ' + str(i)] = ( + ansI * np.sin(2 * np.pi * freq[0] * startSample[i]/samplesPerSec)
                                      + ansQ * np.cos(2 * np.pi * freq[0] * startSample[i]/samplesPerSec) )
                
        for i in (np.arange(NdemodB) + NdemodA):
            if average:
                data[i] = np.mean(data[i], axis=0)
            ansI = 2*np.mean(data[i]*cosesB[:samplesPerBlock[i]], axis=meanAxis)
            ansQ = 2*np.mean(data[i]*sinesB[:samplesPerBlock[i]], axis=meanAxis)
            answerDemod['BI' + str(i-NdemodA)] = ( + ansI * np.cos(2 * np.pi * freq[-1] * startSample[i]/samplesPerSec)
                                              - ansQ * np.sin(2 * np.pi * freq[-1] * startSample[i]/samplesPerSec) )
            answerDemod['BQ' + str(i-NdemodA)] = ( + ansI * np.sin(2 * np.pi * freq[-1] * startSample[i]/samplesPerSec)
                                              + ansQ * np.cos(2 * np.pi * freq[-1] * startSample[i]/samplesPerSec) )
        
        for i in (np.arange(NtraceA) + NdemodB + NdemodA):
            if average:
                answerTrace['A' + str(i-NdemodA-NdemodB)][:samplesPerDemod[i]] = np.mean(data[i], axis=0)
            else:
                answerTrace['A' + str(i-NdemodA-NdemodB)][:,:samplesPerDemod[i]] = data[i]
             
        for i in (np.arange(NtraceB) + NtraceA + NdemodB + NdemodA):
            if average:
                answerTrace['B' + str(i-NdemodA-NdemodB-NtraceA)][:samplesPerDemod[i]] = np.mean(data[i], axis=0)
            else:
                answerTrace['B' + str(i-NdemodA-NdemodB-NtraceA)][:,:samplesPerDemod[i]] = data[i]
            
        print time.clock() - start

        return answerDemod, answerTrace

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
