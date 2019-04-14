import warnings, collections

ActiveClasses = {}
classInstances = {}
functionClasses = {}

def addToGlobal(typ, classRef):
    global ActiveClasses
    if typ not in ActiveClasses.keys():
        ActiveClasses[typ] = classRef


def findClass(typ):
    global ActiveClasses
    return ActiveClasses.get(typ, None)


def addInstance(obj):
    global classInstances
    print('registering new object: %s, name: %s' % (obj, obj.getName().toString()))
    classInstances[obj.getUUID()] = obj


def getInstance(uuid):
    global classInstances
    return classInstances.get(uuid, None)

def getInstanceByName(name: str):
    global classInstances
    for v in classInstances.values():
        if v.getName().toString() == name:
            return v


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


def registerFunction(function):
    global functionClasses

    # "functions" are not actual python methods. They're NObjects that can be called from visual scripting.
    # In function must be the class, not an instance of it.
    if function.__name__ not in functionClasses.keys():
        functionClasses[function.__name__] = function


def funcInstances(classType):
    global classInstances
    result = []
    for k, v in classInstances.items():
        if isinstance(v, classType):
            result.append(v)

    return result
