# coding=utf-8
# =============================================================================
#  Copyright © 2017 FLIR Integrated Imaging Solutions, Inc. All Rights Reserved.
#
#  This software is the confidential and proprietary information of FLIR
#  Integrated Imaging Solutions, Inc. ("Confidential Information"). You
#  shall not disclose such Confidential Information and shall use it only in
#  accordance with the terms of the license agreement you entered into
#  with FLIR Integrated Imaging Solutions, Inc. (FLIR).
#
#  FLIR MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE SUITABILITY OF THE
#  SOFTWARE, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
#  PURPOSE, OR NON-INFRINGEMENT. FLIR SHALL NOT BE LIABLE FOR ANY DAMAGES
#  SUFFERED BY LICENSEE AS A RESULT OF USING, MODIFYING OR DISTRIBUTING
#  THIS SOFTWARE OR ITS DERIVATIVES.
# =============================================================================
#
# ImageFormatControl_QuickSpin.py shows how to apply custom image
# settings to the camera using the QuickSpin API. QuickSpin is a subset of
# the Spinnaker library that allows for simpler node access and control.
#
# This example demonstrates customizing offsets X and Y, width and height,
# and the pixel format. Ensuring custom values fall within an acceptable
# range is also touched on. Retrieving and setting node values using
# QuickSpin is the only portion of the example that differs from
# ImageFormatControl.
#
# A much wider range of topics is covered in the full Spinnaker examples than
# in the QuickSpin ones. There are only enough QuickSpin examples to
# demonstrate node access and to get started with the API; please see full
# Spinnaker examples for further or specific knowledge on a topic.

import PySpin
import numpy as np
import time

NUM_IMAGES = 10  # number of images to grab

from LCpy.ez_thread import threaded

