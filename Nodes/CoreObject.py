import uuid, json
from Nodes.Decorators import *
from Nodes.CoreProperties import *

class NObject(object):
    """
        This is the root object for all node-based logic in this software. It holds a few functions that serve as the base
        for every other NObject subclass. It is made of overridable functions that are expected to be used everywhere in many different instances.
        Every NObject has a 64-bit UUID that is used to have every object be "unique".
    """
    def __init__(self, name="", inOwner=None):
        CLASS_BODY(self)

        NATTR(self, '_uuid', EAttrType.AT_Serializable)
        self._uuid = NString(uuid.uuid4())

        NATTR(self, '_name', EAttrType.AT_Serializable)
        self._name = NString(name)
        self._owner = inOwner

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

    def __archive__(self, Ar):
        """
        Automatically serializes any property that is marked as serializable using EAttrType.AT_Serializable when declaring the attribute.
        Any property marked as serializable must hold an object that overrides the '__archive__(Ar&)' method, or the property will be ignored.
        :param Ar: The archive to use for serialization.
        :type Ar: NArchive.
        """
        for prop in dir(self):
            if EAttrType.AT_Serializable in self.__PropFlags__.get(prop, ()):
                propInst = getattr(self, prop)
                try:
                    # Do not recursively serialize objects. Only properties. Get UUID for objects.
                    if isinstance(propInst, NObject):
                        Ar << propInst.getUUID()
                    else:
                        Ar << propInst
                except TypeError:
                    print(Warning("%s.%s is not serializable." % (propInst.__class__.__name__, prop)))

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
            # @TODO Finish implementation of __reader__(data) in NObject.

        return idx - 1

    def __str__(self):
        return "%s.%s" % (self.__class__.__name__, self._name)



obj = NObject("name")
Ar = NArchive()

Ar << obj
Ar << NPoint2D(35.254654, 8.99990001)

newNode = NObject()
print(Ar.getData())
mem = NMemoryReader(Ar.getData())
mem.seek(0)
mem << newNode

print(newNode.getName(), newNode.getUUID())
dataOrd = []
with open("C:\\Users\\ThyVi\\Desktop\\testBinaryjson.narchive", 'w') as f:

    with open("C:\\Users\\ThyVi\\Desktop\\testBinary_tmp.narchive", 'wb') as fb:

        # for buffer, data in Ar.getData():
        #     dataOrd.append(fb.write(buffer.encode()))
        #     dataOrd.append(fb.write(data))
        #     fb.flush()
        #
        #
        # # write header of file
        #
        # buff = '%dI' % len(dataOrd)
        # length = fb.write(struct.pack(buff, *dataOrd))
        # fb.write(length.to_bytes(8, 'big', signed=False))
        # fb.write(len(dataOrd).to_bytes(8, 'big', signed=False))

        Ar.writeToFile(fb, 'test')

    # print(dataOrd)
#
# with open("C:\\Users\\ThyVi\\Desktop\\testBinary_tmp.narchive", 'rb') as f:
#
#     print(f.read())
#     f.seek(-16, 2)
#     arrlength = int.from_bytes(f.read(8), 'big')
#     print(arrlength)
#     buffcnt = int.from_bytes(f.read(8), 'big')
#     buffer = "%dI" % buffcnt
#     f.seek(-(arrlength+16), 1)
#     arr = struct.unpack(buffer, f.read(arrlength))
#     print(arr)
#
#     i = 0
#     t = 0
#     f.seek(0,0)
#     binary = []
#     for p in arr:
#         binary.append(f.read(p))
#         f.seek(t + p, 0)
#         t += p
#
#     print(binary)

#
#
with open("C:\\Users\\ThyVi\\Desktop\\testBinary_tmp.narchive", 'rb') as f:
    print("=================================================")
    print(NArchive.decodeFile(f))