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

        # TODO Investigate whether saving parent pointer is wise, may not be most efficient
        # I want it store as a pointer
        self._multiFrameData = []
        self._onlyMultiFrames = False

        list.__init__(self)

    def loadMultiFrame(self):
        # Reset to original values
        self._multiFrameData.clear()
        self._onlyMultiFrames = False

        for dataset in self:
            # Use NumberOfFrames as indicator of whether the dataset is multi-frame or not
            # If this is present, we **assume** that Per-frame Functional Groups Sequence is present
            if 'NumberOfFrames' not in dataset:
                self._onlyMultiFrames = True
                continue

            # Loop through each frame dataset and save to list
            for x, frameDataset in enumerate(dataset.PerFrameFunctionalGroupsSequence):
                # Append pointer to parent dataset and slice index
                frameDataset.parent = dataset
                frameDataset.sliceIndex = x

                self.append(frameDataset)

            # Save the parent dataset and remove from list
            self._multiFrameData.append(dataset)
            self.remove(dataset)

    @property
    def isMultiFrame(self):
        return len(self._multiFrameData) > 0

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

        # Loop through data (if there are frames besides only multi frame data)
        if not self._onlyMultiFrames:
            for dataset in self[startNewIndex:]:
                # Skip datasets from multiframe, will check parent dataset later
                if hasattr(dataset, 'parent'):
                    continue

                # Update fields in dataset, remove optional ones if value is None
                dataset.SeriesInstanceUID = ID
                datasetDeleteOrRemove(dataset, 'SeriesDate', date)
                datasetDeleteOrRemove(dataset, 'SeriesTime', time)
                datasetDeleteOrRemove(dataset, 'SeriesDescription', description)
                datasetDeleteOrRemove(dataset, 'SeriesNumber', number)

        for dataset in self._multiFrameData:
            # Update fields in dataset, remove optional ones if value is None
            dataset.SeriesInstanceUID = ID
            datasetDeleteOrRemove(dataset, 'SeriesDate', date)
            datasetDeleteOrRemove(dataset, 'SeriesTime', time)
            datasetDeleteOrRemove(dataset, 'SeriesDescription', description)
            datasetDeleteOrRemove(dataset, 'SeriesNumber', number)

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