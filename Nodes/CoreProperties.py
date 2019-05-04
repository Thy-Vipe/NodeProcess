from __future__ import division

from functools import reduce
import math
from numbers import Real
import array, struct, collections, os, subprocess, warnings

from PySide2.QtCore import QPoint, QPointF
import global_accessor as GA
from Nodes.Decorators import *
from Nodes.WeakReferences import NWeakRef

# Define various macros...
EXPOSEDPROPNAME = "propTypes"
EXPOSED_EXTRADATA = "extra_data"
DATATYPES = {EDataType.DT_Delegate: (244, 246, 249),
             EDataType.DT_Array: (152, 153, 155),
             EDataType.DT_Dict: (229, 201, 45),
             EDataType.DT_Float: (164, 229, 45),
             EDataType.DT_Int: (45, 229, 143),
             EDataType.DT_String: (229, 45, 225),
             EDataType.DT_Struct: (35, 44, 170),
             EDataType.DT_Point: (15, 78, 224),
             EDataType.DT_Vector: (224, 185, 14),
             EDataType.DT_Script: (50, 194, 242),
             EDataType.DT_Variant: (173, 173, 173),
             EDataType.DT_Iterable: (173, 173, 173),
             EDataType.DT_Bool: (200, 10, 0),
             EDataType.DT_AttrRef: (59, 147, 206),
             EDataType.DT_Enum: (78, 135, 77)
             }

DATATYPES_STR = {"str": EDataType.DT_String,
                 "int": EDataType.DT_Int,
                 "float": EDataType.DT_Float,
                 "bool": EDataType.DT_Bool
                 }


class EAnchorType:
    """
    Enum to handle anchor types.
    """
    RelativeRelative = 0
    FixedRelative = 1
    RelativeFixed = 2
    FixedFixed = 3


class EAttrChange:
    """
    Enum for attribute change events.
    """
    AC_Added = 0
    AC_Removed = 1


class EFuncType:
    """
    Enum for func types. They can be either Callable, meaning they need an execution wire (white),
    or they can be Pure, meaning they're called as needed and do not require an execution wire.
    """
    # Used for heavy operations that require a certain amount of processing.
    FT_Callable = 0
    # Used if the logic behind the function object is simple / quick to execute
    FT_Pure = 1


class EStatus:
    # Delegate error
    kError = 1

    kSuccess = 0

    # All good
    Default = -1


class Error_Type(object):
    def __init__(self):
        pass


class NProperty(object):
    def __init__(self, *args, **kwargs):
        CLASS_PROP_BODY(self)

    def __jsonSerialize__(self, Serial: dict):
        pass

    def __jsonReader__(self, myDict: dict):
        pass

    def __archive__(self, Ar):
        pass

    def __reader__(self, data):
        pass


class TEnum(NProperty):
    def __init__(self, v=0):
        super(TEnum, self).__init__()
        self.__v = v

    def value(self):
        return self.__v

    def text(self):
        return self.__class__.from_value(self.__v)

    @classmethod
    def from_value(cls, inValue):
        for x in dir(cls):
            v = getattr(cls, x)
            if callable(v):
                continue

            if v == inValue:
                return x

    @classmethod
    def from_text(cls, v):
        for x in dir(cls):
            if x == v:
                return getattr(cls, x)

    @classmethod
    def items(cls):
        default = dir(TEnum)
        content = dir(cls)
        res = []
        for item in content:
            if item not in default:
                res.append((item, getattr(cls, item)))

        return res



