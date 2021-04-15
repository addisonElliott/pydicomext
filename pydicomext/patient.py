from pydicom.dataset import Dataset

from pydicomext.study import Study


class Patient(dict):
    def __init__(self, DCMImage=None):
        if DCMImage:
            self.name = DCMImage.get('PatientName')
            self.ID = DCMImage.get('PatientID')
            self.issuerOfID = DCMImage.get('IssuerOfPatientID')
            self.birthDate = DCMImage.get('PatientBirthDate')
            self.birthTime = DCMImage.get('PatientBirthTime')
            self.sex = DCMImage.get('PatientSex')
            self.otherIDs = DCMImage.get('OtherPatientIDs')
            self.otherNames = DCMImage.get('OtherPatientNames')
            self.age = DCMImage.get('PatientAge')
            self.size = DCMImage.get('PatientSize')
            self.weight = DCMImage.get('PatientWeight')
            self.ethnicGroup = DCMImage.get('EthnicGroup')
            self.comments = DCMImage.get('PatientComments')
            self.identityRemoved = DCMImage.get('PatientIdentityRemoved')
            self.position = DCMImage.get('PatientPosition')
        else:
            self.name = None
            self.ID = None
            self.issuerOfID = None
            self.birthDate = None
            self.birthTime = None
            self.sex = None
            self.otherIDs = None
            self.otherNames = None
            self.age = None
            self.size = None
            self.weight = None
            self.ethnicGroup = None
            self.comments = None
            self.identityRemoved = None
            self.position = None

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
            raise TypeError('Can only add study or DICOM image to Patient dictionary')

    def only(self):
        if len(self) != 1:
            raise TypeError('More than one study is available')

        return next(iter(self.values()))

    def __str__(self):
        str_ = """Patient %s
    Name: %s
    Issuer of ID: %s
    Birth Date: %s
    Birth Time: %s
    Sex: %s
    Other IDs: %s
    Other Names: %s
    Age: %s
    Size: %s
    Weight: %s
    Ethnic Group: %s
    Comments: %s
    Identity Removed: %s
    Position: %s
    Studies:
""" % (self.ID, self.name, self.issuerOfID, self.birthDate, self.birthTime, self.sex, self.otherIDs, self.otherNames,
            self.age, self.size, self.weight, self.ethnicGroup, self.comments, self.identityRemoved, self.position)

        for _, study in self.items():
            str_ += '\t\t' + str(study).replace('\n', '\n\t\t') + '\n'

        return str_

    def __repr__(self):
        return self.__str__()
