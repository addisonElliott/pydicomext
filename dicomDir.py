from pydicom.dataset import Dataset

from .patient import Patient


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

    # def __str__(self):
    #     x = 'Patients:\n'

    #     for UID, patient in self:
    #         x += 'Patient %s:'
    #         pass

    #     return super().__str__()

    # def __repr__(self):
    #     return super().__repr__()