class NArchive(NProperty):
    """
    Archive class. Used for serializing data into binary. Can be dumped into a binary file.
    Use the "<<" on any class that implements __archive__(Ar) to serialize the object's data.
    NArchive can be converted into byteArrays (in a tuple holding the sequence buffer and the data itself) in order to be quickly
    convertible / transmittable if needed.

    Use NMemoryReader in order to read from byte arrays or byte sequences. NArchive serializes data into byte sequences that can then be converted into
    byte arrays using NArchive.toByteArrays().
    """
    def __init__(self, inAr=None):
        super(NArchive, self).__init__()
        self._byteBuffers = [] if inAr is None else inAr
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

        elif isinstance(buffer, NArchive):
            self._byteBuffers.extend(buffer.getData())
            self.position += 1
        else:
            raise TypeError("Invalid input: buffer must be a tuple holding the buffer and the binary data.")

    def combine(self, recursiveVal=None):
        """
        Combine the entire archive into a single binary. This is a rather slow operation as it deserialize, converts and re-serializes the data.
        :return: the new archive with a combined buffer.
        """
        dataTMp = []
        for buffer, data in self._byteBuffers if not recursiveVal else recursiveVal:
            data = struct.unpack(buffer, data)
            if len(data) == 1:
                if hasattr(data[0], 'decode'):
                    data = data[0].decode()
                else:
                    data = data[0]

            tmp = (buffer, data)
            dataTMp.append(tmp)

        combinedBuffer = ''
        combinedValues = []
        for buff, value in dataTMp:
            combinedBuffer += buff
            if isinstance(value, tuple):
                combinedValues.extend(list(value))
            elif hasattr(value, 'encode'):
                combinedValues.append(value.encode())
            else:
                combinedValues.append(value)

        # print(combinedBuffer, combinedValues)
        outData = (combinedBuffer, struct.pack(combinedBuffer, *combinedValues))
        outData = [outData]

        # print(outData)

        return NArchive(outData)

    def toByteArrays(self, bFromStart=False):
        if not NArchive.ensure(self._byteBuffers, array.array):
            res = []
            for item in self._byteBuffers[self.position if not bFromStart else 0::]:
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
        return 12

    def writeToFile(self, binary_file, objName):
        # Write all the data contained in our buffer
        byteInfo = []
        int_size = NArchive.intSize()
        start_position = binary_file.seek(0, 1)
        # preallocate int_size bits to write the chunk size at the end.
        count = binary_file.write(b'0'.zfill(int_size))
        for buffer, data in self.getData():
            byteInfo.append(binary_file.write(buffer.encode()))
            count += byteInfo[-1]
            byteInfo.append(binary_file.write(data))
            count += byteInfo[-1]
            binary_file.flush()

        # print(byteInfo)

        # Write header of this file at the end, that way we know where the 'block' exactly begins.
        binLen = len(byteInfo)
        buff = '%dI' % binLen
        # write position data from list
        byteInfoLen = binary_file.write(struct.pack(buff, *byteInfo)); count += byteInfoLen
        # write length of position data
        count += binary_file.write(byteInfoLen.to_bytes(int_size, 'big', signed=False))
        # write length of buffer for position data, into int_size bits
        count += binary_file.write(binLen.to_bytes(int_size, 'big', signed=False))
        # write object name
        nameLen = binary_file.write(objName.encode()); count += nameLen

        # write object name length, into int_size bits
        add = binary_file.write(nameLen.to_bytes(int_size, 'big', signed=False)); count += add
        # now use the preallocated 12 bits to write the length of this chunk.
        binary_file.seek(start_position, 0)
        binary_file.write(count.to_bytes(int_size, 'big', signed=False))
        binary_file.seek(count + start_position)
        binary_file.flush()

    @staticmethod
    def decodeFile(binary_file):
        pos = 0
        output = {}
        all_data = binary_file.read()
        # print(all_data)
        j = len(all_data)
        # print(j)
        int_size = NArchive.intSize()

        while pos < j:
            # Get the header for chunk x
            binary_file.seek(pos, 0)
            chnkSize = int.from_bytes(binary_file.read(int_size), 'big', signed=False)
            binary_file.seek(pos+chnkSize-int_size, 0)
            name_len = int.from_bytes(binary_file.read(int_size), 'big', signed=False)
            binary_file.seek(-(name_len+int_size), 1)
            objName = binary_file.read(name_len).decode()
            binary_file.seek(-(int_size+name_len), 1)
            posBufferLen = int.from_bytes(binary_file.read(int_size), 'big', signed=False)
            binary_file.seek(-int_size*2, 1)
            posDataLen = int.from_bytes(binary_file.read(int_size), 'big', signed=False)
            binary_file.seek(-(int_size+posDataLen), 1)
            posData = struct.unpack('%dI' % posBufferLen, binary_file.read(posDataLen))

            # get the serialized properties data
            s = pos + int_size
            binary_file.seek(s, 0)  # move back at the start of the chunk, offset with the chunk size data
            data = []
            buffers = []
            i = 0
            for p in posData:
                # print(binary_file.read(p))
                if i % 2 == 0:
                    buffers.append(binary_file.read(p).decode())
                else:
                    data.append(binary_file.read(p))
                binary_file.seek(s+p, 0)
                i += 1
                s += p

            outdata = []
            for buffer, binary in zip(buffers, data):
                outdata.append((buffer, binary))

            output[objName] = outdata
            # print(pos)
            pos += chnkSize

        return output


