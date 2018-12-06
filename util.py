from enum import Enum, auto

import numpy as np


# TODO Need to reevaluate this because we may have N-D volumes that are spatial temporal all at once.
class VolumeType(Enum):
    Unknown = auto()
    Spatial = auto()
    Temporal = auto()


class MethodType(Enum):
    Unknown = auto()

    # Standard DICOM
    SliceLocation = auto()
    PatientLocation = auto()
    TriggerTime = auto()
    AcquisitionDateTime = auto()
    ImageNumber = auto()

    # Multi-frame DICOM
    StackID = auto()
    StackPosition = auto()
    TemporalPositionIndex = auto()
    FrameAcquisitionNumber = auto()
    MFPatientLocation = auto()
    MFAcquisitionDateTime = auto()
    CardiacTriggerTime = auto()
    CardiacPercentage = auto()

    allStandard = [SliceLocation, PatientLocation, TriggerTime, AcquisitionDateTime, ImageNumber]
    allMultiFrame = [StackID, StackPosition, TemporalPositionIndex, FrameAcquisitionNumber, MFPatientLocation, 
                     MFAcquisitionDateTime, CardiacTriggerTime, CardiacPercentage]

    @property
    def isMultiFrame(self):
        return self.value >= self.StackID.value

    # Slice Location or patient location
    # Trigger time or acquisition date time
    # Otherwise, use image number
    # Otherwise fail
    #
    # Stack ID on its own
    # Stack position or MF patient location or frame acquisiton number
    # Temporal position index or Cardiac trigger time or cardiac percentage or acquisition date time
    # Otherwise fail


def isMethodValid(series, method):
    """Determines if a method is valid for a particular series

    Checks if a given method is available for sorting or combining a series. This checks the DICOM header of each
    dataset in the series for the specified tag based on the method given.

    Parameters
    ----------
    series : Series
        Series of datasets to check
    method : MethodType
        Method to check

    Raises
    ------
    TypeError
        If invalid method is given or if the series is empty

    Returns
    -------
    bool
        True if the method is a valid method of sorting/combining the given series, False otherwise
    """

    if len(series) == 0:
        raise TypeError('Series must contain at least one dataset')

    if method == MethodType.Unknown:
        raise TypeError('Unknown method type is invalid')

    # Method and series must both be multi frame or not
    if method.isMultiFrame != series.isMultiFrame:
        return False

    if method == MethodType.SliceLocation:
        return all(['SliceLocation' in d for d in series])
    elif method == MethodType.PatientLocation:
        return all(['ImageOrientationPatient' in d and 'ImagePositionPatient' in d for d in series])
    elif method == MethodType.TriggerTime:
        return all(['TriggerTime' in d for d in series])
    elif method == MethodType.AcquisitionDateTime:
        return all(['AcquisitionDateTime' in d for d in series])
    elif method == MethodType.ImageNumber:
        return all(['InstanceNumber' in d for d in series])
    elif method == MethodType.StackID:
        return all(['StackID' in d.FrameContentSequence[0] and d.FrameContentSequence[0].StackID.isdigit()
                    for d in series])
    elif method == MethodType.StackPosition:
        return all(['InStackPositionNumber' in d.FrameContentSequence[0] for d in series])
    elif method == MethodType.TemporalPositionIndex:
        return all(['TemporalPositionIndex' in d.FrameContentSequence[0] for d in series])
    elif method == MethodType.FrameAcquisitionNumber:
        return all(['FrameAcquisitionNumber' in d.FrameContentSequence[0] for d in series])
    elif method == MethodType.MFPatientLocation:
        return all(['ImageOrientationPatient' in d.PlaneOrientationSequence[0] and
                    'ImagePositionPatient' in d.PlanePositionSequence[0] for d in series])
    elif method == MethodType.MFAcquisitionDateTime:
        return all(['FrameAcquisitionDateTime' in d.FrameContentSequence[0] for d in series])
    elif method == MethodType.CardiacTriggerTime:
        return all(['CardiacSynchronizationSequence' in d and
                    'NominalCardiacTriggerDelayTime' in d.CardiacSynchronizationSequence[0] for d in series])
    elif method == MethodType.CardiacPercentage:
        return all(['CardiacSynchronizationSequence' in d and
                    'NominalPercentageOfCardiacPhase' in d.CardiacSynchronizationSequence[0] for d in series])
    else:
        raise TypeError('Invalid method specified')


