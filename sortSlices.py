import logging
import operator
import pydicom

import numpy as np

from .util import *

logger = logging.getLogger(__name__)
pydicom.config.datetime_conversion = True


def sortSlices(series, methods=MethodType.Unknown, reverse=False):
    """Sorts datasets in series based on its metadata

    Sorting the datasets within the series can be done based on a number of parameters, which are primarily going to be
    spatial or temporal based.

    Parameters
    ----------
    series : Series
        [description]
    method : MethodType or list(MethodType), optional
        [description] (the default is MethodType.Unknown, which [default_description])
    reverse : bool, optional
        Whether or not to reverse the sort, where the default sorting order is ascending (the default is False)
    """

    if len(series) == 0:
        raise TypeError('Series must contain at least one dataset')

    if methods == MethodType.Unknown:
        methods = getBestMethod(series)

    # Make a list out of the method if it is not one
    if not isinstance(methods, list):
        methods = [methods]

    # This list will contain additional lists/iterators that are the keys to sort the series by
    keys = []

    # Loop through all of the methods and add the key values to the keyAttrs list
    for method in methods:
        # Check all of the specified methods for any invalid ones
        if not isMethodValid(series, method):
            raise TypeError('Invalid method specified: %s' % method)

        if method == MethodType.SliceLocation:
            keys.append([d.SliceLocation for d in series])
        elif method == MethodType.PatientLocation:
            # TODO Go through and clean the function up
            # Get slice positions for each object
            sliceCosines, slicePositions = slicePositionsFromPatientInfo(series)

            keys.append(slicePositions)
        elif method == MethodType.TriggerTime:
            keys.append([d.TriggerTime for d in series])
        elif method == MethodType.AcquisitionDateTime:
            keys.append([d.AcquisitionDateTime for d in series])
        elif method == MethodType.ImageNumber:
            keys.append([d.InstanceNumber for d in series])
        elif method == MethodType.StackID:
            keys.append([int(d.FrameContentSequence[0].StackID) for d in series])
        elif method == MethodType.StackPosition:
            keys.append([d.FrameContentSequence[0].InStackPositionNumber for d in series])
        elif method == MethodType.TemporalPositionIndex:
            keys.append([d.FrameContentSequence[0].TemporalPositionIndex for d in series])
        elif method == MethodType.FrameAcquisitionNumber:
            keys.append([d.FrameContentSequence[0].FrameAcquisitionNumber for d in series])
        elif method == MethodType.MFPatientLocation:
            # TODO Do me
            sliceCosines, slicePositions = slicePositionsFromPatientInfo(series)
            keys.append(slicePositions)
        elif method == MethodType.MFAcquisitionDateTime:
            keys.append([d.FrameContentSequence[0].MFAcquisitionDateTime for d in series])
        elif method == MethodType.CardiacTriggerTime:
            keys.append([d.CardiacSynchronizationSequence[0].NominalCardiacTriggerDelayTime for d in series])
        elif method == MethodType.CardiacPercentage:
            keys.append([d.CardiacSynchronizationSequence[0].NominalPercentageOfCardiacPhase for d in series])

    # Append the actual series to the end of the list so they are sorted as well
    keys.append(series)

    # Lots is happening here, but let me break it up one by one
    # Zip up the keyAttrs so that each iterator in the list will be: (key1, key2, key3, ..., series)
    # Then sort that list which will sort based on key1, then key2, etc
    # Next we unzip the list (by zipping it again) so that each list is the entire list of keys for that method
    sortedKeys = list(zip(*sorted(zip(*keys), key=lambda x: x[:-1], reverse=reverse)))

    # Sorted series is the last element and the remaining items are the keys used for sorting
    sortedSeries, sortedKeys = sortedKeys[-1], sortedKeys[:-1]
    # sortedKeys = sortedKeys[:-1]

    # diffs = list(map(np.diff, sortedKeys))

    # TODO This is going to be different for multiframe DICOM vs regular DICOM, general idea is the same though
    # return sortedSeries, diffs
    return sortedKeys


def sortSlices2(datasets, method=MethodType.Unknown, reverse=False):
    """
    Sorts the given dataset based on the parameters.
    """
    if len(datasets) == 0:
        raise TypeError('Must have at least one image in series to sort slices')

    if method is MethodType.Unknown:
        method = getBestMethod(datasets)
    elif not isMethodAvailable(datasets, method):
        raise TypeError('Invalid method specified')

    # Get slice positions for each object
    sliceCosines, slicePositions = slicePositionsFromPatientInfo(datasets)

    if method == MethodType.SliceLocation:
        sortedDataset = sorted(datasets, key=lambda x: x.SliceLocation, reverse=reverse)

        spacingPerSlice = np.diff([d.SliceLocation for d in sortedDataset])
        zSpacing = np.mean(spacingPerSlice)
    elif method == MethodType.PatientLocation:
        # Put slice positions and datasets together and sort by slice position
        sortedTogether = sorted(zip(slicePositions, datasets), key=operator.itemgetter(0), reverse=reverse)

        # Split the sorted slice positions and datasets into two separate lists
        sortedSlicePositions, sortedDataset = list(zip(*sortedTogether))

        spacingPerSlice = np.diff(sortedSlicePositions)
        zSpacing = np.mean(spacingPerSlice)
    elif method == MethodType.TriggerTime:
        sortedDataset = sorted(datasets, key=lambda x: x.TriggerTime, reverse=reverse)

        spacingPerSlice = np.diff([d.TriggerTime for d in sortedDataset])
        zSpacing = np.mean(spacingPerSlice)
    elif method == MethodType.AcquisitionDateTime:
        sortedDataset = sorted(datasets, key=lambda x: x.AcquisitionDateTime, reverse=reverse)

        # AcquisitionDateTime is in seconds, convert to milliseconds
        spacingPerSlice = np.diff([d.AcquisitionDateTime.timestamp() for d in sortedDataset]) * 1000.0
        zSpacing = np.mean(spacingPerSlice)
    elif method == MethodType.ImageNumber:
        spacingPerSlice = [0, 1, 2]
        sortedDataset = sorted(datasets, key=lambda x: x.ImageNumber, reverse=reverse)
        # ImageNumber has unknown z spacing, no units
        zSpacing = 0.0
    else:
        raise TypeError('Invalid method specified: %s' % method)

    # Check for oddities in the spacing per slice
    # Any spacing that deviate by a large amount or are close to zero indicate something is wrong
    if not np.allclose(spacingPerSlice, spacingPerSlice[0], atol=0.0, rtol=0.1):
        logger.warning('Warning: Spacing per slice is not uniform, greater than 10% tolerance')
        logger.debug('Spacing per slice: %s' % spacingPerSlice)
    if any(np.isclose(spacingPerSlice, [0.0], atol=0.01 * float(zSpacing))):
        logger.warning('Warning: Two slices are within 1% difference of each other')
        logger.debug('Spacing per slice: %s' % spacingPerSlice)

    return sortedDataset, zSpacing, sliceCosines
