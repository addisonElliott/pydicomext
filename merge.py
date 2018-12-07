from .series import Series


def merge(seriess, indices=None):
    """Take a list of series and combine them into one series
    
    Parameters
    ----------
    seriess : [type]
        [description]
    
    Raises
    ------
    TypeError
        [description]
    
    Returns
    -------
    [type]
        [description]
    """

    if len(seriess) == 0:
        raise TypeError('Must have at least one series in the list')
    elif len(seriess) == 1:
        return seriess

    mergedSeries = Series()
    mergedSeries._onlyMultiFrames = seriess[0]._onlyMultiFrames

    for series in seriess:
        mergedSeries._onlyMultiFrames = mergedSeries._onlyMultiFrames and series._onlyMultiFrames
        mergedSeries._multiFrameData.extend(series._multiFrameData)
        mergedSeries.extend(series)
