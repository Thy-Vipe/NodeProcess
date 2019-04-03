from __future__ import division

from functools import reduce
import math
from numbers import Real
import array, struct, collections

from PySide2.QtCore import QPoint, QPointF


# Define various macros...
EXPOSEDPROPNAME = "propTypes"


class EAttrType:
    AT_Serializable = 0
    AT_ReadOnly = 1
    AT_ReadWrite = 2
    AT_MulticastDelegate = 3
    AT_SingleCastDelegate = 4
    AT_Getter = 5


class EPropType:
    PT_Input = 0
    PT_Output = 1
    PT_FuncDelegateIn = 2
    PT_FuncDelegateOut = 3
    PT_Readable = 4


class EFuncType:
    # Used for heavy operations that require a certain amount of processing.
    FT_Callable = 0
    # Used if the logic behind the function object is simple / quick to execute
    FT_Pure = 1


class NArchive(object):
    """
    Archive class. Used for serializing data into binary. Can be dumped into a json file.
    Use the "<<" on any class that implements __archive__(Ar) to serialize the object's data.
    NArchive can be converted into byteArrays (in a tuple holding the sequence buffer and the data itself) in order to be quickly
    convertible / transmittable if needed.

    Use NMemoryReader in order to read from byte arrays or byte sequences. NArchive serializes data into byte sequences that can then be converted into
    byte arrays using NArchive.toByteArrays().
    """
    def __init__(self):
        super(NArchive, self).__init__()
        self._byteBuffers = []
        self.position = 0

    def __lshift__(self, other):
        if hasattr(other, "__archive__"):
            other.__archive__(self)

        else:
            raise TypeError("%s does not implement __archive__()." % other.__class__.__name__)

    def __add__(self, buffer):
        if isinstance(buffer, tuple) and len(buffer) == 2:
            self._byteBuffers.append(buffer)
            self.position += 1
        else:
            raise TypeError("Invalid input: buffer must be a tuple holding the buffer and the binary data.")

    def toByteArrays(self):
        if not NArchive.ensure(self._byteBuffers, array.array):
            res = []
            for item in self._byteBuffers:
                s = struct.Struct(item[0])
                ar = array.array('I', [0] * s.size)
                data = s.unpack(item[1])
                s.pack_into(ar, 0, *data)
                res.append((item[0], ar))

            return res
        else:
            return self._byteBuffers

    def getData(self):
        return self._byteBuffers

    @staticmethod
    def ensure(inList, classType, position=1):
        for item in inList:
            if isinstance(item, tuple) and classType is not tuple:
                item = item[position]

            if not isinstance(item, classType):
                return False

        return True

    @staticmethod
    def headerSeparator():
        return 16

    @staticmethod
    def intSize():
        return 16

    def writeToFile(self, binary_file, objName):
        # Write all the data contained in our buffer
        byteInfo = []
        int_size = NArchive.intSize()
        # will be used at the end to indicate the position of the end of this chunk.
        count = binary_file.write(b'0'.zfill(int_size))

        for buffer, data in self.getData():
            byteInfo.append(binary_file.write(buffer.encode()))
            count += byteInfo[-1]
            byteInfo.append(binary_file.write(data))
            count += byteInfo[-1]
            binary_file.flush()

        # Write header of this file at the end, that way we know where the header exactly begins.
        binLen = len(byteInfo)
        buff = '%dI' % binLen
        byteInfoLen = binary_file.write(struct.pack(buff, *byteInfo)); count += byteInfoLen
        count += binary_file.write(byteInfoLen.to_bytes(int_size, 'big', signed=False))
        count += binary_file.write(binLen.to_bytes(int_size, 'big', signed=False))
        nameLen = binary_file.write(objName.encode())
        print(nameLen)
        add = binary_file.write(nameLen.to_bytes(int_size, 'big', signed=False)); count += add; print(add, count)
        h = binary_file.write(b'0'.zfill(NArchive.headerSeparator())); count += h; print(h, count)

        # now use the preallocated 16 bits to write the length of this chunk.
        binary_file.seek(0, 0)
        binary_file.write(count.to_bytes(int_size, 'big', signed=False))
        binary_file.seek(count)
        binary_file.flush()

    @staticmethod
    def decodeFile(binary_file):
        pos = 0
        output = {}
        all_data = binary_file.read()
        # print(all_data)
        j = len(all_data)
        int_size = NArchive.intSize()
        # Get the header for chunk x
        binary_file.seek(0, 0)
        while pos < j:
            # Get the end of the first chunk. Written at the very start of the header in the 16 first bits.
            nextpos = int.from_bytes(binary_file.read(int_size), 'big', signed=False); print(nextpos)
            tpos = nextpos - (NArchive.headerSeparator()+int_size); print(tpos)
            binary_file.seek(tpos)
            nameBuffer = int.from_bytes(binary_file.read(int_size), 'big', signed=False); print(nameBuffer)
            objName = binary_file.read(nameBuffer).decode()
            print(objName)
            arrayBufferLen = int.from_bytes(binary_file.read(int_size), 'big', signed=False)
            arrayBytesCnt = int.from_bytes(binary_file.read(int_size), 'big', signed=False)
            binary_file.seek(-(arrayBytesCnt + int_size), 1)
            buffer = '%dI' % arrayBufferLen
            arr = struct.unpack(buffer, binary_file.read(arrayBytesCnt))

            data = []
            s = pos + NArchive.headerSeparator()
            for p in arr:
                data.append(binary_file.read(p))
                s += p

            output[objName] = data
            print(data)

            pos = nextpos

        return output





