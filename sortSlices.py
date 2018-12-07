import pydicom

from .util import *

pydicom.config.datetime_conversion = True


def sortSlices(series, methods=MethodType.Unknown, reverse=False, warn=True):
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
    warn : bool, optional
        Whether to warn or raise an exception for non-uniform grid spacing
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

    # From the sorted keys, get the shape of the ND data and spacing
    shape, spacing = getSpacingDims(sortedKeys, warn=warn)

    # TODO Squeeze the shape/spacing?
    # TODO Include shape/spacing for images themselves? Pixel spacing, etc?
    # TODO This is going to be different for multiframe DICOM vs regular DICOM, general idea is the same though
    # return sortedSeries, diffs

    return sortedSeries, shape, spacing
