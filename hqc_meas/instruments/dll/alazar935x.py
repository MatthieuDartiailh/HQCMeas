# -*- coding: utf-8 -*-
#==============================================================================
# module : alazar935x.py
# author : Benjamin Huard & Nathanael Cottet
# license : MIT license
#==============================================================================
"""

This module defines drivers for Alazar using DLL Library.

:Contains:
    Alazar9351

To read well the Dll of the Alazar9351, Visual C++ Studio is needed.

"""
from ..driver_tools import (InstrIOError, secure_communication,
                            instrument_property)
from ..dll_tools import DllInstrument
from inspect import cleandoc
import time
import numpy as np
import math
from pyclibrary import CLibrary
from ctypes import *
import os



class Stats_to_VB(object):
    
    __slots__ = ('tableA', 'tableB', 'record_nb')        
    

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

        cSampleType = c_uint8
        npSampleType = np.uint8
        if bytes_per_sample > 1:
            cSampleType = c_uint16
            npSampleType = np.uint16

        self.addr = None
        if os.name == 'nt':
            MEM_COMMIT = 0x1000
            PAGE_READWRITE = 0x4
            windll.kernel32.VirtualAlloc.argtypes = [c_void_p, c_long, c_long, c_long]
            windll.kernel32.VirtualAlloc.restype = c_void_p
            self.addr = windll.kernel32.VirtualAlloc(
                0, c_long(size_bytes), MEM_COMMIT, PAGE_READWRITE)
        elif os.name == 'posix':
            libc.valloc.argtypes = [c_long]
            libc.valloc.restype = c_void_p
            self.addr = libc.valloc(size_bytes)
            print("Allocated data : " + str(self.addr))
        else:
            raise Exception("Unsupported OS")


        ctypes_array = (cSampleType * (size_bytes // bytes_per_sample)).from_address(self.addr)
        self.buffer = np.frombuffer(ctypes_array, dtype=npSampleType)
        pointer, read_only_flag = self.buffer.__array_interface__['data']

    def __exit__(self):
        if os.name == 'nt':
            MEM_RELEASE = 0x8000
            windll.kernel32.VirtualFree.argtypes = [c_void_p, c_long, c_long]
            windll.kernel32.VirtualFree.restype = c_int
            windll.kernel32.VirtualFree(c_void_p(self.addr), 0, MEM_RELEASE);
        elif os.name == 'posix':
            libc.free(self.addr)
        else:
            raise Exception("Unsupported OS")



class Alazar935x(DllInstrument):

    library = 'ATSApi.dll'

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(Alazar935x, self).__init__(connection_info, caching_allowed,
                                         caching_permissions, auto_open)

        cache_path = unicode(os.path.join(os.path.dirname(__file__), 
                                          'cache/Alazar.pyclibc'))
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
        
        board = self._dll.GetBoardBySystemID(self.instr_id)()
#       board = self._dll.GetBoardBySystemID(1,1)()
        
        # TODO: Select clock parameters as required to generate this
        # sample rate
        global samplesPerSec
        samplesPerSec = 500000000.0
        self._dll.SetCaptureClock(board,
                                  self._dll.EXTERNAL_CLOCK_10MHz_REF,
                                  self._dll.SAMPLE_RATE_500MSPS,
                                  self._dll.CLOCK_EDGE_RISING,
                                  0)
        
        # TODO: Select channel A input parameters as required.
        self._dll.InputControl(board,
                           self._dll.CHANNEL_A,
                           self._dll.AC_COUPLING,
                           self._dll.INPUT_RANGE_PM_400_MV,
                           self._dll.IMPEDANCE_50_OHM)
        
        # TODO: Select channel A bandwidth limit as required.
        self._dll.SetBWLimit(board, self._dll.CHANNEL_A, 0)
        
        
        # TODO: Select channel B input parameters as required.
        self._dll.InputControl(board, self._dll.CHANNEL_B,
                           self._dll.AC_COUPLING,
                           self._dll.INPUT_RANGE_PM_400_MV,
                           self._dll.IMPEDANCE_50_OHM)
        
        # TODO: Select channel B bandwidth limit as required.
        self._dll.SetBWLimit(board, self._dll.CHANNEL_B, 0)
        
        # TODO: Select trigger inputs and levels as required.
        self._dll.SetTriggerOperation(board, self._dll.TRIG_ENGINE_OP_J,
                                  self._dll.TRIG_ENGINE_J,
                                  self._dll.TRIG_EXTERNAL,
                                  self._dll.TRIGGER_SLOPE_POSITIVE,
                                  141,
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
        self._dll.SetTriggerDelay(triggerDelay_samples)
    
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
        triggerTimeout_sec = 0.
        triggerTimeout_clocks = int(triggerTimeout_sec / 0.00001 + 0.5)
        self._dll.SetTriggerTimeOut(triggerTimeout_clocks)
    
        # Configure AUX I/O connector as required
        self._dll.ConfigureAuxIO(self._dll.AUX_OUT_TRIGGER,
                             0)
                             
            
    def get_demod(self, preTriggerSamples, postTriggerSamples, 
                  recordsPerCapture, acquisition_timeout_sec,freq):

#Turning on the LED of the card at the beginning of the acquisition
        self._dll.SetLED(board,1)                  
# TODO: Select the active channels -> SHOULD BE DONE BY THE USER IN 
  #THE INTERFACE ?
#        channels = self._dll.CHANNEL_A | self._dll.CHANNEL_B
#        channelCount = 0
#        for c in self._dll.channels:
#            channelCount += (c & channels == c)
        self._dll.SetParameter(board,
                                  0,
                                  self._dll.SET_SINGLE_CHANNEL_MODE,
                                  self._dll.CHANNEL_A
                                  )                  
        channels = self._dll.CHANNEL_A
        channelCount = 1
            
        
        answer = Stats_to_VB()
        
        retCode, (maxSamplesPerChannel, 
              bitsPerSample) = self._dll.GetChannelInfo(board)
        if retCode != self._dll.ApiSuccess:
            raise ValueError(cleandoc(self._dll.AlazarErrorToText(retCode)))
        
        return answer
        
# Compute the number of bytes per record and per buffer
        ret,(boardhandle,memorySize_samples, 
             bitsPerSample) = self._dll.GetChannelInfo(board)
        bytesPerSample = (bitsPerSample.value + 7) // 8
        samplesPerRecord = preTriggerSamples + postTriggerSamples
        bytesPerRecord = bytesPerSample * samplesPerRecord
                
# Calculate the size of a record buffer in bytes. Note that the
# buffer must be at least 16 bytes larger than the transfer size.
        bytesPerBuffer = bytesPerSample * (samplesPerRecord + 16)
        
# Set the record size
        self._dll.SetRecordSize(board, preTriggerSamples, postTriggerSamples)
        
# Configure the number of records in the acquisition
        self._dll.SetRecordCount(board, recordsPerCapture)

        start = time.clock() # Keep track of when acquisition started
        self._dll.StartCapture(board) # Start the acquisition
        bytesTransferred = 0
        if time.clock() - start > acquisition_timeout_sec:
            self._dll.AbortCapture()
            raise Exception("Error: Capture timeout. Verify trigger")
            time.sleep(10e-3)
            
# How to allow the user to cancel the process?

# Preparation of the tables for the demodulation        
        currenttry = 1;
        while currenttry*1000/(2*freq)<samplesPerRecord:
            if (currenttry*1000)%(2 * freq) != 0:
                currenttry += 1;
            
        tablelength =  currenttry * 1000 / (2*freq)

        dem = np.arange(tablelength)
        coses = math.Cos(4 * math.pi * dem * freq * 0.001)
        sines = math.Sin(4 * math.pi * dem * freq * 0.001)

        dataA=np.zeros((recordsPerCapture,samplesPerRecord))
        dataB=np.zeros((recordsPerCapture,samplesPerRecord))
        
        buffer = DMABuffer(bytesPerSample, bytesPerBuffer)
        # Transfer the records from on-board memory to our buffer
        chans = 'AB'  
        # possible chans are A, B, AB
        for record in range(recordsPerCapture):
            if chans == 'A':
                self._dll.Read(board,
                           1,             # Channel identifier
                           buffer.addr,           # Memory address of buffer
                           bytesPerSample,        # Bytes per sample
                           record + 1,            # Record (1-indexed)
                           preTriggerSamples,     # Pre-trigger samples
                           samplesPerRecord)      # Samples per record
                bytesTransferred += bytesPerRecord;
                dataA[record]=buffer.buffer[:samplesPerRecord]
            elif chans == 'B':
                self._dll.Read(board,
                           2,             # Channel identifier
                           buffer.addr,           # Memory address of buffer
                           bytesPerSample,        # Bytes per sample
                           record + 1,            # Record (1-indexed)
                           preTriggerSamples,     # Pre-trigger samples
                           samplesPerRecord)      # Samples per record
                bytesTransferred += bytesPerRecord;
                dataB[record]=buffer.buffer[:samplesPerRecord]
            else:
                self._dll.Read(board,
                           1,             # Channel identifier
                           buffer.addr,           # Memory address of buffer
                           bytesPerSample,        # Bytes per sample
                           record + 1,            # Record (1-indexed)
                           preTriggerSamples,     # Pre-trigger samples
                           samplesPerRecord)      # Samples per record
                bytesTransferred += bytesPerRecord;
                dataA[record]=buffer.buffer[:samplesPerRecord]
                            
                self._dll.Read(board,
                           2,             # Channel identifier
                           buffer.addr,           # Memory address of buffer
                           bytesPerSample,        # Bytes per sample
                           record + 1,            # Record (1-indexed)
                           preTriggerSamples,     # Pre-trigger samples
                           samplesPerRecord)      # Samples per record
                bytesTransferred += bytesPerRecord;
                dataB[record]=buffer.buffer[:samplesPerRecord]
                
            # Records are arranged in the buffer as follows:
            # R0A, R1A, R2A ... RnA, R0B, R1B, R2B ...
            #
            # A 12-bit sample code is stored in the most significant bits of
            # in each 16-bit sample value.
            #
            # Sample codes are unsigned by default. As a result:
            # - a sample code of 0x0000 represents a negative full scale input 
            # signal.
            # - a sample code of 0x8000 represents a ~0V signal.
            # - a sample code of 0xFFFF represents a positive full scale input 
            # signal.


            
            #Converting binary numbers into Volts 
        dataA=(dataA-2**15)/65535*0.8+0.000459610322728
        dataB=(dataB-2**15)/65535*0.8+0.00154325074388
        
        answer.averageAI = np.mean(dataA*coses)
        answer.averageAQ = np.mean(dataA*sines)
        answer.averageBI = np.mean(dataB*coses)
        answer.averageBQ = np.mean(dataA*sines)

            #Turning off the LED of the card when the acquisition is done
        self._dll.SetLED(board,0)   

DRIVERS = {'Alazar935x': Alazar935x}
