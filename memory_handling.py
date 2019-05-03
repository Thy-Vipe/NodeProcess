import gc


def getReferrers(obj: object):
    """
    Get all hard referrer instances for a given object.
    :param obj: The object to check referrers for.
    :return: A tuple containing the referrer and the dict of attributes referencing the object.
    """
    result = []
    for o in gc.get_referrers(obj):
        s = gc.get_referrers(o)[0]
        try:
            it = iter(s)
        except TypeError:
            result.append((s, o))
        else:
            continue

    return result


def clearReferences(referrers: tuple):
    for refs in referrers:
        for key in refs[1].keys():
            setattr(refs[0], key, None)
