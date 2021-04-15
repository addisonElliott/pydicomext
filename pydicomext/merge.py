import operator

from pydicomext.series import Series


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
        all indices from the series'). If any of the indices are None an empty list/tuple or anything besides an
        integer, then no datasets from that series will not be added to the merged series.

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
        # Loop through each series and add the specified datasets to the merged series
        for series, indices_ in zip(seriess, indices):
            # If the indices is iterable, then we add using itemgetter to retrieve all of the indices
            # Otherwise, add to the list if it is an integer
            if hasattr(indices_, '__iter__') and len(indices_) > 0:
                # If the length is exactly one then we need to append and not extend!
                if len(indices_) == 1:
                    mergedSeries.append(operator.itemgetter(*indices_)(series))
                else:
                    mergedSeries.extend(operator.itemgetter(*indices_)(series))
            elif isinstance(indices_, int):
                mergedSeries.append(series[indices_])

        # Have to check multi frame at the end, we acnnot use series._isMultiFrame and boolean OR like above because we
        # don't know which datasets we are extracting. I.e. we could extract all of the non-multiframe datasets from a
        # multiframe series and cause this to mess up.
        mergedSeries.checkIsMultiFrame()

    return mergedSeries


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

    mergedSeries = Series(datasets)

    # Will reevaluate if the series is multi frame since we added datasets to a blank series
    mergedSeries.checkIsMultiFrame()

    return mergedSeries
