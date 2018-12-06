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

    attrs = []
    for method in methods:
        # Check all of the specified methods for any invalid ones
        if not isMethodValid(series, method):
            raise TypeError('Invalid method specified: %s' % method)

        if method == MethodType.SliceLocation:
            attrs.append([d.SliceLocation for d in series])
        elif method == MethodType.PatientLocation:
            # Get slice positions for each object
            sliceCosines, slicePositions = slicePositionsFromPatientInfo(series)

            attrs.append(slicePositions)
        elif method == MethodType.TriggerTime:
            attrs.append([d.TriggerTime for d in series])
        elif method == MethodType.AcquisitionDateTime:
            attrs.append([d.AcquisitionDateTime for d in series])
        elif method == MethodType.ImageNumber:
            attrs.append([d.InstanceNumber for d in series])
        elif method == MethodType.StackID:
            attrs.append([int(d.FrameContentSequence[0].StackID) for d in series])
        elif method == MethodType.StackPosition:
            attrs.append([d.FrameContentSequence[0].InStackPositionNumber for d in series])
        elif method == MethodType.TemporalPositionIndex:
            attrs.append([d.FrameContentSequence[0].TemporalPositionIndex for d in series])
        elif method == MethodType.FrameAcquisitionNumber:
            attrs.append([d.FrameContentSequence[0].FrameAcquisitionNumber for d in series])
        elif method == MethodType.MFPatientLocation:        
            # TODO Do me
            sliceCosines, slicePositions = slicePositionsFromPatientInfo(series)
            attrs.append(slicePositions)
        elif method == MethodType.MFAcquisitionDateTime:
            attrs.append([d.FrameContentSequence[0].MFAcquisitionDateTime for d in series])
        elif method == MethodType.CardiacTriggerTime:
            attrs.append([d.CardiacSynchronizationSequence[0].NominalCardiacTriggerDelayTime for d in series])
        elif method == MethodType.CardiacPercentage:
            attrs.append([d.CardiacSynchronizationSequence[0].NominalPercentageOfCardiacPhase for d in series])

    attrs.append(series)
    sortedAttrs = list(zip(*sorted(zip(*attrs), reverse=reverse)))

    sortedSeries = sortedAttrs[-1]

    sortedAttrs = sortedAttrs[:-1]
    diffs = list(map(np.diff, sortedAttrs))

    # TODO This is going to be different for multiframe DICOM vs regular DICOM, general idea is the same though
    return sortedSeries, diffs


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
