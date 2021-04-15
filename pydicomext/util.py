from enum import IntFlag, Enum, auto
import logging
import numpy as np

logger = logging.getLogger(__name__)


class VolumeType(IntFlag):
    Unknown = 0
    Spatial = auto()
    Temporal = auto()
    SpatioTemporal = Spatial | Temporal


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

    @property
    def isMultiFrame(self):
        return self.value >= self.StackID.value


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


def getTypeFromMethods(methods):
    """Retrieve the volume type based on the methods used for sorting

    A volume can be spatial, temporal or spatiotemporal. Depending on the methods used to sort the series, this
    function determines the volume type.

    Parameters
    ----------
    methods : MethodType, list(MethodType)
        A single method or a list of methods used to sort a series

    Returns
    -------
    VolumeType
        Volume type based on the given methods
    """

    # Make a list out of the method if it is not one
    if not isinstance(methods, list):
        methods = [methods]

    # Starting volume type
    volumeType = VolumeType.Unknown

    # Loop through all methods and if its spatial or temporal, add that
    for method in methods:
        if method in [MethodType.SliceLocation, MethodType.PatientLocation, MethodType.StackPosition,
                      MethodType.FrameAcquisitionNumber, MethodType.MFPatientLocation]:
            volumeType |= VolumeType.Spatial
        elif method in [MethodType.TriggerTime, MethodType.AcquisitionDateTime, MethodType.TemporalPositionIndex,
                        MethodType.MFAcquisitionDateTime, MethodType.CardiacTriggerTime, MethodType.CardiacPercentage]:
            volumeType |= VolumeType.Temporal

    return volumeType


def getBestMethods(series):
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

    methods = []

    if series.isMultiFrame:
        # Check for stack ID
        if isMethodValid(series, MethodType.StackID) and \
                any([series[0].FrameContentSequence[0].StackID != d.FrameContentSequence[0].StackID for d in series]):
            methods.append(MethodType.StackID)

        # Check for stack position, patient location or frame acquisition number
        if isMethodValid(series, MethodType.MFPatientLocation) and \
                any([series[0].PlanePositionSequence[0].ImagePositionPatient !=
                     d.PlanePositionSequence[0].ImagePositionPatient for d in series]):
            methods.append(MethodType.MFPatientLocation)
        elif isMethodValid(series, MethodType.StackPosition) and \
                any([series[0].FrameContentSequence[0].InStackPositionNumber !=
                     d.FrameContentSequence[0].InStackPositionNumber for d in series]):
            methods.append(MethodType.StackPosition)
        elif isMethodValid(series, MethodType.FrameAcquisitionNumber) and \
                any([series[0].FrameContentSequence[0].FrameAcquisitionNumber !=
                     d.FrameContentSequence[0].FrameAcquisitionNumber for d in series]):
            methods.append(MethodType.FrameAcquisitionNumber)

        # Check for cardiac trigger time, acquisition date time, temporal position index or cardiac percentage
        if isMethodValid(series, MethodType.CardiacTriggerTime) and \
                any([series[0].CardiacSynchronizationSequence[0].NominalCardiacTriggerDelayTime !=
                     d.CardiacSynchronizationSequence[0].NominalCardiacTriggerDelayTime for d in series]):
            methods.append(MethodType.CardiacTriggerTime)
        elif isMethodValid(series, MethodType.MFAcquisitionDateTime) and \
                any([series[0].FrameContentSequence[0].FrameAcquisitionDateTime !=
                     d.FrameContentSequence[0].FrameAcquisitionDateTime for d in series]):
            methods.append(MethodType.MFAcquisitionDateTime)
        elif isMethodValid(series, MethodType.TemporalPositionIndex) and \
                any([series[0].FrameContentSequence[0].TemporalPositionIndex !=
                     d.FrameContentSequence[0].TemporalPositionIndex for d in series]):
            methods.append(MethodType.TemporalPositionIndex)
        elif isMethodValid(series, MethodType.CardiacPercentage) and \
                any([series[0].CardiacSynchronizationSequence[0].NominalPercentageOfCardiacPhase !=
                     d.CardiacSynchronizationSequence[0].NominalPercentageOfCardiacPhase for d in series]):
            methods.append(MethodType.CardiacPercentage)
    else:
        # Check for either patient location or slice location
        if isMethodValid(series, MethodType.PatientLocation) and \
                any([series[0].ImagePositionPatient != d.ImagePositionPatient for d in series]):
            methods.append(MethodType.PatientLocation)
        elif isMethodValid(series, MethodType.SliceLocation) and \
                any([series[0].SliceLocation != d.SliceLocation for d in series]):
            methods.append(MethodType.SliceLocation)

        # Check for trigger time or acquisition date time
        if isMethodValid(series, MethodType.TriggerTime) \
                and any([series[0].TriggerTime != d.TriggerTime for d in series]):
            methods.append(MethodType.TriggerTime)
        elif isMethodValid(series, MethodType.AcquisitionDateTime) \
                and any([series[0].AcquisitionDateTime != d.AcquisitionDateTime for d in series]):
            methods.append(MethodType.AcquisitionDateTime)

        # If nothing has worked until now, try image number
        if len(methods) == 0 and isMethodValid(series, MethodType.ImageNumber) \
                and any([series[0].InstanceNumber != d.InstanceNumber for d in series]):
            methods.append(MethodType.ImageNumber)

    if len(methods) == 0:
        raise TypeError('Unable to find best method')

    return methods


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

    # Slice location is dot product of slice cosines and the image patient position
    return [np.dot(zCosines, position) for position in imagePositions]


def datasetUpdateOrRemove(dataset, key, value):
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


def getSpacingDims(coordinates, warn=True, shapeTolerance=0.01, spacingTolerance=0.10):
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
    shapeTolerance : float, optional
        Amount of relative tolerance to allow between the shape. Default value is 1% (0.01) which should be sufficient
        in most cases. There should not be much deviation in the shape or else the volume cannot be combined easily.

        Note: Only the first shape calculated is used but this tolerance is used to verify that the shape is similar to
        all others.
    spacingTolerance : float, optional
        Amount of relative tolerance to allow between the spacing. Default value is 10% (0.10) which should be
        sufficient in most cases. However, there are instances where the coordinates have non-uniform spacing
        in which case the tolerance should be increased if the user verifies everything is alright.

        Note: Only the first spacing calculated is used but this tolerance is used to verify that spacing is similar to
        all others.

    Returns
    -------
    list(int)
        List of shapgee of each dimension
    list(float)
        List of spacing per dimension
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
            if not np.allclose(nzIndicesDiff, nzIndicesDiff[0], atol=0.0, rtol=shapeTolerance):
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
        if not np.allclose(stepAmount, expectedStepAmount, atol=0.0, rtol=spacingTolerance):
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
