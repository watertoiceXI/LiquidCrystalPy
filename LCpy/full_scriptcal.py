import numpy as np
from matplotlib import pyplot as plt

from QuickCapture import * 
from AnalogDiscovery import *
import time
import os
import scipy.io as sio

#### Parameters
collect_name = "trial"
output_fold = r"A:\Crystal\new_new\V_1_2_lowdope\cal"
if not os.path.exists(output_fold):
	os.mkdir(output_fold)
num_collects = 1;
collect_time = 20; #in seconds
desired_framerate = 3;
out_freq=50;

acq_samp_Hz = 10e3;

out_amp = 1.2; #for now, this has a gain of 22, and a limit of 40V.
out_wv = 1;

#### Derived Parameters
####  (Don't change)
framerate = 30;
framerate_ds = int(framerate/desired_framerate);
num_frames = collect_time*framerate;
acq_n_samp = collect_time*acq_samp_Hz;

#### Setup
cam = Quick_capture.blackfly_camera();

ad = AD_2.Analog_Discovery(acq_n_samp=acq_n_samp,out_amp=out_amp,out_freq=out_freq);

for collect in range(num_collects):
	print(f"Taking data for collect {collect}");
	#ad.output_off();
	#ad.output_setup(waveform=out_wv,out_freq=out_freq,out_amp=out_amp)
	time.sleep(2.0)
	start_time = time.time()+1;
	cam.start_time = start_time;
	ad.start_time = start_time;
	im_holder = cam.acquire_images(num_frames=num_frames)
	dat_holder = ad.take_data();
	while not im_holder.done() and not dat_holder.done():
		time.sleep(1);
	print("  Done. Saving data out.")
	timestamp = time.strftime('%m_%d_%H_%M',time.localtime());
	data_name = collect_name+timestamp;
	images, images_t = im_holder.result();
	power_data = dat_holder.result();
	images = images[0::framerate_ds]
	images_t = images_t[0::framerate_ds]
	outdic = {};
	outdic['images']=images
	outdic['images_t']=images_t
	outdic['power_data']=power_data
	outdic['power_start_time']=ad.input_start_time
	outdic['out_freq']=out_freq
	outdic['out_wv']=out_wv
	outdic['acq_samp_Hz']=acq_samp_Hz
	outdic['out_amp']=out_amp
	outdic['collect_time']=collect_time
	sio.savemat(os.path.join(output_fold,data_name+'.mat'),outdic);
	del outdic
	del images
	del dat_holder
	del im_holder
	