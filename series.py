from .util import *


class Series(list):
    def __init__(self, DCMImage=None):
        if DCMImage:
            self.ID = DCMImage.get('SeriesInstanceUID')
            self.Date = DCMImage.get('SeriesDate')
            self.Time = DCMImage.get('SeriesTime')
            self.Description = DCMImage.get('SeriesDescription')
            self.Number = DCMImage.get('SeriesNumber')
        else:
            self.ID = None
            self.Date = None
            self.Time = None
            self.Description = None
            self.Number = None

        self.method = MethodType.Unknown
        self.type = VolumeType.Unknown

        list.__init__(self)

    # TODO Consider a function that tells best method type and volume type of this
    # TODO Issues with printing out large datasets, fix this
