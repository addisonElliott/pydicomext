from pydicom.dataset import Dataset

from .patient import Patient


class Patients(dict):
    def add(self, var):
        if isinstance(var, Patient):
            self[var.ID] = var
            return var
        elif isinstance(var, Dataset):
            patient = Patient(var)
            self[patient.ID] = patient
            return patient
        else:
            raise TypeError("Can only add patient or DICOM image to Patients dictionary")

    def only(self):
        if len(self) != 1:
            raise TypeError('More than one patient is available')

        return next(iter(self.values()))