class NMemoryReader(NArchive):
    """
    Use NMemoryReader to deserialize data from byte arrays or byte sequences.
    Upon construction, NMemoryReader expects a tuple of byteArrays or byte sequences to operate with.
    Use "<<" to deserialize data from NMemoryReader. Make sure to deserialize data in the exact order it was serialized with,
    or the results will be incorrect.
    Classes must implement __reader__(data) in order to read data from NMemoryReader.
    """
    def __init__(self, inBuffer):
        super(NMemoryReader, self).__init__()
        bUseBytes = False
        if len(inBuffer) != 0:
            if NMemoryReader.ensure(inBuffer, array.array):
                self._byteBuffers = inBuffer
                bUseBytes = True
            elif NMemoryReader.ensure(inBuffer, tuple):
                self._byteBuffers = inBuffer

        self.__memoryType = int(bUseBytes)


    def __lshift__(self, other):
        if hasattr(other, "__reader__"):
            # If memory is bytes buffer
            if self.__memoryType == 1:
                data = self._byteBuffers[self.position]
                unpackedBin = struct.unpack_from(data[0], data[1], 0)
                other.__reader__(unpackedBin)

            # If memory is bytes sequence
            elif self.__memoryType == 0:
                data = self._byteBuffers[self.position]
                unpackedBin = struct.unpack(data[0], data[1])
                other.__reader__(unpackedBin)

            self.position += 1

        elif hasattr(other, '__binaryreader__'):
            end = other.__binaryreader__(self.toByteArrays())
            # mark end of data.
            self.position = end + 1

        else:
            raise TypeError("%s does not implement __reader__(data) or __binaryreader__(data)." % other.__class__.__name__)



    def seek(self, pos):
        if pos < len(self._byteBuffers):
            self.position = pos
        else:
            raise IndexError("Ensure condition failed: position < len(byteBuffer) != True")



class NString(collections.UserString):
    """
    Extension of class "str" with more methods used for NodeProcess.
    We're using a wrapper for str here, because str isn't easy to work with.
    The main difference is that NString is MUTABLE.
    """

    def __archive__(self, Ar):
        """
        Serialize NString into a byte buffer.
        :param Ar: The input archive to serialize into / deserialize from. Modifies the input directly.
        :type Ar: NArchive.
        """
        encoding = '%ds' % len(self)
        s = struct.Struct(encoding)
        buffer = s.pack(self.data.encode())
        Ar += (encoding, buffer)

    def __reader__(self, data):
        self.data = data[0].decode()

    @staticmethod
    def toString(inObject):
        """
        Casts a string/stringifiable object into NString.
        :param inObject: The object to "cast" from
        :return: The new NString.
        """
        return NString(str(inObject))


