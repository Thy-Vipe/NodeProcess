import uuid, json
from Nodes.Decorators import *
from Nodes.CoreProperties import *

class NObject(object):
    """
        This is the root object for all node-based logic in this software. It holds a few functions that serve as the base
        for every other NObject subclass. It is made of overridable functions that are expected to be used everywhere in many different instances.
        Every NObject has a 64-bit UUID that is used to have every object be "unique".
    """
    def __init__(self, world=None, name="", inOwner=None):
        CLASS_BODY(self)

        NATTR(self, '_uuid', EAttrType.AT_Serializable)
        self._uuid = NString(uuid.uuid4())

        NATTR(self, '_name', EAttrType.AT_Serializable)
        self._name = NString(name)
        self._owner = inOwner
        self._world = world if (world and world.__class__.__name__ == 'NWorld') else None

        if self.getWorld():
            self._world.registerObjectWithWorld(self)

    def getUUID(self):
        return self._uuid

    def setUUID(self, inUUID):
        self._uuid = inUUID

    def getName(self):
        return self._name

    def setName(self, inName):
        self._name = inName

    def getOwner(self):
        """
        Get the object that owns this, if defined. Can be None.
        :return: The object owning this object.
        """
        return self._owner

    def getWorld(self):
        return self._world

    def __archive__(self, Ar):
        """
        Automatically serializes any property that is marked as serializable using EAttrType.AT_Serializable when declaring the attribute.
        Any property marked as serializable must hold an object that overrides the '__archive__(Ar&)' method, or the property will be ignored.
        :param Ar: The archive to use for serialization.
        :type Ar: NArchive.
        """
        OwnAr = NArchive()
        for prop in dir(self):
            if EAttrType.AT_Serializable in self.__PropFlags__.get(prop, ()):
                propInst = getattr(self, prop)
                try:
                    # Do not recursively serialize NObjects. Only properties. Get UUID for objects.
                    if isinstance(propInst, NObject):
                        OwnAr << propInst.getUUID()
                    else:
                        OwnAr << propInst
                except TypeError:
                    print(Warning("%s.%s is not serializable." % (propInst.__class__.__name__, prop)))

        Ar += OwnAr.combine()

    def __binaryreader__(self, data):
        """
        NObject __binaryreader__ expects a list of tuples of buffers and byte arrays, the data is unpacked within this function.
        :param data: The list of tuples of buffers and byte arrays.
        :type data: iterable.
        :return: the new Archive position after computation.
        """
        idx = 0
        num = len(data)
        for prop in dir(self):
            if idx < num:
                if EAttrType.AT_Serializable in self.__PropFlags__.get(prop, ()):
                    obj = getattr(self, prop)
                    dt = struct.unpack_from(data[idx][0], data[idx][1], 0)
                    obj.__reader__(dt)

                    idx += 1

        return idx

    def __str__(self):
        return "%s.%s" % (self.__class__.__name__, self._name)
