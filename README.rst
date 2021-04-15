Introduction
==================================================
**pydicomext** provides additional functionality to the `pydicom <https://pydicom.github.io/pydicom/dev>`_ Python package which allows reading and saving DICOM files. This module extends *pydicom* to loading entire directories of DICOM files and organizing the data in terms of patients, studies and series to allow for easy traversal and identification of scans. In addition, *pydicomext* contains functions to manipulate series, merge two series together and even combine series into a Numpy volume is provided.

**If you find this project to be useful in any way, then please let me know via a GitHub issue, email or however!**

Installing
==================================================
Prerequisites
--------------------------------------------------
* Python 3.4+
* Dependencies:
    * pydicom

Installing pydicomext
--------------------------------------------------
pydicomext is currently available on `PyPi <https://pypi.python.org/pypi/pydicomext/>`_. The simplest way to
install is using ``pip`` at the command line::

  pip install pydicomext

which installs the latest release. To install the latest code from the repository (usually stable, but may have
undocumented changes or bugs)::

  pip install git+https://github.com/addisonElliott/pydicomext.git


For developers, you can clone the pydicomext repository and run the ``setup.py`` file. Use the following commands to get
a copy from GitHub and install all dependencies::

  git clone pip install git+https://github.com/addisonElliott/pydicomext.git
  cd pydicomext
  pip install .

or, for the last line, instead use::

  pip install -e .

to install in 'develop' or 'editable' mode, where changes can be made to the local working code and Python will use
the updated code.

Test and coverage
==================================================

Tests are currently non-existent.

Examples
==================================================

Loading and displaying DICOM directory information
--------------------------------------------------

.. code-block:: python

    dicomDir = loadDirectory('DICOM DIRECTORY HERE')

    print(dicomDir)

Result:

.. code-block::

    DicomDir
        Patient MF0307_V3
            Name: MF0307
            Issuer of ID:
            Birth Date: 19910613
            Birth Time: None
            Sex: F
            Other IDs:
            Other Names:
            Age: 026Y
            Size: 1.4732
            Weight: 79.3786
            Ethnic Group:
            Comments:
            Identity Removed: NO
            Position: HFS
            Studies:
                Study 1.3.12.2.1107.5.2.50.175614.30000017120515575743500000290
                    Date: 20171206
                    Time: 121132.400000
                    Desc: CCIR-00900^CCIR-00956
                    Series:
                        Series 1.3.12.2.1107.5.2.50.175614.30000017120614415244700000349
                            Date: 20171206
                            Time: 122855.475000
                            Desc: cine_trufi_cs_rt_adapt_trig_10sl_invf
                            Number: 10001
                            [18 datasets]
                        Series 1.3.12.2.1107.5.2.50.175614.30000017120614415244700000010
                            Date: 20171206
                            Time: 121807.861000
                            Desc: localizer_heart
                            Number: 1001
                            [14 datasets]
                        Series 1.3.12.2.1107.5.2.50.175614.30000017120614415244700000388
                            Date: 20171206
                            Time: 122855.577000
                            Desc: cine_trufi_cs_rt_adapt_trig_10sl_invf_INTP
                            Number: 11001
                            [25 datasets]
                        Series 1.3.12.2.1107.5.2.50.175614.30000017120614415244700000441
                            Date: 20171206
                            Time: 122903.466000
                            Desc: cine_trufi_cs_rt_adapt_trig_10sl_invf
                            Number: 12001
                            [18 datasets]
                        Series 1.3.12.2.1107.5.2.50.175614.30000017120614415244700000480
                            Date: 20171206
                            Time: 122903.570000
                            Desc: cine_trufi_cs_rt_adapt_trig_10sl_invf_INTP
                            Number: 13001
                            [25 datasets]
                        Series 1.3.12.2.1107.5.2.50.175614.30000017120614415244700000533
                            Date: 20171206
                            Time: 122911.695000
                            Desc: cine_trufi_cs_rt_adapt_trig_10sl_invf
                            Number: 14001
                            [20 datasets]
                        Series 1.3.12.2.1107.5.2.50.175614.30000017120614415244700000576
                            Date: 20171206
                            Time: 122911.796000
                            Desc: cine_trufi_cs_rt_adapt_trig_10sl_invf_INTP
                            Number: 15001
                            [25 datasets]
                        Series 1.3.12.2.1107.5.2.50.175614.30000017120614415244700000629
                            Date: 20171206
                            Time: 122919.754000
                            Desc: cine_trufi_cs_rt_adapt_trig_10sl_invf
                            Number: 16001
                            [19 datasets]
                        Series 1.3.12.2.1107.5.2.50.175614.30000017120614415244700000670
                            Date: 20171206
                            Time: 122919.862000
                            Desc: cine_trufi_cs_rt_adapt_trig_10sl_invf_INTP
                            Number: 17001
                            [25 datasets]
                        ...

Combining cMRI scans into a volume
--------------------------------------------------

.. code-block:: python

    dicomDir = loadDirectory('DICOM DIRECTORY HERE')

    # Retrieves the only patient from the directory, throws error if more than one patient
    patient = dicomDir.only()

    # Retrieves the only study from the patient, throws error if more than one study
    study = patient.only()

    # Retrieve a list of all series that have the description 'cine_trufi_cs_2_shot'
    # Each series is a class pydicomext.Series
    # This DICOM directory has multiple series that represent a Z-slice of the heart
    # Each series has multiple temporal frames of that slice of the heart at a certain time frame
    seriess = list(iter(filter(lambda x: x.description == 'cine_trufi_cs_2_shot', study.values())))

    # Merge the series into one, essentially takes datasets from each series and puts into one big series
    series = mergeSeries(seriess)

    # Combine the series into a Numpy volume
    volume = series.combine(methods=[MethodType.StackPosition, MethodType.TemporalPositionIndex])

    # Print data of the volume, which is of type pydicomext.Volume
    # Can access Numpy array by volume.data
    print(volume)

Result:

.. code-block::

    Volume
        Space: left-posterior-superior
        Orientation: [[-5.80474000e-01  4.44949000e-01 -6.81959360e-01]
            [ 2.95683000e-07  8.37502000e-01  5.46433310e-01]
            [-8.14278000e-01 -3.17191000e-01  4.86148268e-01]]
        Origin: [  30.0193 -150.763   271.145 ]
        Spacing: [1.      1.      1.47266 1.47266]
        Volume shape: (12, 16, 256, 256)

Roadmap & Bugs
==================================================
- Create unit tests from local tests
- Add *separate* function in Series class that will take a Volume class and apply it to the Series
- Add a *flatten* function in Series class that will take a Series and flatten it into one Series.
    - This is useful when combining two multi-frame Series into one. This will merge that into one series.
    - Haven't thought about it much for what it will do for a standard DICOM.
- Add a *prefaltten* function (maybe rename) that will look through a series and get all differences between them.
    - This should exclude basic fields that will change such as slice location, image number, triger time, etc. Or allow some way of deciding what fields to exclude

Pull requests are welcome (and encouraged) for any or all issues!

License
==================================================
*pydicomext* has an MIT-based [license](https://github.com/addisonElliott/pydicomext/blob/master/LICENSE>).