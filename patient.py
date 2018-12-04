from pydicom.dataset import Dataset

from .study import Study


class Patient(dict):
    def __init__(self, DCMImage=None):
        if DCMImage:
            self.Name = DCMImage.get('PatientName')
            self.ID = DCMImage.get('PatientID')
            self.IssuerOfID = DCMImage.get('IssuerOfPatientID')
            self.BirthDate = DCMImage.get('PatientBirthDate')
            self.BirthTime = DCMImage.get('PatientBirthTime')
            self.Sex = DCMImage.get('PatientSex')
            self.OtherIDs = DCMImage.get('OtherPatientIDs')
            self.OtherNames = DCMImage.get('OtherPatientNames')
            self.Age = DCMImage.get('PatientAge')
            self.Size = DCMImage.get('PatientSize')
            self.Weight = DCMImage.get('PatientWeight')
            self.EthnicGroup = DCMImage.get('EthnicGroup')
            self.Comments = DCMImage.get('PatientComments')
            self.IdentityRemoved = DCMImage.get('PatientIdentityRemoved')
            self.Position = DCMImage.get('PatientPosition')
        else:
            self.Name = None
            self.ID = None
            self.IssuerOfID = None
            self.BirthDate = None
            self.BirthTime = None
            self.Sex = None
            self.OtherIDs = None
            self.OtherNames = None
            self.Age = None
            self.Size = None
            self.Weight = None
            self.EthnicGroup = None
            self.Comments = None
            self.IdentityRemoved = None
            self.Position = None

        dict.__init__(self)

    def add(self, var):
        if isinstance(var, Study):
            self[var.ID] = var
            return var
        elif isinstance(var, Dataset):
            study = Study(var)
            self[study.ID] = study
            return study
        else:
            raise TypeError("Can only add study or DICOM image to Patient dictionary")

    def study(self, ID):
        if ID is not None:
            return self[ID]

        return None

    def only(self):
        if len(self) != 1:
            raise TypeError('More than one study is available')

        return next(iter(self.values()))
