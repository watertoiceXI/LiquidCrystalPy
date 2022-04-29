#!/usr/bin/env python

from distutils.core import setup

setup(name='LCpy',
      version='0.0',
      description='Python scripts to collect data for the Cressman lab liquid crystal studies.',
      author='Justin Peel',
      author_email='jhpeel@gmail.com',
      url='hahahahahaha',
      packages=['LCpy', 'LCpy.AnalogDiscovery', 'LCpy.QuickCapture'],
      install_requires=['spinnaker-python','dwf']
     )