# Introduction

**pydicomext** provides additional functionality to the [pydicom](https://pydicom.github.io/pydicom/dev) Python package which allows reading and saving DICOM files. This module extends *pydicom* to loading entire directories of DICOM files and organizing the data in terms of patients, studies and series to allow for easy traversal and identification of scans. In addition, *pydicomext* contains functions to manipulate series, merge two series together and even combine series into a Numpy volume is provided.

As of now, I do not feel comfortable releasing this project on PyPi yet because it is an early beta stage and I'm worried there are a bugs in the code. This project is used in multiple projects of mine and I did not want to have separate copies of the repository in case changes are made. **If you like this project and want to see it on PyPi, contact me somehow and let me know!***

**If you find this project to be useful in any way, then please let me know via a GitHub issue, email or however! This will motivate me to finish it and make it a PyPi library! Feedback is always welcome**

# Installation

## Cloning Repository (for projects without Git)

Cloning the repository can be done with the following commands in a Bash or Git Bash terminal with Git installed. In addition, Git GUIs such as GitHub Desktop, TortoiseGit, etc can be used to clone the repository as well.
```bash
git clone https://github.com/addisonElliott/pydicomext.git
```

Updating *pydicomext* can be done with the following commands within the pydicomext folder or once again by using a Git GUI.
```bash
git pull origin master
```

## Adding as Git Submodule (for projects with Git)

For projects that use Git for tracking changes in their source code, it is recommended to utilize *pydicomext* as a Git submodule. The primary advantage of this approach over cloning the repository is that it will not track any changes in the pydicomext folder.

Run the following commands from your project to include *pydicomext* in the project as Git submodule.
```bash
git submodule add -b master https://github.com/addisonElliott/pydicomext.git <PATH_HERE, e.g. util/pydicomext>
git submodule init
```

Updating *pydicomext* can be done with the following commands from your project.
```bash
git submodule update --remote
```

**Note:** For cloning **your project** with *pydicomext* as a Git submodule, there are a few extra steps that one must perform to clone the pydicomext module as well.
```bash
git submodule init
git submodule update
```

You can do this all in one command when cloning the repository by adding the *recurse-submodules* option.
```bash
git clone --recurse-submodules <YOUR_REPO_LINK_HERE>
```

# Test and Coverage

Currently, I have a local test Python file with path-specific DICOM directories that are loaded. If I decide to upload this project to PyPi, I would want to create unit tests.

# Examples

## Loading and displaying DICOM directory information

```python
dicomDir = loadDirectory('DICOM DIRECTORY HERE')

print(dicomDir)
```

Result:
```
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
```

## Combining cMRI scans into a volume

```python
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
```

Result:
```
Volume
    Space: left-posterior-superior
    Orientation: [[-5.80474000e-01  4.44949000e-01 -6.81959360e-01]
 [ 2.95683000e-07  8.37502000e-01  5.46433310e-01]
 [-8.14278000e-01 -3.17191000e-01  4.86148268e-01]]
    Origin: [  30.0193 -150.763   271.145 ]
    Spacing: [1.      1.      1.47266 1.47266]
    Volume shape: (12, 16, 256, 256)
```

# License

*pydicomext* has an MIT-based [license](https://github.com/addisonElliott/pydicomext/blob/master/LICENSE>).
