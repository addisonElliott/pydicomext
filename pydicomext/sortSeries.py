import pydicom

from pydicomext.util import *
from pydicomext.series import Series

pydicom.config.datetime_conversion = True


def sortSeries(series, methods=MethodType.Unknown, reverse=False, squeeze=False, warn=True, shapeTolerance=0.01,
               spacingTolerance=0.1):
    """Sorts datasets in series based on its metadata

    Sorting the datasets within the series can be done based on a number of parameters, which are primarily going to be
    spatial or temporal based.

    Parameters
    ----------
    series : Series
    methods : MethodType or list(MethodType), optional
        A single method or a list of methods to use when sorting the series. If this is :obj:`MethodType.Unknown`, then
        the best methods will be retrieved based on the datasets metadata. If a list of methods are given, then the
        series is sorted in order from left to right of the methods. This in effect will create multidimensional series
        (the default is MethodType.Unknown which will retrieve the best methods based on the series)
    reverse : bool, optional
        Whether or not to reverse the sort, where the default sorting order is ascending (the default is False)
    squeeze : bool, optional
        Whether to remove unnecessary dimensions of size 1 (default is False, meaning dimensions are untouched). The
        resulting methods and spacing will be updated accordingly to remove unnecessary dimensions of size 1.
    warn : bool, optional
        Whether to warn or raise an exception for non-uniform grid spacing (default is True which will display warnings
        rather than exceptions)
    shapeTolerance : float, optional
        Amount of relative tolerance to allow between the shape. Default value is 1% (0.01) which should be sufficient
        in most cases. There should not be much deviation in the shape or else the volume cannot be combined easily.

        Note: Only the first shape calculated is used but this tolerance is used to verify that the shape is similar to
        all others.
    spacingTolerance : float, optional
        Amount of relative tolerance to allow between the spacing. Default value is 10% (0.10) which should be
        sufficient in most cases. However, there are instances where the coordinates have non-uniform spacing
        in which case the tolerance should be increased if the user verifies everything is alright.

        An example of where this parameter becomes useful is for the TriggerTime method because the trigger time may
        not be the same throughout the process.

        Note: Only the first spacing calculated is used but this tolerance is used to verify that spacing is similar to
        all others.

    Raises
    ------
    TypeError
        If the series is empty or the method is invalid

    Returns
    -------
    Series
        Series that has been sorted
    """

    if len(series) == 0:
        raise TypeError('Series must contain at least one dataset')

    if methods == MethodType.Unknown:
        methods = getBestMethods(series)

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
            # Get slice positions for each object
            slicePositions = getZPositionsFromPatientInfo(series)

            keys.append(slicePositions)
        elif method == MethodType.TriggerTime:
            keys.append([d.TriggerTime for d in series])
        elif method == MethodType.AcquisitionDateTime:
            keys.append([d.AcquisitionDateTime.timestamp() * 1000.0 for d in series])
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
            # Get slice positions for each object
            slicePositions = getZPositionsFromPatientInfo(series)

            keys.append(slicePositions)
        elif method == MethodType.MFAcquisitionDateTime:
            keys.append([d.FrameContentSequence[0].FrameAcquisitionDateTime.timestamp() * 1000.0 for d in series])
        elif method == MethodType.CardiacTriggerTime:
            keys.append([d.CardiacSynchronizationSequence[0].NominalCardiacTriggerDelayTime for d in series])
        elif method == MethodType.CardiacPercentage:
            keys.append([d.CardiacSynchronizationSequence[0].NominalPercentageOfCardiacPhase for d in series])

    # Append the actual series to the end of the list so they are sorted as well
    keys.append(series)

    # Lots is happening here, but let me break it up one by one
    # Zip up the keyAttrs so that each iterator in the list will be: (key1, key2, key3, ..., series)
    # Then sort that list which will sort based on key1, then key2, etc (but do NOT use dataset as sorting key!)
    # Next we unzip the list (by zipping it again) so that each list is the entire list of keys for that method
    sortedKeys = list(zip(*sorted(zip(*keys), key=lambda x: x[:-1], reverse=reverse)))

    # Sorted series is the last element and the remaining items are the keys used for sorting
    # Wrap the sorted series back into Series class because it is a tuple
    sortedSeries, sortedKeys = Series(sortedKeys[-1]), sortedKeys[:-1]

    # Update to determine if series is multiframe
    sortedSeries.checkIsMultiFrame()

    # From the sorted keys, get the shape of the ND data and spacing
    shape, spacing = getSpacingDims(sortedKeys, warn, shapeTolerance, spacingTolerance)

    # Squeeze dimensional data by removing any instances with a 1 for the shape
    if squeeze:
        # Zip up the shape, spacing, methods. Filter any components out that have a dimension of 1
        squeezedData = list(filter(lambda x: x[0] != 1, zip(shape, spacing, methods)))

        # Unzip the data (by zipping again)
        shape, spacing, methods = list(zip(*squeezedData))
    else:
        # Convert shape and spacing to a tuple, better for passing around, should not be mutable
        shape, spacing = tuple(shape), tuple(spacing)

    # Update the metadata in the series itself
    sortedSeries._shape = shape
    sortedSeries._spacing = spacing
    sortedSeries._methods = methods

    # Return methods as well because the user may have set the method type to unknown to retrieve best method type, so
    # they would want to know the results
    return sortedSeries
