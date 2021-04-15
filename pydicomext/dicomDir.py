from pydicom.dataset import Dataset

from pydicomext.patient import Patient


class DicomDir(dict):
    def add(self, var):
        if isinstance(var, Patient):
            self[var.ID] = var
            return var
        elif isinstance(var, Dataset):
            patient = Patient(var)
            self[patient.ID] = patient
            return patient
        else:
            raise TypeError('Can only add patient or DICOM image to DicomDir dictionary')

    def only(self):
        if len(self) != 1:
            raise TypeError('More than one patient is available')

        return next(iter(self.values()))

    def __str__(self):
        str_ = """DicomDir\n"""

        for _, patient in self.items():
            str_ += '\t' + str(patient).replace('\n', '\n\t') + '\n'

        return str_

    def __repr__(self):
        return self.__str__()