class NMemoryReader(NArchive):
    """
    Use NMemoryReader to deserialize data from byte arrays or byte sequences.
    Upon construction, NMemoryReader expects a tuple of byteArrays or byte sequences to operate with.
    Use "<<" to deserialize data from NMemoryReader. Make sure to deserialize data in the exact order it was serialized with,
    or the results will be incorrect.
    Classes must implement __reader__(data) or __binaryreader__(data) in order to read data from NMemoryReader.
    """
    def __init__(self, inBuffer: (tuple, array.array)):
        super(NMemoryReader, self).__init__()
        bUseBytes = False
        if len(inBuffer) != 0:
            if NMemoryReader.ensure(inBuffer, array.array):
                self._byteBuffers = inBuffer
                bUseBytes = True
            elif NMemoryReader.ensure(inBuffer, tuple):
                self._byteBuffers = inBuffer
            else:
                raise RuntimeError("%s is not properly initialized. Input buffer is invalid." % self.__class__.__name__)

        self.__memoryType = int(bUseBytes)


    def __lshift__(self, other):
        self._deserialize(other)

    def _deserialize(self, item):
        if hasattr(item, "__reader__"):
            # If memory is bytes buffer
            if self.__memoryType == 1:
                data = self._byteBuffers[self.position]
                unpackedBin = struct.unpack_from(data[0], data[1], 0)
                item.__reader__(unpackedBin)

            # If memory is bytes sequence
            elif self.__memoryType == 0:
                data = self._byteBuffers[self.position]
                unpackedBin = struct.unpack(data[0], data[1])
                item.__reader__(unpackedBin)

            self.position += 1

        elif hasattr(item, '__binaryreader__'):
            end = item.__binaryreader__(self.toByteArrays())
            if not end:
                raise RuntimeError("__binaryreader__ in %s must return the end position of its read sequence." % item.__class__.__name__)
            # mark end of data.
            self.position += end

        else:
            raise TypeError("%s does not implement __reader__(data) or __binaryreader__(data)." % item.__class__.__name__)

    def seek(self, pos):
        if pos < len(self._byteBuffers):
            self.position = pos
        else:
            raise IndexError("Ensure condition failed: position < len(byteBuffer) != True")


class NMutable(NProperty):
    """
    A simple mutable object holding wildcard data. Is serializable if buffer is defined.
    """
    def __init__(self, v, buffer=''):
        super(NMutable, self).__init__()
        self._data = v
        self._buffer = buffer

    def get(self):
        return self._data

    def set(self, v):
        self._data = v

    def __archive__(self, Ar):
        if self._buffer != '':
            Ar += (self._buffer, struct.pack(self._buffer, self._data))
        else:
            raise RuntimeError("Buffer for %s is not defined." % self.__class__.__name__)

    def __reader__(self, data):
        self._data = data

    def __jsonSerialize__(self, Serial: dict):
        Serial['_data'] = self._data

    def __jsonReader__(self, myDict: dict):
        self._data = myDict['_data']

    def __repr__(self):
        return str(self._data)

    def __str__(self):
        return str(self.get())

    def __int__(self):
        return int(self.get())

    def __float__(self):
        return float(self.get())


