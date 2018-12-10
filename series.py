from .util import *


class Series(list):
    def __init__(self, datasets=None, dataset=None):
        if dataset:
            self.ID = dataset.get('SeriesInstanceUID')
            self.date = dataset.get('SeriesDate')
            self.time = dataset.get('SeriesTime')
            self.description = dataset.get('SeriesDescription')
            self.number = dataset.get('SeriesNumber')
        else:
            self.ID = None
            self.date = None
            self.time = None
            self.description = None
            self.number = None

        # Stores whether we have multi frame data and whether we have only multi frame data
        self._isMultiFrame = False

        # Stores sort information if this series is ever sorted
        self._shape = None
        self._spacing = None
        self._methods = None

        list.__init__(self)

        # Add items to the list
        if datasets:
            self.extend(datasets)

    def loadMultiFrame(self):
        # Reset to original value
        self._isMultiFrame = False

        for dataset in self:
            # Use NumberOfFrames as indicator of whether the dataset is multi-frame or not
            # If this is present, we **assume** that Per-frame Functional Groups Sequence is present
            if 'NumberOfFrames' not in dataset:
                continue

            # The first instance of a multiframe series sets this true
            self._isMultiFrame = True

            # Loop through each frame dataset and save to list
            for x, frameDataset in enumerate(dataset.PerFrameFunctionalGroupsSequence):
                # Append pointer to parent dataset and slice index
                frameDataset.parent = dataset
                frameDataset.sliceIndex = x

                self.append(frameDataset)

            # Save the parent dataset and remove from list
            self.remove(dataset)

    def checkIsMultiFrame(self):
        # Check all datasets for the parent attribute, if any are present, then we have multiframe data
        self._isMultiFrame = any([hasattr(dataset, 'parent') for dataset in self])

    @property
    def isMultiFrame(self):
        return self._isMultiFrame

    @property
    def shape(self):
        return self._shape

    @property
    def spacing(self):
        return self._spacing

    @property
    def sortMethods(self):
        return self._methods

    def clearSeries(self):
        self.ID = None
        self.date = None
        self.time = None
        self.description = None
        self.number = None

    def update(self, ID, date=None, time=None, description=None, number=None, startNewIndex=0):
        # Series instance ID is required and must be known
        if ID is None:
            return

        multiFrameParents = []

        for dataset in self[startNewIndex:]:
            # Check for multiframe datasets, will update the parent dataset
            if hasattr(dataset, 'parent'):
                # If we have already handled this multiframe parent, then skip
                if dataset.parent in multiFrameParents:
                    continue

                # Otherwise, set dataset to be the parent and append to list so we dont do this again
                dataset = dataset.parent
                multiFrameParents.append(dataset)

            # Update fields in dataset, remove optional ones if value is None
            dataset.SeriesInstanceUID = ID
            datasetDeleteOrRemove(dataset, 'SeriesDate', date)
            datasetDeleteOrRemove(dataset, 'SeriesTime', time)
            datasetDeleteOrRemove(dataset, 'SeriesDescription', description)
            datasetDeleteOrRemove(dataset, 'SeriesNumber', number)

    def isMethodValid(method):
        """Determines if a method is valid for sorting/combining this series

        Checks if a given method is available for sorting or combining this series. This checks the DICOM header of each
        dataset in the series for the specified tag based on the method given.

        Parameters
        ----------
        method : MethodType
            Method to check

        Raises
        ------
        TypeError
            If invalid method is given or if the series is empty

        Returns
        -------
        bool
            True if the method is a valid method of sorting/combining this series, False otherwise
        """
        return isMethodValid(self, method)

    def getBestMethods(self):
        """Select best method to use for sorting/combining datasets in this series

        Raises
        ------
        TypeError
            If unable to find the best method or if the series is empty

        Returns
        -------
        list(MethodType)
            Return list of best method type to use
        """
        return getBestMethods(self)

    @property
    def volumeType(self):
        return getTypeFromMethods(self._methods) if self._methods else VolumeType.Unknown

    @property
    def isSpatial(self):
        return self.volumeType() & VolumeType.Spatial

    @property
    def isTemporal(self):
        return self.volumeType() & VolumeType.Temporal

    def sort(self, methods=MethodType.Unknown, reverse=False, squeeze=False, warn=True, shapeTolerance=0.01,
             spacingTolerance=0.1):
        """Sorts datasets in series based on its metadata

        Sorting the datasets within the series can be done based on a number of parameters, which are primarily going
        to be spatial or temporal based.

        Parameters
        ----------
        method : MethodType or list(MethodType), optional
            A single method or a list of methods to use when sorting the series. If this is :obj:`MethodType.Unknown`,
            then the best methods will be retrieved based on the datasets metadata. If a list of methods are given,
            then the series is sorted in order from left to right of the methods. This in effect will create
            multidimensional series (the default is MethodType.Unknown which will retrieve the best methods based on
            the series)
        reverse : bool, optional
            Whether or not to reverse the sort, where the default sorting order is ascending (the default is False)
        squeeze : bool, optional
            Whether to remove unnecessary dimensions of size 1 (default is False, meaning dimensions are untouched). The
            resulting methods and spacing will be updated accordingly to remove unnecessary dimensions of size 1.
        warn : bool, optional
            Whether to warn or raise an exception for non-uniform grid spacing (default is True which will display
            warnings rather than exceptions)
        """

        return sortSeries(self, methods, reverse, squeeze, warn, shapeTolerance, spacingTolerance)

    def getSliceSpacingThickness(self):
        """Return the slice spacing and slice thickness in the series

        This function will obtain the slice spacing (0018, 0088) and slice thickness (0018, 0050) from the DICOM
        metadata. If there are different slice spacings and/or thicknesses, then an array of the different values
        will be returned.

        Returns
        -------
        float or (M,) numpy.ndarray, float or (N,) numpy.ndarray
            Slice thickness from series. Will return a single number if all of the series have the same value,
            otherwise an array of the unique values are given.
        float or (N,) numpy.ndarray
            Spacing between slices from series. Will return a single number if all of the series have the same value,
            otherwise an array of the unique values are given.
        """

        # Empty lists for the thickness and slice spacings for each series
        imageThicknesses = []
        imageSliceSpacings = []

        # Retrieve the slice spacing and slice thickness for each series
        # Note: This information is located in different spots if the image is multi-frame
        # If the slice thickness or spacing is not available in that series, then it will be set to -1
        # This should allow the user to tell if there is missing data because a negative thickness or spacing is invalid
        if self.isMultiFrame:
            for dataset in self:
                imageThicknesses.append(dataset.PixelMeasuresSequence[0].SliceThickness if 'SliceThickness' in
                                        dataset.PixelMeasuresSequence[0] else -1.0)
                imageSliceSpacings.append(dataset.PixelMeasuresSequence[0].SpacingBetweenSlices if
                                          'SpacingBetweenSlices' in dataset.PixelMeasuresSequence[0] else -1.0)
        else:
            for dataset in self:
                imageThicknesses.append(dataset.SliceThickness if 'SliceThickness' in dataset else -1.0)
                imageSliceSpacings.append(dataset.SpacingBetweenSlices if 'SpacingBetweenSlices' in
                                          dataset else -1.0)

        # Retrieve a list of unique image thicknesses from the series'
        # If there is only one item in the array, they all have the same thickness and we will just return that
        imageThickness = np.unique(imageThicknesses)
        if len(imageThickness) == 1:
            imageThickness = imageThickness[0]

        # Retrieve a list of unique image slice spacings from the series'
        # If there is only one item in the array, they all have the same slice spacing and we will just return that
        imageSliceSpacing = np.unique(imageSliceSpacings)
        if len(imageSliceSpacing) == 1:
            imageSliceSpacing = imageSliceSpacing[0]

        return imageThickness, imageSliceSpacing

    def __str__(self):
        return """Series %s
    Date: %s
    Time: %s
    Desc: %s
    Number: %s
    [%i datasets]%s""" % (self.ID, self.date, self.time, self.description, self.number, len(self),
                          (' (Multi-frame)' if self.isMultiFrame else ''))

    def __repr__(self):
        return self.__str__()


from .sortSeries import sortSeries
