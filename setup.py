from setuptools import setup, find_packages
import os

from pydicomext._version import __version__

currentPath = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(currentPath, 'README.rst'), 'r') as f:
    long_description = f.read()

long_description = '\n' + long_description
setup(name='pydicomext',
      version=__version__,
      description='Python package that provides additional features to pydicom',
      long_description=long_description,
      long_description_content_type='text/x-rst',
      author='Addison Elliott',
      author_email='addison.elliott@gmail.com',
      url='https://github.com/addisonElliott/pydicomext',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Topic :: Scientific/Engineering',
          'License :: OSI Approved :: MIT License',
          "Programming Language :: Python",
          'Programming Language :: Python :: 3',
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "Programming Language :: Python :: 3.8",
          "Operating System :: OS Independent"

      ],
      keywords='pydicom dicom load read save medical imaging',
      project_urls={
          'Documentation': 'https://github.com/addisonElliott/pydicomext',
          'Source': 'https://github.com/addisonElliott/pydicomext',
          'Tracker': 'https://github.com/addisonElliott/pydicomext/issues',
      },
      python_requires='>=3.4',
      packages=find_packages(),
      license='MIT License',
      install_requires=[
          'numpy>=1.12', 'pydicom']
      )