class NNumeric(NMutable):

    def __add__(self, other):
        if isinstance(other, (float, int)):
            return self.__class__(self._data + other)
        elif isinstance(other, NNumeric):
            return self.__class__(self._data + other._data)
        else:
            raise TypeError("Invalid operand type for NNumeric: %s" % other.__class__.__name__)

    def __mul__(self, other):
        if isinstance(other, (float, int)):
            return self.__class__(self._data * other)
        elif isinstance(other, NNumeric):
            return self.__class__(self._data * other._data)
        else:
            raise TypeError("Invalid operand type for NNumeric: %s" % other.__class__.__name__)

    def __truediv__(self, other):
        if isinstance(other, (float, int)):
            return self.__class__(self._data / other)
        elif isinstance(other, NNumeric):
            return self.__class__(self._data / other._data)
        else:
            raise TypeError("Invalid operand type for NNumeric: %s" % other.__class__.__name__)

    def __floordiv__(self, other):
        if isinstance(other, (float, int)):
            return self.__class__(self._data // other)
        elif isinstance(other, NNumeric):
            return self.__class__(self._data // other._data)
        else:
            raise TypeError("Invalid operand type for NNumeric: %s" % other.__class__.__name__)

    def __neg__(self):
        return self.__class__(-self._data)

    def __sub__(self, other):
        if isinstance(other, (float, int)):
            return self.__class__(self._data - other)
        elif isinstance(other, NNumeric):
            return self.__class__(self._data - other._data)
        else:
            raise TypeError("Invalid operand type for NNumeric: %s" % other.__class__.__name__)

    def __lt__(self, other):
        if isinstance(other, (float, int)):
            return self._data < other
        elif isinstance(other, NNumeric):
            return self._data < other._data
        else:
            raise TypeError("Invalid operand type for NNumeric: %s" % other.__class__.__name__)

    def __le__(self, other):
        if isinstance(other, (float, int)):
            return self._data <= other
        elif isinstance(other, NNumeric):
            return self._data <= other._data
        else:
            raise TypeError("Invalid operand type for NNumeric: %s" % other.__class__.__name__)

    def __eq__(self, other):
        if isinstance(other, (float, int)):
            return self._data == other
        elif isinstance(other, NNumeric):
            return self._data == other._data
        else:
            raise TypeError("Invalid operand type for NNumeric: %s" % other.__class__.__name__)

    def __ne__(self, other):
        if isinstance(other, (float, int)):
            return self._data != other
        elif isinstance(other, NNumeric):
            return self._data != other._data
        else:
            raise TypeError("Invalid operand type for NNumeric: %s" % other.__class__.__name__)

    def __ge__(self, other):
        if isinstance(other, (float, int)):
            return self._data > other
        elif isinstance(other, NNumeric):
            return self._data > other._data
        else:
            raise TypeError("Invalid operand type for NNumeric: %s" % other.__class__.__name__)

    def __gt__(self, other):
        if isinstance(other, (float, int)):
            return self._data >= other
        elif isinstance(other, NNumeric):
            return self._data >= other._data
        else:
            raise TypeError("Invalid operand type for NNumeric: %s" % other.__class__.__name__)

    def __float__(self):
        return float(self._data)

    def __int__(self):
        return int(self._data)

    def __bool__(self):
        return bool(self._data)


class NInt(NNumeric):
    """
    A simple mutable integer. Is serializable.
    """
    def __init__(self, v: int = 0):
        super(NInt, self).__init__(v, 'i')


class NFloat(NNumeric):
    """
    A simple mutable float. Is serializable.
    """
    def __init__(self, v: float = 0.0):
        super(NFloat, self).__init__(v, 'd')

    def __float__(self):
        return self.get()


class NVariant(NMutable):
    def __init__(self, v=None):
        super(NVariant, self).__init__(v, '')
        self._type = EDataType.DT_Variant

        if v:
            self.set(v)

    def set(self, v):
        super(NVariant, self).set(v)

        for k, val in DATACLASSES.items():
            if type(v) is val:
                self._type = k
                return

        raise TypeError("%s is not supported by NVariant." % v.__class__.__name__)

    def type_(self):
        return self._type


class ByRefVar(NProperty):
    def __init__(self, obj: object = None, var: str = ''):
        """
        Create an object that references a property on an object.
        :param obj: The object reference. A weak reference to this object will be created when  this class is initialized.
            The object MUST be valid or an exception will be raised.
        :param var: The attribute / property name string.
        """
        super(ByRefVar, self).__init__()

        self.objectRef = NWeakRef(obj) if obj else None
        self.property = var

    def set(self, value):
        if isinstance(self.objectRef, str):
            self.__recoverObject(str(self.objectRef))

        if self.objectRef and self.objectRef.isValid():
            setattr(self.objectRef(), self.property, value)
            return 0

        warnings.warn("ByRefVar: referenced object is no longer valid!", UserWarning)
        return 1

    def get(self):
        if isinstance(self.objectRef, str):
            self.__recoverObject(str(self.objectRef))

        if self.objectRef is not None and self.objectRef.isValid():
            return getattr(self.objectRef(), self.property)

    def __str__(self):
        return str(self.get())

    def __jsonSerialize__(self, Serial: dict):
        Serial['linking_object'] = self.objectRef().getUUID().toString() if (self.objectRef and self.objectRef.isValid()) else None
        Serial['linking_property'] = self.property

    def __jsonReader__(self, myDict: dict):
        self.__recoverObject(myDict['linking_object'])
        self.property = myDict['linking_property']

    def __recoverObject(self, uuid: str):
        obj = g_a.getInstance(uuid)
        if obj:
            self.objectRef = NWeakRef(obj)


class NStatus(NMutable):
    """
    Result status by reference. Used for delegates and such.
    Default state is EStatus.Default - meaning it was not modified.
    """
    def __init__(self, v: EStatus = EStatus.Default):
        super(NMutable, self).__init__(v, 'I')

    def isError(self):
        return self._data != EStatus.kSuccess and not self._data == EStatus.Default


class NScript(object):
    """
    Class representing a dynamic script to be executed with the python interpreter.
    It is fully serializable as string, but does not preserve the class references,
    and therefore needs to be spawned non-dynamically with the expected globals, locals and extras.
    """
    def __init__(self, script, global_vars=None, local_vars=None, **extraVars):
        self._script = ''
        self.setCode(script)
        self._globals = global_vars if global_vars else {}
        self._locals = local_vars if local_vars else {}
        self._scriptThread = None
        self._bAsync = False

        for k, v in extraVars.items():
            self._locals[k] = v

    def exec(self, bFromThread=False):
        if not self._bAsync or bFromThread:
            exec(self._script, self._globals, self._locals)

        elif not bFromThread and self._bAsync:
            self._scriptThread = g_a.findClass('NThread')("tempThread_%s" % id(self), bDestroyAfterWork=True)
            self._scriptThread.bindFinishedEvent(self, '_OnFinishedKillThread')
            self._scriptThread.asyncTask(self)
            self._scriptThread.start()

        return 0

    def __archive__(self, Ar):
        Ar << NString(self._script)

    def __reader__(self, data):
        new = NString()
        new.__reader__(data)
        self._script = new.get()

    def __jsonSerialize__(self, Serial: dict):
        Serial['script'] = self._script

    def __jsonReader__(self, myDict: dict):
        self._script = myDict['script']

    def setCode(self, code: str):
        self._script = code

    def getCode(self):
        return self._script

    def addLocal(self, item: dict):
        for k, v in item.items():
            self._locals[k] = v

    def removeLocal(self, item: list):
        for k in item:
            del self._locals[k]

    def setAsync(self, v: bool):
        self._bAsync = v

    def getAsync(self):
        return self._bAsync

    def _OnFinishedKillThread(self, *args):
        g_a.killInstance(self._scriptThread.getUUID())
        print("Thread finished work for script %s" %self)


class NBatchScript(NScript):
    def __init__(self, script, global_vars=None, local_vars=None, **extraVars):
        self._tempPath = os.environ['tmp']
        self._scriptdir = '%s\\tmpscript_%d.ts.bat' % (self._tempPath, id(self))

        super(NBatchScript, self).__init__(script, global_vars, local_vars, **extraVars)

    def exec(self, bFromThread=False):
        if not self._bAsync or bFromThread:
            r = subprocess.call(self._scriptdir, shell=False, stdin=subprocess.DEVNULL)
            if not bFromThread:
                print("Batch script <%d> finished with exit code %s." % (id(self), r))

            return r

        elif not bFromThread and self._bAsync:
            self._scriptThread = g_a.findClass('NThread')("tempThread_%s" % id(self), bDestroyAfterWork=True)
            self._scriptThread.bindFinishedEvent(self, '_OnFinishedKillThread')
            self._scriptThread.asyncTask(self)
            self._scriptThread.start()

        return 0

    def setCode(self, code: str):
        with open(self._scriptdir, 'w') as f:
            f.write(code)
            f.close()

        self._script = code

    def __del__(self):
        os.remove(self._scriptdir)

    def _OnFinishedKillThread(self, *args):
        g_a.killInstance(self._scriptThread.getUUID())
        print("Batch script <%d> finished with exit code %s." % (id(self), args[0]))


class NArray(collections.UserList, NProperty):
    """
    NArray is a serializable array, that is mutable and behaves exactly like a list that would enforce a specific type.
    Upon deserialization, NArray re-spawns the objects that were contained in it, and recovers the states they were in, according to their __reader__(data)
    """
    def __init__(self, objectType):
        super(NArray, self).__init__()
        self._typ = objectType


    def append(self, item):
        if isinstance(item, self._typ):
            super(NArray, self).append(item)
        else:
            raise TypeError("Input isn't valid. type is %s, input is %s" % (item.__class__.__name__, self._typ.__name__))

    def extend(self, arr):
        if any(map(lambda x: not isinstance(x, self._typ), arr)):
            raise TypeError("Input isn't a single-typed list. type is %s, input is %s" % (arr.__class__.__name__, self._typ.__name__))
        else:
            super(NArray, self).extend(arr)

    def __archive__(self, Ar):
        OwnAr = NArchive()
        OwnAr << NString('array_begin')  # write header for array
        OwnAr << NInt(len(self))
        OwnAr << NString(self._typ.__name__)

        for item in self:
            OwnAr << item

        OwnAr << NString('array_end')

        Ar += OwnAr.combine()

    def __binaryreader__(self, data: (list, tuple)):
        # isinstance(data[0], int) would be true if this array is nested into an other node. If it is standalone it will not require such.

        if (len(data) == 2 and not isinstance(data[0], int)) or (len(data) == 1 and len(data[0]) == 2 and not isinstance(data[0], int)):
            values = struct.unpack_from(data[0][0], data[0][1], 0)[1:-1]
            values = list(map(lambda x: x.decode() if hasattr(x, 'decode') else x, values))

        else:
            values = list(map(lambda x: x.decode() if hasattr(x, 'decode') else x, data))

        count, typ = values[0], values[1]
        # print(count, typ)
        self._typ = GA.findClass(typ)
        dds_data = values[2::]
        arr_count = len(dds_data) // count
        b_len = str(len(typ)).__len__(); buffer = data[0][0][2+b_len::]
        if self._typ:
            for idx in range(count):
                new = self._typ()
                if hasattr(new, '__reader__'):
                    new.__reader__(dds_data[idx*arr_count:idx*arr_count+arr_count])

                elif hasattr(new, '__binaryreader__'):
                    # @TODO Add support for binary deserialization of nested objects from NArray.
                    # binary = struct.pack(, *dds_data[idx*arr_count:idx*arr_count+arr_count])
                    warnings.warn("Binary deserialization of nested items in NArray is not yet supported.", RuntimeWarning)
                    break

                self.append(new)

        return 1



class NString(collections.UserString, NProperty):
    """
    Extension of class "str" with more methods used for NodeProcess.
    We're using a wrapper for str here, because str isn't easy to work with.
    The main difference is that NString is MUTABLE.
    """
    def __init__(self, seq: str = ''):
        super(NString, self).__init__(seq)

        CLASS_PROP_BODY(self)

    def __archive__(self, Ar: NArchive):
        """
        Serialize NString into a byte buffer.
        :param Ar: The input archive to serialize into. Modifies the input directly.
        :type Ar: NArchive.
        """
        encoding = '%ds' % len(self)
        s = struct.Struct(encoding)
        buffer = s.pack(self.data.encode())
        Ar += (encoding, buffer)

    def __reader__(self, data: (list, tuple, str)):
        """
        Deserialize NString from bytes / get from value.
        :param data: the data to read from.
        :type data: tuple from unpacked struct or str.
        """
        if isinstance(data, (tuple, list)):
            self.data = data[0].decode() if not isinstance(data[0], str) else data[0]
        else:
            self.data = data

    @staticmethod
    def toNString(inObject):
        """
        Casts a string/stringifiable object into NString.
        :param inObject: The object to "cast" from
        :return: The new NString.
        """
        return NString(str(inObject))

    def copy(self):
        return NString(self.data)

    def get(self):
        return self.data

    def set(self, string: str):
        self.data.replace(self.data, string)

    def toString(self):
        return str(self)


class NPoint2D(NProperty):
    """
    Npoint2D: Represents a point in 2D space.
    """
    def __init__(self, x=0.0, y=0.0, bForceInt=False):
        super(NPoint2D, self).__init__()

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

    def __jsonReader__(self, myDict: dict):
        self.x = myDict['x']
        self.y = myDict['y']
        self.__IsInt = myDict['isint']

    def __jsonSerialize__(self, Serial: dict):
        Serial['x'] = self.x
        Serial['y'] = self.y
        Serial['isint'] = self.__IsInt

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

    def __truediv__(self, other):
        if isinstance(other, NPoint2D):
            if not self.__IsInt:
                return NPoint2D(float(self.x) / float(other.x), float(self.y) / float(other.y), self.__IsInt)
            else:
                return NPoint2D(self.x / other.x, self.y / other.y, self.__IsInt)
        # ...
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


class NPoint(NProperty):
    """NPoint class: Represents a point in the x, y, z space."""
    def __init__(self, x=0.0, y=0.0, z=0.0):
        super(NPoint, self).__init__()

        self.x = x
        self.y = y
        self.z = z

    def __archive__(self, Ar):
        s = struct.Struct('3d')
        Ar += ('3d', s.pack(self.x, self.y, self.z))

    def __reader__(self, data):
        self.x, self.y, self.z = data

    def __jsonSerialize__(self, Serial: dict):
        Serial['x'] = self.x
        Serial['y'] = self.y
        Serial['z'] = self.z

    def __jsonReader__(self, myDict: dict):
        self.x = myDict['x']
        self.y = myDict['y']
        self.z = myDict['z']

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

    def equals(self, pt, tolerance=1e-3):
        return (
            self.x - tolerance <= self.x <= self.x + tolerance and
            self.y - tolerance <= self.y <= self.y + tolerance and
            self.z - tolerance <= self.z <= self.z + tolerance
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
        if isinstance(vec, NVector):
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
        return self.from_list([x + number for x in (self.x, self.y, self.z)])

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
                [x * vector.vector[i] for i, x in self.to_list()]))

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
        if (self.parallel(vector) is not True and
                self.perpendicular(vector) is not True):
            return True
        return False

    def rotate(self, angle, axis=(0, 0, 1)):
        """Returns the rotated vector. Assumes angle is in radians"""
        if not all(isinstance(a, int) for a in axis):
            raise ValueError
        x, y, z = self.x, self.y, self.z

        # Z axis rotation
        if axis[2]:
            x = (self.x * math.cos(angle) - self.y * math.sin(angle))
            y = (self.x * math.sin(angle) + self.y * math.cos(angle))

        # Y axis rotation
        if axis[1]:
            x = self.x * math.cos(angle) + self.z * math.sin(angle)
            z = -self.x * math.sin(angle) + self.z * math.cos(angle)

        # X axis rotation
        if axis[0]:
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


DATACLASSES = {EDataType.DT_Delegate: None,
               EDataType.DT_Array: NArray,
               EDataType.DT_Dict: dict,
               EDataType.DT_Float: NFloat,
               EDataType.DT_Int: NInt,
               EDataType.DT_String: NString,
               EDataType.DT_Struct: NVariant,
               EDataType.DT_Point: NPoint,
               EDataType.DT_Vector: NVector,
               EDataType.DT_Script: NScript,
               EDataType.DT_Variant: NVariant,
               EDataType.DT_Iterable: list,
               EDataType.DT_Bool: bool,
               EDataType.DT_AttrRef: ByRefVar,
               EDataType.DT_Enum: TEnum
               }

CLASSTYPES = {str: EDataType.DT_String,
              NString: EDataType.DT_String,
              int: EDataType.DT_Int,
              NInt: EDataType.DT_Int,
              float: EDataType.DT_Float,
              NFloat: EDataType.DT_Float,
              list: EDataType.DT_Iterable,
              tuple: EDataType.DT_Iterable,
              NArray: EDataType.DT_Iterable,
              bool: EDataType.DT_Bool,
              NPoint: EDataType.DT_Point,
              NVariant: EDataType.DT_Variant,
              NVector: EDataType.DT_Vector,
              NScript: EDataType.DT_Script,
              NBatchScript: EDataType.DT_Script,
              ByRefVar: EDataType.DT_AttrRef
              }
