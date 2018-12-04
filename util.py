from enum import Enum

import numpy as np


class VolumeType(Enum):
    Unknown = 0
    Spatial = 1
    Temporal = 2


class MethodType(Enum):
    Unknown = 0
    SliceLocation = 1
    PatientLocation = 2
    TriggerTime = 3
    AcquisitionDateTime = 4
    ImageNumber = 5


def isMethodAvailable(datasets, method):
    """
    Checks if a given method is available from the dataset in the class. This checks the DICOM header for specified
    tags for each of the DICOM images.

    :param datasets: List of DICOM images to be combined into a 3D volume
    :param method: Method to check whether it is available. Must be option from VolumeType
    :return: Returns true if method is available in dataset, otherwise it returns false
    """

    if method == MethodType.TriggerTime:
        return all(['TriggerTime' in d for d in datasets])
    elif method == MethodType.AcquisitionDateTime:
        return all(['AcquisitionDateTime' in d for d in datasets])
    elif method == MethodType.ImageNumber:
        return all(['ImageNumber' in d for d in datasets])
    elif method == MethodType.SliceLocation:
        return all(['SliceLocation' in d for d in datasets])
    elif method == MethodType.PatientLocation:
        return all(['ImageOrientationPatient' in d and 'ImagePositionPatient' in d for d in datasets])
    else:
        raise TypeError('Invalid method specified')


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


def getBestMethod(datasets):
    """
    Select the best method to use for combining the slices in the dataset. The methods are checked in the following
    order:
        SliceLocation, PatientLocation, TriggerTime, AcquisitionDateTime, ImageNumber
    Thus, it follows that the slices are checked for spatial differences first before temporal differences. This
    yields the best results because spatial slices can still be acquired at different times and not be considered a
    time series.

    :return: Returns MethodType value representing the best method to use for combining slices
    """
    # noinspection PyUnusedLocal
    method = MethodType.Unknown

    if isMethodAvailable(datasets, MethodType.SliceLocation) \
            and any([datasets[0].SliceLocation != d.SliceLocation for d in datasets]):
        method = MethodType.SliceLocation
    elif isMethodAvailable(datasets, MethodType.PatientLocation) \
            and any([datasets[0].ImageOrientationPatient != d.ImageOrientationPatient
                     or datasets[0].ImagePositionPatient != d.ImagePositionPatient for d in datasets]):
        method = MethodType.PatientLocation
    elif isMethodAvailable(datasets, MethodType.TriggerTime) \
            and any([datasets[0].TriggerTime != d.TriggerTime for d in datasets]):
        method = MethodType.TriggerTime
    elif isMethodAvailable(datasets, MethodType.AcquisitionDateTime) \
            and any([datasets[0].AcquisitionDateTime != d.AcquisitionDateTime for d in datasets]):
        method = MethodType.AcquisitionDateTime
    elif isMethodAvailable(datasets, MethodType.ImageNumber) \
            and any([datasets[0].ImageNumber != d.ImageNumber for d in datasets]):
        method = MethodType.ImageNumber
    else:
        raise TypeError('Unable to find best method')

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
