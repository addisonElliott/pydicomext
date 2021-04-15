import numpy as np
import pydicom

from pydicomext.util import *
from pydicomext.volume import Volume

pydicom.config.datetime_conversion = True


def combineSeries(series, methods=MethodType.Unknown, reverse=False, squeeze=False, warn=True, shapeTolerance=0.01,
                  spacingTolerance=0.1):
    """Combines a series into an N-D Numpy array and returns some information about the volume

    Many of the parameters are from the :meth:`sortSeries` function which this function will call unless the series has
    already been sorted once before.

    After combining the series into a N-D volume, the following additional parameters are calculated and inserted into
    the :class:`Volume` class:
    * Origin
    * Orientation
    * Spacing
    * Coordinate system

    The volume will be shaped such that it adheres to C-order indexing rather than Fortran-order indexing. This means
    that the slowest varying axis will be first and the fastest varying axis will be last. As an example, a
    spatiotemporal volume would be indexed like (t, z, y, x). In accordance with this convention, the spacing
    parameter will match the order of the dimensions. For example, the second element of the spacing array will
    correspond to the spacing of the z-axis.

    Two other parameters do **not** follow this convention however. The origin is Fortran-ordered, or Cartesian indexed,
    such that the origin is (x, y, z). This was decided because the origin is a spatial point and that is the typical
    way of representing a point. In a similar manner, the orientation matrix is constructed such that the left column
    is the x cosines, and the right most column is the z cosines.

    Parameters
    ----------
    series : Series
    methods : MethodType or list(MethodType), optional
        See :meth:`sortSeries` for more information on this parameter. Only used if the series has **not** been sorted
        yet.
    reverse : bool, optional
        See :meth:`sortSeries` for more information on this parameter. Only used if the series has **not** been sorted
        yet.
    squeeze : bool, optional
        See :meth:`sortSeries` for more information on this parameter. Only used if the series has **not** been sorted
        yet.
    warn : bool, optional
        See :meth:`sortSeries` for more information on this parameter. Only used if the series has **not** been sorted
        yet.
    shapeTolerance : float, optional
        See :meth:`sortSeries` for more information on this parameter. Only used if the series has **not** been sorted
        yet.
    spacingTolerance : float, optional
        See :meth:`sortSeries` for more information on this parameter. Only used if the series has **not** been sorted
        yet.

    Raises
    ------
    TypeError
        If the series is empty
    Exception
        If datasets do not have the same image shape
    Exception
        If datasets do not have uniform image spacing or orientation

    Returns
    -------
    Volume
        Volume that contains Numpy array, origin, spacing and other relevant information
    """

    # If the series has not been sorted yet, then sort it
    # Or, if there are no datasets in the series then throw an error
    if series._shape is None:
        series = series.sort(methods, reverse, squeeze, warn, shapeTolerance, spacingTolerance)
    elif len(series) == 0:
        raise TypeError('Series must contain at least one dataset')

    # List of variables that are stored from DICOM header
    imageShapes = []
    imageSpacings = []
    imageOrientations = []
    origin = None
    images = []

    if series.isMultiFrame:
        # Foreach dataset, store image shape, spacing, orientation and the image data itself
        # The image spacing is not required in the DICOM header, so it will default to (1, 1) if not available
        for dataset in series:
            imageShapes.append(dataset.parent.pixel_array.shape[1:])
            imageSpacings.append(dataset.PixelMeasuresSequence[0].PixelSpacing if 'PixelSpacing' in
                                 dataset.PixelMeasuresSequence[0] else (1, 1))
            imageOrientations.append(dataset.PlaneOrientationSequence[0].ImageOrientationPatient)
            images.append(dataset.parent.pixel_array[dataset.sliceIndex, None, :, :])

        # Origin for volume is the first series position
        origin = np.asfarray(series[0].PlanePositionSequence[0].ImagePositionPatient)
    else:
        # Foreach dataset, store image shape, spacing, orientation and the image data itself
        # The image spacing is not required in the DICOM header, so it will default to (1, 1) if not available
        for dataset in series:
            imageShapes.append(dataset.pixel_array.shape)
            imageSpacings.append(dataset.PixelSpacing if 'PixelSpacing' in dataset else (1, 1))
            imageOrientations.append(dataset.ImageOrientationPatient)
            images.append(dataset.pixel_array[None, :, :])

        # Origin for volume is the first series position
        origin = np.asfarray(series[0].ImagePositionPatient)

    # Check all of the image shapes to make sure they can be stacked together
    if not np.allclose(imageShapes, imageShapes[0], rtol=0.01):
        logger.debug('Datasets shape: %s' % imageShapes)
        raise Exception('Datasets do not have the same shape. Unable to combine into one volume')

    # Check image spacings to make sure they are uniform, otherwise throw warning/error
    if not np.allclose(imageSpacings, imageSpacings[0], rtol=0.1):
        if warn:
            logger.warning('Datasets image spacing are not uniform')
            logger.debug('Datasets spacings: %s' % imageSpacings)
        else:
            logger.debug('Datasets spacings: %s' % imageSpacings)
            raise Exception('Datasets image spacing are not uniform')

    # Check image orientations to make sure they are the same, otherwise throw warning/error
    # I cannot think of a use case where there would be different image orientations that would be combined into one
    # volume. It is a weird idea.
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

    # Get the entire shape of the data by taking the multidimensional shape and spacing and tack on the image size and
    # spacing
    # This is prepended because we are using C-ordering meaning slower varying indices come first
    shape = series.shape + imageShape

    # Spacing is flipped to go from C-order to Fortran-order, this way it stays consistent with the rest of the
    # DICOM & Volume data (origin, orientation, etc)
    spacing = np.flip(series.spacing + tuple(imageSpacing), axis=0)

    # Create 3D volume from stack of 2D images
    volume = np.vstack(images)

    # Ensure that we are able to resize the volume into the correct shape
    if np.prod(shape) != np.prod(volume.shape):
        raise Exception('Unable to reshape volume with %i elements into shape %s' % (np.prod(volume.shape), shape))

    # Reshape the volume into the image shape
    volume = volume.reshape(shape)

    # DICOM uses LPS space
    space = 'left-posterior-superior'

    # Row cosines is first 3 elements, column cosines is last 3 elements of array, compute z cosines from row/col
    rowCosines = np.array(imageOrientation[:3])
    colCosines = np.array(imageOrientation[3:])
    zCosines = np.cross(rowCosines, colCosines)

    # Orientation is combination of the three cosines direction matrix
    # Note: If the user sorts based on (z) location and sets reverse to True, then the third (z) column of orientation
    # will need to be inverted to accurately reflect the orientation. No metadata for if the series is reverse sorted
    # is not stored and I don't think it is worth storing. Rather, I have decided to leave it up to the user to change
    # that last dimension if necessary. Until there is an valid application where reverse is used then I won't bother
    orientation = np.hstack((rowCosines[:, None], colCosines[:, None], zCosines[:, None]))

    # Return Volume class containing information about the volume
    # It's a basic wrapper class to contain any relevant data for the volume
    return Volume(volume, space, orientation, origin, spacing)
