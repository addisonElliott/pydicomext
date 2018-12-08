import numpy as np
import pydicom

from .sortSeries import sortSeries
from .util import *

pydicom.config.datetime_conversion = True


def combineSeries(series, methods=MethodType.Unknown, reverse=False, squeeze=False, warn=True, shapeTolerance=0.01,
                  spacingTolerance=0.01):
    """
    Combines the given dataset for Volume into a 3D volume. In addition, some parameters for the volume are
    calculated, such as:
        Origin, spacing, coordinate system, and orientation.
    """

    if series._shape is None:
        series = series.sort(methods, reverse, squeeze, warn, shapeTolerance, spacingTolerance)
    elif len(series) == 0:
        raise TypeError('Series must contain at least one dataset')

    if series.isMultiFrame:
        for dataset in series:
            pass

        return None
    else:
        imageShapes = []
        imageSpacings = []
        imageOrientations = []
        images = []

        for dataset in series:
            imageShapes.append(dataset.pixel_array.shape)
            imageSpacings.append(dataset.PixelSpacing)
            imageOrientations.append(dataset.ImageOrientationPatient)
            images.append(dataset.pixel_array)

        if not np.allclose(imageShapes, imageShapes[0], rtol=0.01):
            logger.debug('Datasets shape: %s' % imageShapes)
            raise Exception('Datasets do not have the same shape. Unable to combine into one volume')

        if not np.allclose(imageSpacings, imageSpacings[0], rtol=0.1):
            if warn:
                logger.warning('Datasets image spacing are not uniform')
                logger.debug('Datasets spacings: %s' % imageSpacings)
            else:
                logger.debug('Datasets spacings: %s' % imageSpacings)
                raise Exception('Datasets image spacing are not uniform')

        if not np.allclose(imageOrientations, imageOrientations[0], rtol=0.1):
            if warn:
                logger.warning('Datasets image orientation are not the same')
                logger.debug('Datasets orientations: %s' % imageOrientations)
            else:
                logger.debug('Datasets orientations: %s' % imageOrientations)
                raise Exception('Datasets image orientation are not the same')

        # Use the first values of datasets since we **assume** these are all the same
        imageShape = imageShapes[0]
        imageSpacing = imageSpacings[0]
        imageOrientation = imageOrientations[0]

        # Create 3D volume from stack of 2D images (will reshape this later into N-D data)
        volume = np.dstack(images)

    # DICOM uses LPS space
    space = 'left-posterior-superior'

    # TODO Swap rows/columns of pixel array or give option to do this

    # Row cosines is first 3 elements, column cosines is last 3 elements of array, compute z cosines from row/col
    rowCosines = np.array(imageOrientation[:3])
    colCosines = np.array(imageOrientation[3:])
    zCosines = np.cross(rowCosines, colCosines)

    # Orientation is combination of the three cosines direction matrix
    orientation = np.hstack((rowCosines, colCosines, zCosines))

    # # TODO Check that all of the images are the same size first!
    # # TODO Stack them together and reshape them
    # # TODO Get space, orientation, pixel spacing, origin all setup!
    # # TODO THink about reverse when doing this stuff
    # # TODO Create a Volume class that holds all this information!

    # # Get 3D volume from list of datasets
    # volume = np.dstack((x.pixel_array for x in sortedDataset))

    # space = 'left-posterior-superior'
    # # Append the Z cosines to image orientation and then resize into 3x3 matrix
    # orientation = np.append(np.asfarray(series[0].ImageOrientationPatient), sliceCosines).reshape((3, 3))
    # # Concatenate (x,y) spacing list and zSpacing list
    # spacing = np.append(np.asfarray(series[0].PixelSpacing), zSpacing)
    # origin = np.asfarray(series[0].ImagePositionPatient)

    # return method, space, orientation, spacing, origin, volume
    return Volume(volume, space, orientation)
