import os

import pydicom
import pydicom.filereader

from pydicomext.patient import Patient
from pydicomext.dicomDir import DicomDir
from pydicomext.series import Series
from pydicomext.study import Study


def loadDirectory(directory, patientID=None, studyID=None, seriesID=None):
    dicomDir = DicomDir()
    patient = None
    study = None
    series = None
    seriess = []

    # Search for DICOM files within directory
    # Append each DICOM file to a list
    DCMFilenames = []
    for dirName, subdirs, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.dcm'):
                DCMFilenames.append(os.path.join(dirName, filename))

    # Throw an exception if there are no DICOM files in the given directory
    if not DCMFilenames:
        raise Exception('No DICOM files were found in the directory: %s' % directory)

    # Loop through each DICOM filename
    for filename in DCMFilenames:
        # Read DICOM file
        # Set defer_size to be 2048 bytes which means any data larger than this will not be read until it is first
        # used in code. This should primarily be the pixel data
        dataset = pydicom.dcmread(filename, defer_size=2048)

        if patientID:
            if dataset.PatientID != patientID:
                continue

            patient = Patient(dataset)
        else:
            # Check for existing patient, if not add new patient
            if dataset.PatientID in dicomDir:
                patient = dicomDir[dataset.PatientID]
            else:
                patient = dicomDir.add(dataset)

        if studyID:
            if dataset.StudyInstanceUID != studyID:
                continue

            study = Study(dataset)
        else:
            # Check for existing study for patient, if not add a new study
            if dataset.StudyInstanceUID in patient:
                study = patient[dataset.StudyInstanceUID]
            else:
                study = patient.add(dataset)

        if seriesID:
            if dataset.SeriesInstanceUID != seriesID:
                continue

            series = Series(dataset=dataset)
        else:
            # Check for existing series within study, if not add a new series
            if dataset.SeriesInstanceUID in study:
                series = study[dataset.SeriesInstanceUID]
            else:
                series = study.add(dataset)
                seriess.append(series)

        # Append image to series
        series.append(dataset)

    # Go through all of the series and load any multiframe data
    for series in seriess:
        series.loadMultiFrame()

    if patientID:
        return patient
    elif studyID:
        return study
    elif seriesID:
        return series
    else:
        return dicomDir
