import numpy as np

from .sortSeries import sortSeries
from .util import *

pydicom.config.datetime_conversion = True


def combineSeries(series, method=MethodType.Unknown, reverse=False, squeeze=False, warn=True, shapeTolerance=0.01,
                  spacingTolerance=0.01):
    """
    Combines the given dataset for Volume into a 3D volume. In addition, some parameters for the volume are
    calculated, such as:
        Origin, spacing, coordinate system, and orientation.
    """

    if series._shape is None:
        series = series.sort(method, reverse, squeeze, warn, shapeTolerance, spacingTolerance)

    # TODO Check that all of the images are the same size first!
    # TODO Stack them together and reshape them
    # TODO Get space, orientation, pixel spacing, origin all setup!
    # TODO THink about reverse when doing this stuff
    # TODO Create a Volume class that holds all this information!

    # Get 3D volume from list of datasets
    volume = np.dstack((x.pixel_array for x in sortedDataset))

    space = 'left-posterior-superior'
    # Append the Z cosines to image orientation and then resize into 3x3 matrix
    orientation = np.append(np.asfarray(series[0].ImageOrientationPatient), sliceCosines).reshape((3, 3))
    # Concatenate (x,y) spacing list and zSpacing list
    spacing = np.append(np.asfarray(series[0].PixelSpacing), zSpacing)
    origin = np.asfarray(series[0].ImagePositionPatient)

    return method, space, orientation, spacing, origin, volume
