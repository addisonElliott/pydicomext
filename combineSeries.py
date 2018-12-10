import numpy as np
import pydicom

from .util import *

pydicom.config.datetime_conversion = True


def combineSeries(series, methods=MethodType.Unknown, reverse=False, squeeze=False, warn=True, shapeTolerance=0.01,
                  spacingTolerance=0.1):
    """
    Combines the given dataset for Volume into a 3D volume. In addition, some parameters for the volume are
    calculated, such as:
        Origin, spacing, coordinate system, and orientation.
    """

    if series._shape is None:
        series = series.sort(methods, reverse, squeeze, warn, shapeTolerance, spacingTolerance)
    elif len(series) == 0:
        raise TypeError('Series must contain at least one dataset')

    imageShapes = []
    imageSpacings = []
    imageThicknesses = []
    imageSliceSpacings = []
    imageOrientations = []
    images = []

    if series.isMultiFrame:
        for dataset in series:
            imageShapes.append(dataset.parent.pixel_array.shape[1:])
            imageSpacings.append(dataset.PixelMeasuresSequence[0].PixelSpacing if 'PixelSpacing' in
                                 dataset.PixelMeasuresSequence[0] else (1, 1))
            imageThicknesses.append(dataset.PixelMeasuresSequence[0].SliceThickness if 'SliceThickness' in
                                    dataset.PixelMeasuresSequence[0] else -1.0)
            imageSliceSpacings.append(dataset.PixelMeasuresSequence[0].SpacingBetweenSlices if 'SpacingBetweenSlices' in
                                      dataset.PixelMeasuresSequence[0] else -1.0)
            imageOrientations.append(dataset.PlaneOrientationSequence[0].ImageOrientationPatient)
            images.append(dataset.parent.pixel_array[dataset.sliceIndex, None, :, :])
    else:
        for dataset in series:
            imageShapes.append(dataset.pixel_array.shape)
            imageSpacings.append(dataset.PixelSpacing if 'PixelSpacing' in dataset else (1, 1))
            imageOrientations.append(dataset.ImageOrientationPatient)
            images.append(dataset.pixel_array[None, :, :])

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

    # TODO Document me, maybe make separate function?
    imageThickness = np.unique(imageThicknesses)
    if len(imageThickness) == 1:
        imageThickness = imageThickness[0]

    # TODO Document me
    imageSliceSpacing = np.unique(imageSliceSpacings)
    if len(imageSliceSpacing) == 1:
        imageSliceSpacing = imageSliceSpacing[0]

    # Tack on the multidimensional shape and spacing calculated from sort series
    # This is prepended because we are using C-ordering meaning slower varying indices come first
    imageShape = series.shape + imageShape
    imageSpacing = series.spacing + imageSpacing

    # Create 3D volume from stack of 2D images
    # Reshape the volume into the image shape
    volume = np.vstack(images)
    volume = volume.reshape(imageShape)

    # DICOM uses LPS space
    space = 'left-posterior-superior'

    # TODO Swap rows/columns of pixel array or give option to do this
    # Nope, we are going to use C-order indexing which is what pydicom abides by.
    # Thus, shape of image is (frame, row, col) or (frame, y, x)
    # This means any multidimensional info should be in front like:
    # (t, z, y, x)
    # Plenty of libraries in Python are using C-ordered indexing which Numpy defaults to so I want to stick with that.
    # A simple transpose and reversal of data will work.

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
