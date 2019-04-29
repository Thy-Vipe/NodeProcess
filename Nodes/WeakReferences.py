import weakref


class NWeakRef(weakref.ref):
    """
    Extension of weak reference.
    """
    def __init__(self, ob, callback=None, **annotations):
        super(NWeakRef, self).__init__(ob, callback)

        for k, v in annotations.items():
            setattr(self, k, v)

    def isValid(self):
        return self() is not None


class NWeakMethod(weakref.WeakMethod):
    def __init__(self, *args, **kwargs):
        super(NWeakMethod, self).__init__(*args, **kwargs)

    def isValid(self):
        return self() is not None


class NFinalizer(weakref.finalize):
    def __init__(self, obj, callback, *args, **kwargs):
        super(NFinalizer, self).__init__(obj, callback, *args, **kwargs)