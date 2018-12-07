import operator

from .series import Series


def mergeSeries(seriess, indices=None):
    """Merge a list of series into one series only taking the specified indices from the list of series

    Takes each series in the list of series' and combines them into one large series. In addition, if the :obj:`indices`
    argument is specified, then specified indices from each of the series will be selected and placed into the
    resulting merged series.

    The length of :obj:`indices` should be the same as :obj:`seriess`. Each series will select datasets using the
    corresponding indices from the :obj:`indices` argument. For example, the 7th series in :obj:`seriess` will use the
    index or list of indices at the 7th index of :obj:`indices`.

    If one series is given in the list of series', then that series will be returned regardless of whether indices are
    given to extract.

    Parameters
    ----------
    seriess : list(Series)
        List of series to combine into one merged series
    indices : list(list(int)) or list(int), optional
        list of lists of integers that represent indices to place into the merged series (default is None, which uses
        all indices from the series')

    Raises
    ------
    TypeError
        If there are no series in the list of series'
    TypeError
        If the length of indices is not equal to the length of the series'

    Returns
    -------
    Series
        Merged series from the combination of series'
    """

    # If no series given, throw error
    # If only one series given, return that series
    # If length of indices does not match length of series, throw error
    if len(seriess) == 0:
        raise TypeError('Must have at least one series in the list')
    elif len(seriess) == 1:
        return seriess[0]
    elif indices is not None and len(indices) != len(seriess):
        raise TypeError('Should be the same number of indices as series\' to merge')

    mergedSeries = Series()
    if indices is None:
        # Loop through and add each series' datasets to the merged series
        # Use boolean OR to figure out if multi frame datasets exist
        for series in seriess:
            mergedSeries._isMultiFrame |= series._isMultiFrame
            mergedSeries.extend(series)
    else:
        for series, indices_ in zip(seriess, indices):
            if len(indices_) > 0:
                mergedSeries._isMultiFrame |= series._isMultiFrame
                mergedSeries.extend(operator.itemgetter(*indices_)(series))

    return mergeSeries


def mergeDatasets(datasets):
    """Merge a list of datasets into one series

    Parameters
    ----------
    datasets : list(pydicom.Dataset)
        List of datasets to combine into one series together

    Raises
    ------
    TypeError
        If no datasets are present in the list

    Returns
    -------
    Series
        Merged series from the combination of datasets
    """

    if len(datasets) == 0:
        raise TypeError('Must have at least one dataset in the list')

    mergedSeries = Series()
    mergeSeries.extend(datasets)

    # Will reevaluate if the series is multi frame since we added datasets to a blank series
    mergedSeries.checkIsMultiFrame()

    return mergeSeries
