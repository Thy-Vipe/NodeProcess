import uuid, json, warnings
from Nodes.Decorators import *
from Nodes.CoreProperties import *
import global_accessor as GA
import weakref


class NWeakRef(weakref.ref):
    """
    Extension of weak reference.
    """
    def __init__(self, ob, callback=None, **annotations):
        super(NWeakRef, self).__init__(ob, callback)

        for k, v in annotations.items():
            setattr(self, k, v)


class NWeakMethod(weakref.WeakMethod):
    def __init__(self, *args, **kwargs):
        super(NWeakMethod, self).__init__(*args, **kwargs)


class NFinalizer(weakref.finalize):
    def __init__(self, obj, callback, *args, **kwargs):
        super(NFinalizer, self).__init__(obj, callback, *args, **kwargs)


class NObject(object):
    """
        This is the root object for all node-based logic in this software. It holds a few functions that serve as the base
        for every other NObject subclass. It is made of overridable functions that are expected to be used everywhere in many different instances.
        Every NObject has a 64-bit UUID that is used to have every object be "unique".
    """
    def __init__(self, **kwargs):

        CLASS_BODY(self)

        inOwner = kwargs.get('owner', None); world = kwargs.get('world', None); assert world.__class__.__name__ == 'NWorld' if world else True

        NATTR(self, '_uuid', EAttrType.AT_Serializable)
        self._uuid = NString(uuid.uuid4())

        NATTR(self, '_name', EAttrType.AT_Serializable)
        self._name = NString(kwargs.get('name', "Unnamed"))

        NATTR(self, '_owner', EAttrType.AT_Serializable)
        self._owner = NWeakRef(inOwner) if kwargs.get("UseHardRef", False) and inOwner else inOwner

        #  Always keep a hard reference of NWorld.
        self._world = world

        if self.getWorld():
            self._world.registerObjectWithWorld(self)

        CLASS_REGISTER(self)

    def getUUID(self):
        return self._uuid.copy()

    def setUUID(self, inUUID):
        self._uuid = inUUID

    def getName(self):
        return self._name.copy()

    def setName(self, inName):
        self._name = inName

    def getOwner(self):
        """
        Get the object that owns this, if defined. Can be None.
        :return: The object owning this object.
        """
        return self._owner()

    def getWorld(self):
        return self._world

    def __archive__(self, Ar: NArchive):
        """
        Automatically serializes any property that is marked as serializable using EAttrType.AT_Serializable when declaring the attribute.
        Any property marked as serializable must hold an object that overrides the '__archive__(Ar&)' method, or TypeError will be thrown.
        :param Ar: The archive to use for serialization.
        :type Ar: NArchive.
        """
        OwnAr = NArchive()
        for prop in dir(self):
            __propFlags = self.__PropFlags__.get(prop, ())
            if EAttrType.AT_Serializable in __propFlags:
                propInst = getattr(self, prop)
                if propInst:
                    # Do not recursively serialize NObjects. Only properties.
                    # Get UUID for objects unless they're declared as transient, in which case serialize.
                    if isinstance(propInst, NObject) and EAttrType.AT_Transient not in __propFlags:
                        OwnAr << propInst.getUUID()
                    else:
                        OwnAr << propInst

        Ar += OwnAr.combine()

    def __binaryreader__(self, data: (list, tuple)):
        """
        NObject __binaryreader__ expects a list of tuples of buffers and byte arrays, the data is unpacked within this function.
        :param data: The list of tuples of buffers and byte arrays.
        :type data: iterable.
        :return: the new Archive position after computation.
        """
        prevUUID = self._uuid.copy()
        idx = 0
        # print(data)
        values = struct.unpack_from(data[0][0], data[0][1], 0)
        # print(values)
        num = len(values); print(num)
        PendingArrays = []
        for prop in dir(self):
            if idx < num:
                __propFlags = self.__PropFlags__.get(prop, ())
                if EAttrType.AT_Serializable in __propFlags:
                    obj = getattr(self, prop)
                    val = values[idx] if not hasattr(values[idx], 'decode') else values[idx].decode()
                    if hasattr(obj, '__reader__'):
                        # print(prop, val)
                        obj.__reader__(val)
                        idx += 1
                    elif hasattr(obj, '__binaryreader__'):
                        if val == 'array_begin':
                            endArray = values.index('array_end'.encode()); assert endArray != -1  # should never be false
                            dt = values[idx+1:endArray]
                            PendingArrays.append([idx, endArray, dt, obj])

                            # Make sure to offset the read index, as the order is sensitive.
                            # Objects MUST be deserialized in the exact order they were serialized.
                            idx += endArray+1

                        else:
                            obj.__binaryreader__(val)
                            idx += 1

        GA.swapInstanceKey(prevUUID)

        # Arrays must be regenerated at the end of the properties parsing, because they regenerate the items that were saved into them automatically, which
        # requires the appropriate NObject._uuid to respawn connections, for instance.
        for arr in PendingArrays:
            arr[3].__binaryreader__(arr[2])

        return 1

    def __str__(self):
        return "%s with ID %s" % (self.__class__.__name__, self.getUUID())
