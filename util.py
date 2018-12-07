from enum import Enum, auto
import logging

import numpy as np

logger = logging.getLogger(__name__)


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
        # Retrieve image orientation from first dataset (will return None if not present)
        imageOrientation = series[0].get('ImageOrientationPatient')

        return all(['ImageOrientationPatient' in d and 'ImagePositionPatient' in d and
                    d.ImageOrientationPatient == imageOrientation for d in series])
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
        # Retrieve image orientation from first dataset (will return None if not present)
        imageOrientation = series[0].PlaneOrientationSequence[0].get('ImageOrientationPatient')

        return all(['ImageOrientationPatient' in d.PlaneOrientationSequence[0] and
                    d.PlaneOrientationSequence[0].ImageOrientationPatient == imageOrientation and
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
            and any([series[0].ImageOrientationPatient != d.ImageOrientationPatient or
                     series[0].ImagePositionPatient != d.ImagePositionPatient for d in series]):
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


def getZPositionsFromPatientInfo(series):
    """Calculates slice location from the Image Orientation/Position fields

    This function is used for the :obj:`MethodType.PatientLocation` and :obj:`MethodType.MFPatientLocation` methods. It
    calculates the slice location for the Image Orientation (Patient) and Image Position (Patient) fields in the DICOM
    header. For multi-frame images, the same fields are used but they are stored elsewhere in the frame functional
    group.

    Parameters
    ----------
    series : Series

    Raises
    ------
    TypeError
        If the series is empty containing no datasets

    Returns
    -------
    list(float)
        Return value is a list of length N where N is the number of datasets present in the series with each value
        being the Z position
    """
    if len(series) == 0:
        raise TypeError('Series must contain at least one dataset')

    # We assume that the image orientations are the same throughout the entire series
    # This **should** be checked before calling this function (such as in isMethodValid)
    if series.isMultiFrame:
        imageOrientation = series[0].PlaneOrientationSequence[0].ImageOrientationPatient
        imagePositions = [d.PlanePositionSequence[0].ImagePositionPatient for d in series]
    else:
        imageOrientation = series[0].ImageOrientationPatient
        imagePositions = [d.ImagePositionPatient for d in series]

    # Row cosines is first 3 elements, column cosines is last 3 elements of array
    rowCosines = np.array(imageOrientation[:3])
    colCosines = np.array(imageOrientation[3:])

    # Get cross product of row and column cosines (gets normal to row/column cosines)
    zCosines = np.cross(rowCosines, colCosines)

    # Okay, so here is a puzzling question that I do not know how I want to solve. What if there are multiple image orientations. In this case, I assume that's not going to happen and just use the first one. But do I do the same thing for the multi-frame DICOM as well. Is that a safe bet?
    #
    # One instance that I can think of is if a series contains multiple orientations. But, the thing about that is I probably wouldn't try to combine these. Well, yes I would, but just based on stack ID I guess, right?
    # In that case, I would use sortSlices for StackID, then some sort of split command to split the series into multiple
    # based on that parameter?
    #
    # If I am sorting based on position, which is what this function is used for. Then I don't see any reason why different orientations would be used because I **don't** know how you would even piece those together.
    #
    # Maybe on that note, I should change isMethodValid to include a check for that.
    #
    # Well shoot, what about we combining slices, we need that slice orientation somehow. Do we just assume that the slice orientation is the same?
    #
    # on that note, it's just the same as checking pixel spacing and such. Do we just assume that is the same all the way throughout for all images? Do we check it somewhere?
    #
    # So, I'm thinking maybe a function like checkPatientLocation() that will verify they are all the same or throws an Exception/warning. That will be called in sortSlices, well maybe not. I hate to call it multiple times, you know? Not sure..

    # Functions I would like to create:
    # splitSeries (opposite to merge)
    # preflatten? Basically find changes in key info between each dataset and see which one to accept
    # flatten - With changes done by preflatten, it will basically take and merge two datasets into one
    #   Does nothing for standard DICOM I don't think. But for multiframe, it'll create/update 3D volume for parent and update any parents that have been flattened and such. Sort of a way to merge two multiframe datasets
    # Some sort of function to take a 3D volume and update the data on it.

    # Slice location is dot product of slice cosines and the image patient position
    return [np.dot(zCosines, position) for position in imagePositions]


def datasetDeleteOrRemove(dataset, key, value):
    """Delete key from dataset if value is None, otherwise set key to value

    Parameters
    ----------
    dataset : Dataset
    key : str
    value : Object
    """

    if value is not None:
        dataset[key] = value
    elif key in dataset:
        del dataset[key]


def getSpacingDims(coordinates, warn=True):
    """Takes 2D list of coordinates and returns dimensional size and spacing

    :obj:`coordinates` is a 2D list where the internal lists represent the coordinate for a given dimension. An example
    setup for the variable for a 2D image would be [[x1, x2, x3], [y1, y2, y3]] where x/y are each coordinate pair.

    The coordinates should be in order such that the last dimension varies the quickest.

    Since the math can be confusing within the function, a simple example will be given to demonstrate exactly how the
    function works. The following is our example where each column would be a list and the three columns would be
    combined into the coordinates list.
        1 2.5 10
        1 2.5 20
        1 2.5 30
        1 2.5 40
        1 2.5 50
        1 5.0 10
        1 5.0 20
        1 5.0 30
        1 5.0 40
        1 5.0 50
        1 7.5 10
        1 7.5 20
        1 7.5 30
        1 7.5 40
        1 7.5 50
        2 2.5 10
        2 2.5 20
        2 2.5 30
        2 2.5 40
        2 2.5 50
        2 5.0 10
        2 5.0 20
        2 5.0 30
        2 5.0 40
        2 5.0 50
        2 7.5 10
        2 7.5 20
        2 7.5 30
        2 7.5 40
        2 7.5 50

    The final result in this example is a dimensional size of 2x3x5 with spacing of 1, 2.5 and 10.

    Parameters
    ----------
    coordinates : list(list(float))
        2D list where the first list contains a list of coordinates for each dimension
    warn : bool, optional
        Whether to warn or raise an exception for non-uniform grid spacing

    Returns
    -------
    list(int), list(float)
        First element of tuple is the dimensions and second element is the spacing per dimension
    """

    # Total number of indices, for instance above this is 2 * 3 * 5 = 30
    total = len(coordinates[0])

    # Spacing and dimensions that will store results
    shape = []
    spacing = []

    # Loop through each list in coordinates (in example, there is 3 lists)
    for x in coordinates:
        # Difference between each preceding element
        # For the second column, this would be:
        #    [0, 0, 0, 0, 2.5, 0, 0, 0, 0, 2.5, 0, 0, 0, 0, -5.0, ...]
        diffs = np.diff(x)

        # Location of non-zero elements
        # For second column, this would be:
        #    [4, 9, 14, 19, 24]
        nzIndices = np.argwhere(diffs != 0).flatten()

        # The number of indices between non-zero elements should be uniform so we check this
        # by taking the difference between elements and check they are close (may be a small bit off due to rounding)
        # Check for even spacing in this dimension, between each non-zero index should be
        # nzIndicesDiff will be [5, 5, 5, 5] which are all the same as expected!
        if len(nzIndices) > 1:
            nzIndicesDiff = np.diff(nzIndices)
            if not np.allclose(nzIndicesDiff, nzIndicesDiff[0], atol=0.0, rtol=0.01):
                if warn:
                    logger.warning('Dims are not uniform, greater than 1% tolerance')
                    logger.debug('Dimension #%i key values: %s' % (coordinates.index(x) + 1, x))
                    logger.debug('Location of non-zero changes in: %s' % nzIndices)
                    logger.debug('Spacing Differences: %s' % nzIndicesDiff)
                else:
                    logger.debug('Dimension #%i key values: %s' % (coordinates.index(x) + 1, x))
                    logger.debug('Location of non-zero changes in: %s' % nzIndices)
                    logger.debug('Spacing Differences: %s' % nzIndicesDiff)
                    raise Exception('Dims are not uniform, greater than 1% tolerance')
        elif len(nzIndices) == 0:
            # No nonzero indices means no changes in coordinate occurred, hence a size of 1
            # Guess that means the spacing is 0? Really it's undefined
            shape.append(1)
            spacing.append(0)
            continue

        # Since we know all the indices spacing is the same, just grab the first one
        # This is 5 in the case of the second dimension
        # TODO May want to consider taking an average of all values in case there are small differences?
        # Not sure I see a direct need to do this now
        numNZIndices = nzIndices[0] + 1

        # Dimension will be total / numNZIndices
        # This is 15 / 5 = 3 for the second dimension
        # As noted below, the total will be overridden with the numNZIndices of the previous run
        shape.append(total // numNZIndices)

        # Retrieve the amount of change between each transition
        # Will be the following for second dimension:
        #    2.5, 2.5, 2.5, 2.5, -5.0
        stepAmount = diffs[nzIndices]

        # The pattern for the step amount is as follows:
        # The spacing value is repeated (dim size - 1) times followed by
        # a -(dim size - 1) * spacing value result where it is transitioning from the maximum dimension size to the
        # minimum size.
        # We retrieve the spacing value first and then validate this pattern is followed
        spacing.append(stepAmount[0])

        # Start with an array like the step amount with all of the spacing values
        expectedStepAmount = spacing[-1] * np.ones_like(stepAmount)

        # Then set every Nth element to be -(dim size - 1) * spacing where N is the size of that dimension
        expectedStepAmount[shape[-1] - 1::shape[-1]] = -(shape[-1] - 1) * spacing[-1]

        # Verify step amount and expected step amount are close, if not there was a problem
        if not np.allclose(stepAmount, expectedStepAmount, atol=0.0, rtol=0.1):
            if warn:
                logger.warning('Spacing is not uniform, greater than 10% tolerance')
                logger.debug('Dimension #%i key values: %s' % (coordinates.index(x) + 1, x))
                logger.debug('Location of non-zero changes in: %s' % nzIndices)
                logger.debug('Step amount at each transition: %s' % stepAmount)
                logger.debug('Expected step amounts at each transition: %s' % expectedStepAmount)
                logger.debug('Shape is %i, spacing is %f' % (shape[-1], spacing[-1]))
            else:
                logger.debug('Dimension #%i key values: %s' % (coordinates.index(x) + 1, x))
                logger.debug('Location of non-zero changes in: %s' % nzIndices)
                logger.debug('Step amount at each transition: %s' % stepAmount)
                logger.debug('Expected step amounts at each transition: %s' % expectedStepAmount)
                logger.debug('Shape is %i, spacing is %f' % (shape[-1], spacing[-1]))
                raise Exception('Spacing is not uniform, greater than 10% tolerance')

        # Finish by setting total number of elements to the number of nonzero indices
        total = numNZIndices

    # If the last number of nonzero indices is not one, meaning that the coordinates change each time, then this
    # indicates that there are duplicate slices
    if numNZIndices != 1:
        if warn:
            logger.warning('Datasets are not unique in dimensional space. Duplicate keys present. Try again with '
                           'additional sorting methods')
            logger.debug('Dimension #%i key values: %s' % (len(coordinates), coordinates[-1]))
            logger.debug('Differences in key values: %s' % diffs)
            logger.debug('Number of non-zero changes: %i' % numNZIndices)
            logger.debug('Location of non-zero changes in: %s' % nzIndices)
        else:
            logger.debug('Dimension #%i key values: %s' % (len(coordinates), coordinates[-1]))
            logger.debug('Differences in key values: %s' % diffs)
            logger.debug('Number of non-zero changes: %i' % numNZIndices)
            logger.debug('Location of non-zero changes in: %s' % nzIndices)
            raise Exception('Datasets are not unique in dimensional space. Duplicate keys present. Try again with '
                            'additional sorting methods')

    return shape, spacing