# TODO Evaluate if I need this function
def getTypeFromMethod(method):
    """
    Select the type of volume based off the method used to combine slices
    """
    if method in [MethodType.SliceLocation, MethodType.PatientLocation]:
        return VolumeType.Spatial
    elif method in [MethodType.TriggerTime, MethodType.AcquisitionDateTime]:
        return VolumeType.Temporal
    else:
        return VolumeType.Unknown


def getBestMethod(series):
    """Select best method to use for sorting/combining datasets in a series

    Parameters
    ----------
    series : Series

    Raises
    ------
    TypeError
        If unable to find the best method or if the series is empty

    Returns
    -------
    list(MethodType)
        Return list of best method type to use
    """

    if len(series) == 0:
        raise TypeError('Series must contain at least one dataset')

    method = MethodType.Unknown

    # For this, since we may be dealing with multidimensional data, we want to see how many groups we would have
    # Also, not sure I want to check if the method is valid since it consists of calling all twice, can do all in one run I think

    methods = []
    checkMethods = MethodType.allMultiFrame if series.isMultiFrame else MethodType.allStandard

    # If slice location is not present on either one, then stop
    for d in series:
        for method in checkMethods:
            if method == MethodType.TriggerTime:
                if 'TriggerTime' not in d:
                    checkMethods.remove(method)
                elif series[0].TriggerTime != d.TriggerTime:
                    methods.append(method)
                    # TODO Also remove other temporal ones here!
                    checkMethods.remove(method)

    # return methods

    if isMethodValid(series, MethodType.SliceLocation) \
            and any([series[0].SliceLocation != d.SliceLocation for d in series]):
        method = MethodType.SliceLocation
    elif isMethodValid(series, MethodType.PatientLocation) \
            and any([series[0].ImageOrientationPatient != d.ImageOrientationPatient
                     or series[0].ImagePositionPatient != d.ImagePositionPatient for d in series]):
        method = MethodType.PatientLocation
    elif isMethodValid(series, MethodType.TriggerTime) \
            and any([series[0].TriggerTime != d.TriggerTime for d in series]):
        method = MethodType.TriggerTime
    elif isMethodValid(series, MethodType.AcquisitionDateTime) \
            and any([series[0].AcquisitionDateTime != d.AcquisitionDateTime for d in series]):
        method = MethodType.AcquisitionDateTime
    elif isMethodValid(series, MethodType.ImageNumber) \
            and any([series[0].ImageNumber != d.ImageNumber for d in series]):
        method = MethodType.ImageNumber
    else:
        raise TypeError('Unable to find best method')

    # TODO Add new method types here!

    return method


def slicePositionsFromPatientInfo(datasets):
    """
    This function is used for the MethodType.PatientLocation method. It retrieves the slice location from the
    Patient Image Orientation and Patient Image Position fields.

    :return: Returns a list of slice positions for the current dataset.
    """
    imageOrientation = datasets[0].ImageOrientationPatient

    # Row cosines is first 3 elements, column cosines is last 3 elements of array
    rowCosines = np.array(imageOrientation[:3])
    colCosines = np.array(imageOrientation[3:])

    # Get cross product of row and column cosines
    sliceCosines = np.cross(rowCosines, colCosines)

    # Slice location is dot product of slice cosines and the image patient position
    return sliceCosines, [np.dot(sliceCosines, d.ImagePositionPatient) for d in datasets]


def datasetDeleteOrRemove(dataset, key, value):
    if value is not None:
        dataset[key] = value
    elif key in dataset:
        del dataset[key]
