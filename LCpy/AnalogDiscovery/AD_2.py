#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision: 10/17/2013
   Requires:                       
       Python 2.7, 3.3 or later
       numpy, matplotlib
"""

import dwf
import time
import matplotlib.pyplot as plt
import numpy as np
from LCpy.ez_thread import threaded

class Analog_Discovery:
	def __init__(self,verbose=False,acq_samp_Hz=10e3,acq_n_samp=1000,
	waveform=1,out_freq=50,out_amp=1.0,acq_range=15.0):
		self.verbose = verbose;
		if self.verbose: print("DWF Version: " + dwf.FDwfGetVersion())
		#open device
		if self.verbose: print("Opening device")
		self.start_time = 0;
		self.input_start_time = None;
		self.dwf_ao = dwf.DwfAnalogOut()
		self.output_setup(waveform=waveform,out_freq=out_freq,out_amp=out_amp)
		self.dwf_ai = dwf.DwfAnalogIn(self.dwf_ao)
		self.input_setup(acq_samp_Hz=acq_samp_Hz,acq_n_samp=acq_n_samp,acq_range=acq_range)
		
	def output_off(self):
		self.dwf_ao.nodeEnableSet(0, self.dwf_ao.NODE.CARRIER, False)
		self.dwf_ao.configure(0, False)
		return 

	
	def output_setup(self,waveform=None,out_freq=None,out_amp=None):
		"""
		If something isn't called, it's left at a default value. 
		Waveform options are:
			DC: 0
			SINE: 1
			SQUARE: 2
			TRIANGLE: 3
			RAMP_UP: 4
			RAMP_DOWN: 5
			NOISE: 6
			CUSTOM: 30
			PLAY: 31
		"""
		if self.verbose: print("Setting up the output...")
		if not waveform is None: self.waveform = waveform;
		if not out_freq is None: self.out_freq = out_freq;
		if not out_amp is None: self.out_amp = out_amp;
		
		self.dwf_ao.nodeEnableSet(0, self.dwf_ao.NODE.CARRIER, True)
		self.dwf_ao.nodeFunctionSet(0, self.dwf_ao.NODE.CARRIER, self.waveform)
		self.dwf_ao.nodeFrequencySet(0, self.dwf_ao.NODE.CARRIER, self.out_freq)
		self.dwf_ao.nodeAmplitudeSet(0, self.dwf_ao.NODE.CARRIER, self.out_amp)
		self.dwf_ao.configure(0, True)
		self.output_start_time = time.time();
		return 
		
	def input_setup(self,acq_samp_Hz=None,acq_n_samp=None,acq_range=None):
		#set up acquisition
		if self.verbose: print("Setting up the input...")
		if not acq_samp_Hz is None: self.acq_samp_Hz = acq_samp_Hz;
		if not acq_n_samp is None: self.acq_n_samp = acq_n_samp;
		if not acq_range is None: self.acq_range = acq_range;
		
		self.dwf_ai.channelEnableSet(0, True)
		self.dwf_ai.channelRangeSet(0, self.acq_range)
		self.dwf_ai.channelEnableSet(1, True)
		self.dwf_ai.channelRangeSet(1, self.acq_range)
		self.dwf_ai.acquisitionModeSet(self.dwf_ai.ACQMODE.RECORD)
		self.dwf_ai.frequencySet(self.acq_samp_Hz)
		self.dwf_ai.recordLengthSet(self.acq_n_samp / self.acq_samp_Hz)
		return
	
	@threaded
	def take_data(self):
		
		#wait at least 2 seconds for the offset to stabilize
		if (time.time()-self.output_start_time)<2:
			time.sleep(2+(time.time()-self.output_start_time))
		#wait for start time
		while time.time()<self.start_time:
			time.sleep(0.001);
		#begin acquisition
		self.dwf_ai.configure(False, True)
		self.input_start_time = time.time();
		if self.verbose: print("   taking analog data")
		rgdSamples1 = []
		rgdSamples2 = []
		cSamples = 0
		fLost = False
		fCorrupted = False
		while cSamples < self.acq_n_samp:
			sts = self.dwf_ai.status(True)
			if cSamples == 0 and sts in (self.dwf_ai.STATE.CONFIG,
										 self.dwf_ai.STATE.PREFILL,
										 self.dwf_ai.STATE.ARMED):
				# Acquisition not yet started.
				continue

			cAvailable, cLost, cCorrupted = self.dwf_ai.statusRecord()
			cSamples += cLost
				
			if cLost > 0:
				fLost = True
			if cCorrupted > 0:
				fCorrupted = True
			if cAvailable == 0:
				continue
			if cSamples + cAvailable > self.acq_n_samp:
				cAvailable = self.acq_n_samp - cSamples
			
			# get samples
			rgdSamples1.extend(self.dwf_ai.statusData(0, cAvailable))
			rgdSamples2.extend(self.dwf_ai.statusData(1, cAvailable))
			cSamples += cAvailable

		if self.verbose: print("Recording finished")
		if fLost:
			print("Samples were lost! Reduce frequency")
		if cCorrupted:
			print("Samples could be corrupted! Reduce frequency")

		#with open("record.csv", "w") as f:
		#	for v in rgdSamples:
		#		f.write("%s\n" % v)
		if self.verbose: 
			plt.plot(rgdSamples1)
			plt.plot(rgdSamples2)
			plt.show()
		return np.stack([np.array(rgdSamples1),np.array(rgdSamples2)])

class Analog_Discovery_Sweep:
	def __init__(self,verbose=False,acq_samp_Hz=10e3,acq_n_samp=10000,
	waveform=1,out_freq=50,out_amp=1.0,acq_range=15.0,mod_freq=0.05):
		self.verbose = verbose;
		if self.verbose: print("DWF Version: " + dwf.FDwfGetVersion())
		#open device
		if self.verbose: print("Opening device")
		self.start_time = 0;
		self.input_start_time = None;
		self.dwf_ao = dwf.DwfAnalogOut()
		self.output_setup(waveform=waveform,out_freq=out_freq,out_amp=out_amp,mod_freq=mod_freq)
		self.dwf_ai = dwf.DwfAnalogIn(self.dwf_ao)
		self.input_setup(acq_samp_Hz=acq_samp_Hz,acq_n_samp=acq_n_samp,acq_range=acq_range)
		
	def output_off(self):
		self.dwf_ao.nodeEnableSet(0, self.dwf_ao.NODE.CARRIER, False)
		self.dwf_ao.configure(0, False)
		return 

	
	def output_setup(self,waveform=None,out_freq=None,out_amp=None,mod_freq=None):
		"""
		If something isn't called, it's left at a default value. 
		Waveform options are:
			DC: 0
			SINE: 1
			SQUARE: 2
			TRIANGLE: 3
			RAMP_UP: 4
			RAMP_DOWN: 5
			NOISE: 6
			CUSTOM: 30
			PLAY: 31
		"""
		if self.verbose: print("Setting up the output...")
		if not waveform is None: self.waveform = waveform;
		if not out_freq is None: self.out_freq = out_freq;
		if not out_amp is None: self.out_amp = out_amp;
		if not mod_freq is None: self.mod_freq = mod_freq;
		
		self.dwf_ao.nodeEnableSet(0, self.dwf_ao.NODE.CARRIER, True)
		self.dwf_ao.nodeFrequencySet(0, self.dwf_ao.NODE.CARRIER, self.out_freq)
		self.dwf_ao.nodeAmplitudeSet(0, self.dwf_ao.NODE.CARRIER, self.out_amp)
		self.dwf_ao.nodeEnableSet(0, self.dwf_ao.NODE.CARRIER, True)
		self.dwf_ao.nodeFunctionSet(0, self.dwf_ao.NODE.CARRIER, self.waveform)
		self.dwf_ao.nodeFrequencySet(0, self.dwf_ao.NODE.CARRIER, self.out_freq)
		self.dwf_ao.nodeAmplitudeSet(0, self.dwf_ao.NODE.CARRIER, self.out_amp)
		self.dwf_ao.nodeOffsetSet(0, self.dwf_ao.NODE.CARRIER, 0)

		self.dwf_ao.nodeEnableSet(0, self.dwf_ao.NODE.AM, True)
		self.dwf_ao.nodeFunctionSet(0, self.dwf_ao.NODE.AM, 4)
		self.dwf_ao.nodeFrequencySet(0, self.dwf_ao.NODE.AM, mod_freq)
		self.dwf_ao.nodeAmplitudeSet(0, self.dwf_ao.NODE.AM, 100)
		self.dwf_ao.nodeOffsetSet(0, self.dwf_ao.NODE.AM, 0)
		self.dwf_ao.configure(0, True)




		self.output_start_time = time.time();
		return 
		
	def input_setup(self,acq_samp_Hz=None,acq_n_samp=None,acq_range=None):
		#set up acquisition
		if self.verbose: print("Setting up the input...")
		if not acq_samp_Hz is None: self.acq_samp_Hz = acq_samp_Hz;
		if not acq_n_samp is None: self.acq_n_samp = acq_n_samp;
		if not acq_range is None: self.acq_range = acq_range;
		
		self.dwf_ai.channelEnableSet(0, True)
		self.dwf_ai.channelRangeSet(0, self.acq_range)
		self.dwf_ai.channelEnableSet(1, True)
		self.dwf_ai.channelRangeSet(1, self.acq_range)
		self.dwf_ai.acquisitionModeSet(self.dwf_ai.ACQMODE.RECORD)
		self.dwf_ai.frequencySet(self.acq_samp_Hz)
		self.dwf_ai.recordLengthSet(self.acq_n_samp / self.acq_samp_Hz)
		return
	
	@threaded
	def take_data(self):
		
		#wait at least 2 seconds for the offset to stabilize
		if (time.time()-self.output_start_time)<2:
			time.sleep(2+(time.time()-self.output_start_time))
		#wait for start time
		while time.time()<self.start_time:
			time.sleep(0.001);
		#begin acquisition
		self.dwf_ai.configure(False, True)
		self.input_start_time = time.time();
		if self.verbose: print("   taking analog data")
		rgdSamples1 = []
		rgdSamples2 = []
		cSamples = 0
		fLost = False
		fCorrupted = False
		while cSamples < self.acq_n_samp:
			sts = self.dwf_ai.status(True)
			if cSamples == 0 and sts in (self.dwf_ai.STATE.CONFIG,
										 self.dwf_ai.STATE.PREFILL,
										 self.dwf_ai.STATE.ARMED):
				# Acquisition not yet started.
				continue

			cAvailable, cLost, cCorrupted = self.dwf_ai.statusRecord()
			cSamples += cLost
				
			if cLost > 0:
				fLost = True
			if cCorrupted > 0:
				fCorrupted = True
			if cAvailable == 0:
				continue
			if cSamples + cAvailable > self.acq_n_samp:
				cAvailable = self.acq_n_samp - cSamples
			
			# get samples
			rgdSamples1.extend(self.dwf_ai.statusData(0, cAvailable))
			rgdSamples2.extend(self.dwf_ai.statusData(1, cAvailable))
			cSamples += cAvailable

		if self.verbose: print("Recording finished")
		if fLost:
			print("Samples were lost! Reduce frequency")
		if cCorrupted:
			print("Samples could be corrupted! Reduce frequency")

		#with open("record.csv", "w") as f:
		#	for v in rgdSamples:
		#		f.write("%s\n" % v)
		if self.verbose: 
			plt.plot(rgdSamples1)
			plt.plot(rgdSamples2)
			plt.show()
		return np.stack([np.array(rgdSamples1),np.array(rgdSamples2)])

if __name__ == "__main__":
    ad = Analog_Discovery(verbose=False);
    dat_holder = ad.take_data();
    while not dat_holder.done():
        time.sleep(.1);
    print('Done, displaying')
    a = dat_holder.result()
    plt.figure()
    plt.plot(a[0])
    plt.plot(a[1])
    plt.show()

