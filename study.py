from pydicom.dataset import Dataset

from .series import Series


class Study(dict):
    def __init__(self, DCMImage=None):
        if DCMImage:
            self.ID = DCMImage.get('StudyInstanceUID')
            self.Date = DCMImage.get('StudyDate')
            self.Time = DCMImage.get('StudyTime')
            self.Description = DCMImage.get('StudyDescription')
        else:
            self.ID = None
            self.Date = None
            self.Time = None
            self.Description = None

        dict.__init__(self)

    def add(self, var):
        if isinstance(var, Series):
            self[var.ID] = var
            return var
        elif isinstance(var, Dataset):
            series = Series(var)
            self[series.ID] = series
            return series
        else:
            raise TypeError("Can only add series or DICOM image to Study dictionary")

    def series(self, ID):
        if ID is not None:
            return self[ID]

        return None

    def only(self):
        if len(self) != 1:
            raise TypeError('More than one patient is available')

        return next(iter(self.values()))
