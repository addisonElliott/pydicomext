from pydicom.dataset import Dataset

from .series import Series


class Study(dict):
    def __init__(self, DCMImage=None):
        if DCMImage:
            self.ID = DCMImage.get('StudyInstanceUID')
            self.date = DCMImage.get('StudyDate')
            self.time = DCMImage.get('StudyTime')
            self.description = DCMImage.get('StudyDescription')
        else:
            self.ID = None
            self.date = None
            self.time = None
            self.description = None

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
            raise TypeError('Can only add series or DICOM image to Study dictionary')

    def only(self):
        if len(self) != 1:
            raise TypeError('More than one patient is available')

        return next(iter(self.values()))

    def __str__(self):
        str_ = """Study %s
    Date: %s
    Time: %s
    Desc: %s
    Series:
""" % (self.ID, self.date, self.time, self.description)

        for _, series in self.items():
            str_ += '\t\t\t' + str(series).replace('\n', '\n\t\t\t') + '\n'

        return str_

    def __repr__(self):
        return self.__str__()