class NPoint2D(object):
    """
    Npoint2D: Represents a point in 2D space.
    """
    def __init__(self, x=0, y=0, bForceInt=False):
        self.x = x
        self.y = y
        self.__IsInt = bForceInt

    def __archive__(self, Ar):
        """
        Serialize NPoint2D into a byte buffer.
        :param Ar: The input archive to serialize into / deserialize from. Modifies the input directly.
        :type Ar: NArchive.
        """
        s = struct.Struct('2d?')
        Ar += ('2d?', s.pack(self.x, self.y, self.__IsInt))

    def __reader__(self, data):
        self.x, self.y, self.__IsInt = data

    def __repr__(self):
        return "{0}({1}, {2})".format(
            self.__class__.__name__,
            self.x,
            self.y
        )

    def __mul__(self, pt):
        if isinstance(pt, NPoint2D):
            return NPoint2D(self.x * pt.x, self.y * pt.y, self.__IsInt)
        elif isinstance(pt, (float, int)):
            return NPoint2D(self.x * pt, self.y * pt, self.__IsInt)
        else:
            raise TypeError

    def __sub__(self, pt):
        if type(pt) is NPoint2D:
            return NPoint2D(pt.x - self.x, pt.y - self.y, self.__IsInt)
        elif type(pt) is (int, float):
            return NPoint2D(pt - self.x, pt - self.y, self.__IsInt)
        else:
            raise TypeError

    def __add__(self, pt):
        if isinstance(pt, NPoint2D):
            return NPoint2D(self.x + pt.x, self.y + pt.y, self.__IsInt)
        elif isinstance(pt, (int, float)):
            return NPoint2D(self.x + pt, self.y + pt, self.__IsInt)
        else:
            raise TypeError

    def __eq__(self, pt):
        if isinstance(pt, NPoint2D):
            return (
                self.x == pt.x and
                self.y == pt.y
            )
        else:
            raise TypeError

    def toList(self):
        return [self.x, self.y]

    def toQPoint(self):
        return QPoint(*map(int, self.toList()))

    def toQPointF(self):
        return QPointF(*map(float, self.toList()))

    @classmethod
    def fromList(cls, l, bForceInt=False):
        if len(l) == 2:
            return cls(*map(float, l)) if bForceInt else cls(*map(int, l))
        else:
            raise AttributeError

    @classmethod
    def fromQPoint(cls, pt):
        return cls(pt.x(), pt.y(), type(pt.x()) is int)


class NPoint(object):
    """NPoint class: Represents a point in the x, y, z space."""
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def __archive__(self, Ar):
        s = struct.Struct('3d')
        Ar += ('3d', s.pack(self.x, self.y, self.z))

    def __reader__(self, data):
        self.x, self.y, self.z = data

    def __repr__(self):
        return '{0}({1}, {2}, {3})'.format(
            self.__class__.__name__,
            self.x,
            self.y,
            self.z
        )

    def __sub__(self, point):
        """Return a NPoint instance as the displacement of two points."""
        if type(point) is NPoint:
            return self.substract(point)
        else:
            raise TypeError

    def __add__(self, pt):
        if isinstance(pt, NPoint):
            if self.z and pt.z:
                return NPoint(pt.x + self.x, pt.y + self.y, pt.z + self.z)
            elif self.z:
                return NPoint(pt.x + self.x, pt.y + self.y, self.z)
            elif pt.z:
                return NPoint(pt.x + self.x, pt.y + self.y, pt.z)
            else:
                return NPoint(pt.x + self.x, pt.y + self.y)
        else:
            raise TypeError

    def __eq__(self, pt):
        return (
            self.x == pt.x and
            self.y == pt.y and
            self.z == pt.z
        )

    def to_list(self):
        """Returns an array of [x,y,z] of the end points"""
        return [self.x, self.y, self.z]

    def substract(self, pt):
        """Return a NPoint instance as the displacement of two points."""
        if isinstance(pt, NPoint):
                return NPoint(pt.x - self.x, pt.y - self.y, pt.z - self.z)
        else:
            raise TypeError

    @classmethod
    def from_list(cls, l):
        """Return a NPoint instance from a given list"""
        if len(l) == 3:
                x, y, z = map(float, l)
                return cls(x, y, z)
        elif len(l) == 2:
            x, y = map(float, l)
            return cls(x, y)
        else:
            raise AttributeError


