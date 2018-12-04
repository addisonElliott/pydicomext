import os

import pydicom
import pydicom.filereader

from .patient import Patient
from .patients import Patients
from .series import Series
from .study import Study


def loadDirectory(path, patientID=None, studyID=None, seriesID=None):
    patients = Patients()
    patient = None
    study = None
    series = None

    # Search for DICOM files within directory
    # Append each DICOM file to a list
    DCMFilenames = []
    for dirName, subdirs, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith('.dcm'):
                DCMFilenames.append(os.path.join(dirName, filename))

    # Loop through each DICOM filename
    for filename in DCMFilenames:
        # Read DICOM file
        # Set defer_size to be 2048 bytes which means any data larger than this will not be read until it is first
        # used in code. This should primarily be the pixel data
        DCMImage = pydicom.dcmread(filename, defer_size=2048)

        if patientID:
            if DCMImage.PatientID != patientID:
                continue

            patient = Patient(DCMImage)
        else:
            # Check for existing patient, if not add new patient
            if DCMImage.PatientID in patients:
                patient = patients[DCMImage.PatientID]
            else:
                patient = patients.add(DCMImage)

        if studyID:
            if DCMImage.StudyInstanceUID != studyID:
                continue

            study = Study(DCMImage)
        else:
            # Check for existing study for patient, if not add a new study
            if DCMImage.StudyInstanceUID in patient:
                study = patient[DCMImage.StudyInstanceUID]
            else:
                study = patient.add(DCMImage)

        if seriesID:
            if DCMImage.SeriesInstanceUID != seriesID:
                continue

            series = Series(DCMImage)
        else:
            # Check for existing series within study, if not add a new series
            if DCMImage.SeriesInstanceUID in study:
                series = study[DCMImage.SeriesInstanceUID]
            else:
                series = study.add(DCMImage)

        # Append image to series
        series.append(DCMImage)

    if patientID:
        return patient
    elif studyID:
        return study
    elif seriesID:
        return series
    else:
        return patients
