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

    def isMethodAvailable(self, method):
        """
        Checks if a given method is available from the dataset in the class. This checks the DICOM header for specified
        tags for each of the DICOM images.

        :param method: Method to check whether it is available. Must be option from VolumeType
        :return: Returns true if method is available in dataset, otherwise it returns false
        """

        if method == MethodType.TriggerTime:
            return all(['TriggerTime' in d for d in self])
        elif method == MethodType.AcquisitionDateTime:
            return all(['AcquisitionTime' in d for d in self])
        elif method == MethodType.ImageNumber:
            return all(['ImageNumber' in d for d in self])
        elif method == MethodType.SliceLocation:
            return all(['SliceLocation' in d for d in self])
        elif method == MethodType.PatientLocation:
            return all(['ImageOrientationPatient' in d and 'ImagePositionPatient' in d for d in self])
        else:
            raise TypeError('Invalid method specified')

    def getBestType(self):
        """
        Select the best method to use for combining the slices in the dataset. The methods are checked in the following
        order:
            SliceLocation, PatientLocation, TriggerTime, AcquisitionTime, ImageNumber
        Thus, it follows that the slices are checked for spatial differences first before temporal differences. This
        yields the best results because spatial slices can still be acquired at different times and not be considered a
        time series.

        :return: Returns MethodType value representing the best method to use for combining slices
        """
        self.type = VolumeType.Unknown
        self.method = MethodType.Unknown

        if self.isMethodAvailable(MethodType.SliceLocation) \
                and any([self[0].SliceLocation != d.SliceLocation for d in self]):
            self.type = VolumeType.Spatial
        elif self.isMethodAvailable(MethodType.PatientLocation) \
                and any([self[0].ImageOrientationPatient != d.ImageOrientationPatient
                         or self[0].ImagePositionPatient != d.ImagePositionPatient for d in self]):
            self.type = VolumeType.Spatial
        elif self.isMethodAvailable(MethodType.TriggerTime) \
                and any([self[0].TriggerTime != d.TriggerTime for d in self]):
            self.type = VolumeType.Temporal
        elif self.isMethodAvailable(MethodType.AcquisitionDateTime) \
                and any([self[0].AcquisitionTime != d.AcquisitionTime for d in self]):
            self.type = VolumeType.Temporal
        elif self.isMethodAvailable(MethodType.ImageNumber) \
                and any([self[0].ImageNumber != d.ImageNumber for d in self]):
            pass
        else:
            raise TypeError('Unable to find best method')

    def getType(self, method=MethodType.Unknown):
        # If no images in series, this return False since it is not temporal
        if len(self) == 0:
            return None

        if method == MethodType.Unknown:
            self.getBestType()
        elif not self.isMethodAvailable(method):
            raise TypeError('Invalid method specified')

        return self.type

    def isTemporal(self, method=MethodType.Unknown):
        return self.getType(method) == VolumeType.Temporal

    def isSpatial(self, method=MethodType.Unknown):
        return self.getType(method) == VolumeType.Spatial
