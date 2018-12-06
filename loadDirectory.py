import os

import pydicom
import pydicom.filereader

from .patient import Patient
from .dicomDir import DicomDir
from .series import Series
from .study import Study


def loadDirectory(directory, patientID=None, studyID=None, seriesID=None):
    dicomDir = DicomDir()
    patient = None
    study = None
    series = None

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
        DCMImage = pydicom.dcmread(filename, defer_size=2048)

        if patientID:
            if DCMImage.PatientID != patientID:
                continue

            patient = Patient(DCMImage)
        else:
            # Check for existing patient, if not add new patient
            if DCMImage.PatientID in dicomDir:
                patient = dicomDir[DCMImage.PatientID]
            else:
                patient = dicomDir.add(DCMImage)

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

        # Regular append isn't the best here, I'm thinking append will be used for adding/altering lists
        # but even then, I want to check if we are adding multiple series IDs and such
        #
        # Update ID, description, on Series. Make it None if multiple times
        # Check for MultiFrame data, handle accordingly.
        # But, there may be cases where we know this is true/false and don't want to update.
        #
        # Should just the usual append check stuff?
        # Append/extend...
        # Update function, should we call this manually and it will do that stuff
        # Checking for multiframe data should only be done once because otherwise it may overwrite info in the list...
        #
        # Okay, thinking of a function that will be public but probably only loadDirectory will call to handle the multiframe data
        # at the end of loading everything.
        # Something like series.loadMultiFrame() <--- Good this will imply that it's going to overwrite any data in series
        # Plus, it will allow in the very **off chance** that there are multiple multiframes per series.
        #
        # Next function I need is something to clear the series specific data. Maybe more appropriately is a function that will check
        # this information.
        # updateSeriesInfo() <-- Why does this matter? Why keep this data valid?
        # Why not have a mutable series where these values are set to false anyhow?
        # Well, we will let the user be the one that calls this function after they make large changes to it.
        # updateSeries(startNewIndex=0) <-- Index indicates at what position the data is new, typically this will be negative like
        # -1 means one new item at the end
        # Useful if you just add a few items to the end and dont want to recheck everything
        # TODO Rename DCMImage to dataset! Confuses me
        #
        # Also, maybe those parameters should be properties that derive from cached values. That way if you try to change it, it will go
        # through the trouble of changing the children data and DCM data itself.

        # Append image to series
        series.append(DCMImage)

    if patientID:
        return patient
    elif studyID:
        return study
    elif seriesID:
        return series
    else:
        return dicomDir
