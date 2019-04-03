import warnings, collections

ActiveClasses = {}
classInstances = {}


def addToGlobal(typ, classRef):
    global ActiveClasses
    if typ not in ActiveClasses.keys():
        ActiveClasses[typ] = classRef


def findClass(typ):
    global ActiveClasses
    return ActiveClasses.get(typ, None)


def addInstance(obj):
    global classInstances
    classInstances[obj.getUUID()] = obj


def getInstance(uuid):
    global classInstances
    return classInstances.get(uuid, None)


def swapInstanceKey(olduuid):
    global classInstances
    assert isinstance(olduuid, (str, collections.UserString))
    ptr = classInstances.get(olduuid, None)

    if ptr:
        classInstances[ptr.getUUID()] = ptr
        classInstances.pop(olduuid)
    else:
        warnings.warn("%s no longer exists or is not valid." % olduuid, RuntimeWarning)
        classInstances[olduuid] = None
        del classInstances[olduuid]