class blackfly_camera:
	def __init__(self,verbose=False,cam_num=0,wh=None,offset=None,framerate=None):
		"""
		Example entry point; please see Enumeration_QuickSpin example for more
		in-depth comments on preparing and cleaning up the system.

		:return: True if successful, False otherwise.
		:rtype: bool
		"""
		result = True
		self.verbose = verbose;
		# TODO: input checks for below
		self.wh = wh;
		self.offset = offset;
		self.framerate = framerate;
		self.start_time = 0;
		# Retrieve singleton reference to system object
		self.system = PySpin.System.GetInstance()

		# Retrieve list of cameras from the system
		self.cam_list = self.system.GetCameras()
		
		num_cameras = self.cam_list.GetSize()
		if cam_num>num_cameras:
			print(f'Not enough cameras found! Attempted to use camera {cam_num}, only have {num_cameras}')
			return False

		if self.verbose: print(f'Number of cameras detected: {num_cameras}')
		if self.verbose: print('    Using camera number: %d' % cam_num)
		
		# Finish if there are no cameras
		if num_cameras == 0:
			# Clear camera list before releasing system
			self.cam_list.Clear()

			# Release system instance
			self.system.ReleaseInstance()

			print('No cameras found!')
			return False

		self.cam = self.cam_list[cam_num]
		
		try:
			# Initialize camera
			self.cam.Init()

			# Print device info
			if self.verbose: result = self.print_device_info()

			# Configure exposure
			if not self._configure_custom_image_settings():
				print('Failed to set camera parameters!')
				return False

		except PySpin.SpinnakerException as ex:
			print('Error: %s' % ex)
			return False
		if self.verbose: print('Ready for capture!')

	def __del__(self):
		# Release reference to camera
		# NOTE: Unlike the C++ examples, we cannot rely on pointer objects being automatically
		# cleaned up when going out of scope.
		# The usage of del is preferred to assigning the variable to None
					# Deinitialize camera
		
		self.cam.DeInit()
		del self.cam

		# Clear camera list before releasing system
		self.cam_list.Clear()

		# Release system instance
		self.system.ReleaseInstance()	

	def _configure_custom_image_settings(self):
		"""
		Configures a number of settings on the camera including offsets X and Y,
		width, height, and pixel format. These settings must be applied before
		BeginAcquisition() is called; otherwise, those nodes would be read only.
		Also, it is important to note that settings are applied immediately.
		This means if you plan to reduce the width and move the x offset accordingly,
		you need to apply such changes in the appropriate order.

		:param cam: Camera to configure settings on.
		:type cam: CameraPtr
		:return: True if successful, False otherwise.
		:rtype: bool
		"""
		if self.verbose: print('\n*** CONFIGURING CUSTOM IMAGE SETTINGS ***\n')

		result = True
		try:
			if self.wh is None:
				#wh = [cam.Width.GetMax(),cam.Height.GetMax()]
				self.wh = [640,480]
				if self.verbose: print('Default Width/Height')
			if self.offset is None:
				self.offset = [0,0];#[976, 732]
				#offset = [cam.OffsetX.GetMin(),cam.OffsetY.GetMin()]
			if not self.framerate is None:
				if self.verbose: print('Seeting framerate may fail! If it does, set through the SpinView program, then rerun.')
				self.cam.AcquisitionFrameRate.SetValue(self.framerate);
			# Apply mono 8 pixel format
			#
			# *** NOTES ***
			# In QuickSpin, enumeration nodes are as easy to set as other node
			# types. This is because enum values representing each entry node
			# are added to the API.
			if self.cam.PixelFormat.GetAccessMode() == PySpin.RW:
				self.cam.PixelFormat.SetValue(PySpin.PixelFormat_Mono8)
				if self.verbose: print('Pixel format set to %s...' % self.cam.PixelFormat.GetCurrentEntry().GetSymbolic())

			else:
				print('Pixel format not available...')
				result = False
				
			
			# Set maximum width
			#
			# *** NOTES ***
			# Other nodes, such as those corresponding to image width and height,
			# might have an increment other than 1. In these cases, it can be
			# important to check that the desired value is a multiple of the
			# increment.
			#
			# This is often the case for width and height nodes. However, because
			# these nodes are being set to their maximums, there is no real reason
			# to check against the increment.
			if self.cam.Width.GetAccessMode() == PySpin.RW and self.cam.Width.GetInc() != 0 and self.cam.Width.GetMax != 0:
				self.cam.Width.SetValue(self.wh[0])
				if self.verbose: print('Width set to %i...' % self.cam.Width.GetValue())

			else:
				print('Width not available...')
				result = False

			# Set maximum height
			#
			# *** NOTES ***
			# A maximum is retrieved with the method GetMax(). A node's minimum and
			# maximum should always be a multiple of its increment.
			if self.cam.Height.GetAccessMode() == PySpin.RW and self.cam.Height.GetInc() != 0 and self.cam.Height.GetMax != 0:
				self.cam.Height.SetValue(self.wh[1])
				if self.verbose: print('Height set to %i...' % self.cam.Height.GetValue())
			else:
				print('Height not available...')
				result = False
			
			# Apply minimum to offset X
			#
			# *** NOTES ***
			# Numeric nodes have both a minimum and maximum. A minimum is retrieved
			# with the method GetMin(). Sometimes it can be important to check
			# minimums to ensure that your desired value is within range.
			if self.cam.OffsetX.GetAccessMode() == PySpin.RW:
				self.cam.OffsetX.SetValue(self.offset[0])
				if self.verbose: print('Offset X set to %d...' % self.cam.OffsetX.GetValue())

			else:
				print('Offset X not available...')
				result = False

			# Apply minimum to offset Y
			#
			# *** NOTES ***
			# It is often desirable to check the increment as well. The increment
			# is a number of which a desired value must be a multiple. Certain
			# nodes, such as those corresponding to offsets X and Y, have an
			# increment of 1, which basically means that any value within range
			# is appropriate. The increment is retrieved with the method GetInc().
			if self.cam.OffsetY.GetAccessMode() == PySpin.RW:
				self.cam.OffsetY.SetValue(self.offset[1])
				if self.verbose: print('Offset Y set to %d...' % self.cam.OffsetY.GetValue())

			else:
				print('Offset Y not available...')
				result = False


		except PySpin.SpinnakerException as ex:
			print('Error: %s' % ex)
			return False

		return result

	def print_device_info(self):
		"""
		This function prints the device information of the camera from the transport
		layer; please see NodeMapInfo example for more in-depth comments on printing
		device information from the nodemap.

		:param cam: Camera to get device information from.
		:type cam: CameraPtr
		:return: True if successful, False otherwise.
		:rtype: bool
		"""

		print('\n*** DEVICE INFORMATION ***\n')

		try:
			result = True
			nodemap = self.cam.GetTLDeviceNodeMap()

			node_device_information = PySpin.CCategoryPtr(nodemap.GetNode('DeviceInformation'))

			if PySpin.IsAvailable(node_device_information) and PySpin.IsReadable(node_device_information):
				features = node_device_information.GetFeatures()
				for feature in features:
					node_feature = PySpin.CValuePtr(feature)
					print('%s: %s' % (node_feature.GetName(),
									  node_feature.ToString() if PySpin.IsReadable(node_feature) else 'Node not readable'))

			else:
				print('Device control information not available.')

		except PySpin.SpinnakerException as ex:
			print('Error: %s' % ex.message)
			return False

		return result

	@threaded
	def acquire_image(self):
		"""
		This function acquires and saves 10 images from a device; please see
		Acquisition example for more in-depth comments on the acquisition of images.

		:param cam: Camera to acquire images from.
		:type cam: CameraPtr
		:return: True if successful, False otherwise.
		:rtype: bool
		"""
		if self.verbose: print('\n*** IMAGE ACQUISITION ***\n')

		new_im = np.zeros((1,self.wh[1],self.wh[0]),dtype=int) #yes, it is annoyingly switched
		capture_time = 0.0;
		try:
			result = True

			# Set acquisition mode to continuous
			if self.cam.AcquisitionMode.GetAccessMode() != PySpin.RW:
				print('Unable to set acquisition mode to continuous. Aborting...')
				return False

			self.cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
			if self.verbose: print('Acquisition mode set to continuous...')

			# Begin acquiring images
			while time.time()<self.start_time:
				time.sleep(0.001);
			self.cam.BeginAcquisition()

			if self.verbose: print('Acquiring images...')

			# Get device serial number for filename
			device_serial_number = ''
			if self.cam.TLDevice.DeviceSerialNumber is not None and self.cam.TLDevice.DeviceSerialNumber.GetAccessMode() == PySpin.RO:
				device_serial_number = self.cam.TLDevice.DeviceSerialNumber.GetValue()

				if self.verbose: print('Device serial number retrieved as %s...' % device_serial_number)

			if self.verbose: t_start = time.time();
			# Retrieve, convert, and save images
			try:
				# Retrieve next received image and ensure image completion
				image_result = self.cam.GetNextImage()

				if image_result.IsIncomplete():
					print('Image incomplete with image status %d...' % image_result.GetImageStatus())
				
				new_im[0,:,:] = image_result.GetNDArray()
			except PySpin.SpinnakerException as ex:
				print('Error: %s' % ex)
				result = False
			# End acquisition
			self.cam.EndAcquisition()
		except PySpin.SpinnakerException as ex:
			print('Error: %s' % ex)
			result = False
		return new_im


	@threaded
	def acquire_images(self,num_frames=NUM_IMAGES,save_images=False):
		"""
		This function acquires and saves 10 images from a device; please see
		Acquisition example for more in-depth comments on the acquisition of images.

		:param cam: Camera to acquire images from.
		:type cam: CameraPtr
		:return: True if successful, False otherwise.
		:rtype: bool
		"""
		if self.verbose: print('\n*** IMAGE ACQUISITION ***\n')
		
		new_vid = np.zeros((num_frames,self.wh[1],self.wh[0]),dtype=int) #yes, it is annoyingly switched
		capture_times = np.zeros((num_frames));
		try:
			result = True

			# Set acquisition mode to continuous
			if self.cam.AcquisitionMode.GetAccessMode() != PySpin.RW:
				print('Unable to set acquisition mode to continuous. Aborting...')
				return False

			self.cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
			if self.verbose: print('Acquisition mode set to continuous...')

			# Begin acquiring images
			while time.time()<self.start_time:
				time.sleep(0.001);
			self.cam.BeginAcquisition()

			if self.verbose: print('Acquiring images...')

			# Get device serial number for filename
			device_serial_number = ''
			if self.cam.TLDevice.DeviceSerialNumber is not None and self.cam.TLDevice.DeviceSerialNumber.GetAccessMode() == PySpin.RO:
				device_serial_number = self.cam.TLDevice.DeviceSerialNumber.GetValue()

				if self.verbose: print('Device serial number retrieved as %s...' % device_serial_number)

			if self.verbose: t_start = time.time();
			# Retrieve, convert, and save images
			for i in range(num_frames):

				try:
					# Retrieve next received image and ensure image completion
					image_result = self.cam.GetNextImage()
					capture_times[i] = time.time();

					if image_result.IsIncomplete():
						print('Image incomplete with image status %d...' % image_result.GetImageStatus())

					else:
						# Print image information
						width = image_result.GetWidth()
						height = image_result.GetHeight()
						if self.verbose: 
							print('Grabbed Image %d, width = %d, height = %d' % (i, width, height))
							print(f'  in time {time.time()-t_start}')
							t_start = time.time();
						# Convert image to Mono8
						image_converted = image_result.Convert(PySpin.PixelFormat_Mono8)

						# Create a unique filename
						if device_serial_number and save_images:
							filename = 'ImageFormatControlQS-%s-%d.jpg' % (device_serial_number, i)
						else:
							filename = 'ImageFormatControlQS-%d.jpg' % i
						if save_images:
							# Save image
							image_converted.Save(filename)
							if self.verbose: print('Image saved at %s' % filename)
					new_vid[i,:,:] = image_result.GetNDArray()
					# Release image
					image_result.Release()

				except PySpin.SpinnakerException as ex:
					print('Error: %s' % ex)
					result = False

			# End acquisition
			self.cam.EndAcquisition()

		except PySpin.SpinnakerException as ex:
			print('Error: %s' % ex)
			result = False

		return new_vid, capture_times

if __name__ == "__main__":
    bc = blackfly_camera(verbose=True);
    im_holder = bc.acquire_image();
    from matplotlib import pyplot as plt
    import time
    while not im_holder.done():
        time.sleep(.1)
    image = im_holder.result();
    print(image)
    plt.imshow(np.squeeze(image),cmap='gray')
    plt.show();
