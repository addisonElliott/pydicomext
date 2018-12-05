from .util import *


class Series(list):
    def __init__(self, DCMImage=None):
        if DCMImage:
            self.ID = DCMImage.get('SeriesInstanceUID')
            self.date = DCMImage.get('SeriesDate')
            self.time = DCMImage.get('SeriesTime')
            self.description = DCMImage.get('SeriesDescription')
            self.number = DCMImage.get('SeriesNumber')
        else:
            self.ID = None
            self.date = None
            self.time = None
            self.description = None
            self.number = None

            # TODO Store scan information here too?

        list.__init__(self)

    def __str__(self):
        return """Series %s
    Date: %s
    Time: %s
    Desc: %s
    Number: %i
    [%i datasets]""" % (self.ID, self.date, self.time, self.description, self.number, len(self))

    def __repr__(self):
        return self.__str__()

    # TODO Consider a function that tells best method type and volume type of this

