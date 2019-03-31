from __future__ import division

from functools import reduce
import math
from numbers import Real

from PySide2.QtCore import QPoint, QPointF

class NArchive(object):
    def __init__(self):
        super(NArchive, self).__init__(self)
        self.__dataBinary = []

    def addData(self, binary):
        pass


class NString(str):
    """
    Extension of class "str" with more methods used for NodeProcess.
    """
    def __new__(cls, content):
        return str.__new__(cls, content)

    def __lshift__(self, other):
        if isinstance(other, NArchive):
            other.addData(self.encode())

    def __rshift__(self, other):
        raise ArithmeticError("Wrong operand order for serialization.")

    @staticmethod
    def fromString(inString):
        """
        Casts a string/stringifiable object into NString.
        :param inString: The string to cast from
        :return: The new NString.
        """
        return NString(str(inString))


class NPoint2D(object):
    """
    Npoint2D: Represents a point in 2D space.
    """
    def __init__(self, x=0, y=0, bForceInt=False):
        self.x = x
        self.y = y
        self.__IsInt = bForceInt

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
    def __init__(self, x, y, z=0):
        self.x = x
        self.y = y
        self.z = z

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

    def __init__(self, x, y, z):
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
        return "{0},{1},{2}".format(self.x, self.y, self.z)

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