class NVector(NPoint):
    """NVector class: Representing a vector in 3D space.
    Can accept formats of:
    Cartesian coordinates in the x, y, z space.(Regular initialization)
    Spherical coordinates in the r, theta, phi space.(Spherical class method)
    Cylindrical coordinates in the r, theta, z space.(Cylindrical class method)
    """

    def __init__(self, x=0.0, y=0.0, z=0.0):
        """Vectors are created in rectangular coordniates
        to create a vector in spherical or cylindrical
        see the class methods
        """
        super(NVector, self).__init__(x, y, z)

    def __add__(self, vec):
        """Add two vectors together"""
        if(type(vec) == type(self)):
            return NVector(self.x + vec.x, self.y + vec.y, self.z + vec.z)
        elif isinstance(vec, Real):
            return self.add(vec)
        else:
            raise TypeError

    def __sub__(self, vec):
        """Subtract two vectors"""
        if(type(vec) == type(self)):
            return NVector(self.x - vec.x, self.y - vec.y, self.z - vec.z)
        elif isinstance(vec, Real):
            return NVector(self.x - vec, self.y - vec, self.z - vec)
        else:
            raise TypeError

    def __mul__(self, anotherVector):
        """Return a NVector instance as the cross product of two vectors"""
        return self.cross(anotherVector)

    def __str__(self):
        return "{0}({1},{2},{3})".format(self.__class__.__name__, self.x, self.y, self.z)

    def add(self, number):
        """Return a NVector as the product of the vector and a real number."""
        return self.from_list([x + number for x in self])

    def multiply(self, number):
        """Return a NVector as the product of the vector and a real number."""
        return self.from_list([x * number for x in self.to_list()])

    def magnitude(self):
        """Return magnitude of the vector."""
        return math.sqrt(
            reduce(lambda x, y: x + y, [x ** 2 for x in self.to_list()])
        )

    def sum(self, vector):
        """Return a NVector instance as the vector sum of two vectors."""
        return self.from_list(
            [x + vector.vector[i] for i, x in self.to_list()]
        )

    def subtract(self, vector):
        """Return a NVector instance as the vector difference of two vectors."""
        return self.__sub__(vector)

    def dot(self, vector, theta=None):
        """Return the dot product of two vectors.
        If theta is given then the dot product is computed as
        v1*v1 = |v1||v2|cos(theta). Argument theta
        is measured in degrees.
        """
        if theta is not None:
            return (self.magnitude() * vector.magnitude() *
                    math.degrees(math.cos(theta)))
        return (reduce(lambda x, y: x + y,
                [x * vector.vector[i] for i, x in self.to_list()()]))

    def cross(self, vector):
        """Return a NVector instance as the cross product of two vectors"""
        return NVector((self.y * vector.z - self.z * vector.y),
                      (self.z * vector.x - self.x * vector.z),
                      (self.x * vector.y - self.y * vector.x))

    def unit(self):
        """Return a NVector instance of the unit vector"""
        return NVector(
            (self.x / self.magnitude()),
            (self.y / self.magnitude()),
            (self.z / self.magnitude())
        )

    def angle(self, vector):
        """Return the angle between two vectors in degrees."""
        return math.degrees(
            math.acos(
                self.dot(vector) /
                (self.magnitude() * vector.magnitude())
            )
        )

    def parallel(self, vector):
        """Return True if vectors are parallel to each other."""
        if self.cross(vector).magnitude() == 0:
            return True
        return False

    def perpendicular(self, vector):
        """Return True if vectors are perpendicular to each other."""
        if self.dot(vector) == 0:
            return True
        return False

    def non_parallel(self, vector):
        """Return True if vectors are non-parallel.
        Non-parallel vectors are vectors which are neither parallel
        nor perpendicular to each other.
        """
        if (self.is_parallel(vector) is not True and
                self.is_perpendicular(vector) is not True):
            return True
        return False

    def rotate(self, angle, axis=(0, 0, 1)):
        """Returns the rotated vector. Assumes angle is in radians"""
        if not all(isinstance(a, int) for a in axis):
            raise ValueError
        x, y, z = self.x, self.y, self.z

        # Z axis rotation
        if(axis[2]):
            x = (self.x * math.cos(angle) - self.y * math.sin(angle))
            y = (self.x * math.sin(angle) + self.y * math.cos(angle))

        # Y axis rotation
        if(axis[1]):
            x = self.x * math.cos(angle) + self.z * math.sin(angle)
            z = -self.x * math.sin(angle) + self.z * math.cos(angle)

        # X axis rotation
        if(axis[0]):
            y = self.y * math.cos(angle) - self.z * math.sin(angle)
            z = self.y * math.sin(angle) + self.z * math.cos(angle)

        return NVector(x, y, z)

    def to_points(self):
        """Returns an array of [x,y,z] of the end points"""
        return [self.x, self.y, self.z]

    @classmethod
    def from_points(cls, point1, point2):
        """Return a NVector instance from two given points."""
        if isinstance(point1, NPoint) and isinstance(point2, NPoint):
            displacement = point1.substract(point2)
            return cls(displacement.x, displacement.y, displacement.z)
        raise TypeError

    @classmethod
    def spherical(cls, mag, theta, phi=0):
        """Returns a NVector instance from spherical coordinates"""
        return cls(
            mag * math.sin(phi) * math.cos(theta),  # X
            mag * math.sin(phi) * math.sin(theta),  # Y
            mag * math.cos(phi)  # Z
        )

    @classmethod
    def cylindrical(cls, mag, theta, z=0):
        """Returns a NVector instance from cylindrical coordinates"""
        return cls(
            mag * math.cos(theta),  # X
            mag * math.sin(theta),  # Y
            z  # Z
        )
