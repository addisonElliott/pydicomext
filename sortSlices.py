import logging
import operator

import pydicom

from .util import *

logger = logging.getLogger(__name__)
pydicom.config.datetime_conversion = True


def sortSlices(datasets, method=MethodType.Unknown, reverse=False):
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
        raise TypeError('Invalid method')

    # Check for oddities in the spacing per slice
    # Any spacing that deviate by a large amount or are close to zero indicate something is wrong
    if not np.allclose(spacingPerSlice, spacingPerSlice[0], atol=0.0, rtol=0.1):
        logger.warning('Warning: Spacing per slice is not uniform, greater than 10% tolerance')
        logger.debug('Spacing per slice: %s' % spacingPerSlice)
    if any(np.isclose(spacingPerSlice, [0.0], atol=0.01 * float(zSpacing))):
        logger.warning('Warning: Two slices are within 1% difference of each other')
        logger.debug('Spacing per slice: %s' % spacingPerSlice)

    return sortedDataset, zSpacing, sliceCosines
