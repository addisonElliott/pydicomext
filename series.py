from .util import *


class Series(list):
    def __init__(self, dataset=None):
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

        list.__init__(self)

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

    def checkPatientOrientation(self):
        if self.isMultiFrame():
            imageOrientation = self[0].PlaneOrientationSequence[0].get('ImageOrientationPatient')
            any([d.PlaneOrientationSequence[0].get('ImageOrientationPatient') != imageOrientation for d in self])
            pass
        else:
            pass
        pass

    def __str__(self):
        return """Series %s
    Date: %s
    Time: %s
    Desc: %s
    Number: %i
    [%i datasets]%s""" % (self.ID, self.date, self.time, self.description, self.number, len(self),
                          (' (Multi-frame)' if self.isMultiFrame else ''))

    def __repr__(self):
        return self.__str__()

    # TODO Consider a function that tells best method type and volume type of this