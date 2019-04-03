from Nodes.CoreObject import NObject
from Nodes import CoreUtils
from Nodes.Decorators import *
from Nodes.CoreProperties import *

import global_accessor as GA


class BoundMethod(object):
    def __init__(self, owning_del=None, owner=None, o=None, fname='', fRef=None):
        CLASS_BODY(self)

        NATTR(self, '_owningDelegate', EAttrType.AT_Serializable)
        self._owningDelegate = owning_del

        NATTR(self, '_Owner', EAttrType.AT_Serializable)
        self._Owner = owner

        NATTR(self, '_ObjectRef', EAttrType.AT_Serializable)
        self._ObjectRef = o

        self._FuncRef = fRef

        NATTR(self, 'FuncName', EAttrType.AT_Serializable)
        self._FuncName = fname


    def call(self, *args, **kwargs):
        return self._FuncRef(*args, **kwargs)

    def getFuncName(self):
        return self._FuncName

    def getLinkedObject(self):
        return self._ObjectRef

    def getOwner(self):
        return self._Owner

    def __archive__(self, Ar):
        # print('BOUND METHOD OBJECTS', self._Owner, self._ObjectRef, self._owningDelegate)
        ownerID = self._Owner.getUUID() if self._Owner else NString("None")
        ObjectID = self._ObjectRef.getUUID() if self._ObjectRef else NString("None")
        Ar << ownerID
        Ar << ObjectID
        Ar << self._owningDelegate.getUUID()
        Ar << NString(self._FuncName)

    def __reader__(self, data):
        # print('BOUND METHOD DATA:', data)
        self._Owner = GA.getInstance(data[0])
        self._ObjectRef = GA.getInstance(data[1])
        self._owningDelegate = GA.getInstance(data[2])
        self._FuncRef = getattr(self._ObjectRef, data[3])
        # @TODO Finish debugging this. self._Owner is never saved / recovered for obscure reasons. It's probably stupid but I am tired.
        pass


class Delegate(NObject):
    """
    This class allows to dynamically link NObject's functions together.
    It keeps track of the objects the functions are attached to, allowing a fairly simple access of relatives.
    """
    def __init__(self, name, Owner=None):
        if Owner and not isinstance(Owner, NObject):
            raise RuntimeError("Delegate Owner must be NObject, got %s" % Owner.__class__.__name__)

        super(Delegate, self).__init__(Owner.getWorld() if Owner else None, name, Owner)

        NATTR(self, '_functions', EAttrType.AT_Serializable)
        self._functions = NArray(BoundMethod)


    def bindFunction(self, *args):
        """
        Expects either a function reference or an object and a function name string.
        :param args: either a single method, or an object instance, followed by a name string.
        """
        bError = False

        if callable(args[0]):
            owningClass = CoreUtils.UCoreUtils.get_class_that_defined_method(args[0])
            name = args[0].__name__
            self._functions.append(BoundMethod(self, self.getOwner(), owningClass, name, args[0]))
        elif isinstance(args[0], NObject):
            funcRef = getattr(args[0], args[1], None)

            if funcRef is not None and callable(funcRef):
                self._functions.append(BoundMethod(self, self.getOwner(), args[0], args[1], funcRef))
            else:
                bError = True
        else:
            bError = True

        if bError:
            raise TypeError("{input} is not a function type or NObject reference, or the passed-in function name is not valid.".format(input=str(args[0])))

    def removeFunction(self, *args):
        """
        Expects either the function reference or an object and a function name string.
        :param args: either a single method, or an object instance, followed by a name string.
        :return: No return value.
        """
        bError = False
        BoundFunc = self.findFunc(*args)
        if BoundFunc is not None:
            self._functions.remove(BoundFunc)
        else:
            bError = True

        if bError:
            raise TypeError("{input} is not a function type or NObject reference, or the passed-in function name is not valid.".format(input=str(args[0])))

    def execute(self, *args, **kwargs):
        for func in self._functions:
            func.call(*args, **kwargs)

        return

    def getBoundFunctions(self):
        return self._functions

    def findFunc(self, funcNameOrObj, obj=None):
        for bm in self._functions:
            if isinstance(funcNameOrObj, str):
                if bm.getFuncName() == funcNameOrObj:
                    if obj is not None:
                        if bm.getLinkedObject() == obj:
                            return bm
                    else:
                        return bm

            elif callable(funcNameOrObj):
                if bm.getFuncRef() == funcNameOrObj:
                    return bm

            else:
                raise TypeError("Input param 1 is not callable and is not a string.")

        return None



class DelegateSingle(Delegate):
    def __init__(self, name="", Owner=None):
        super(DelegateSingle, self).__init__(name, Owner)

    def bindFunction(self, *args):
        if len(self._functions) == 0:
            super(DelegateSingle, self).bindFunction(*args)
        else:
            raise Warning("{0} is already bound to a method.".format(str(self)))

    def removeFunction(self, *args):
        """
        /!\\ Not used by this class.
        """
        pass

    def clear(self):
        del self._functions[0]


class DelegateMulticast(Delegate):
    def __init__(self, name="", Owner=None):
        super(DelegateMulticast, self).__init__(name, Owner)


class CollectorSingle(DelegateSingle):

    def execute(self, *args, **kwargs):
        """
        /!\\ Not used by this class.
        """
        pass

    def call(self, *args, **kwargs):
        if len(self._functions) != 0:
            return self._functions[0].call(*args, **kwargs)
        else:
            print(Warning("{0} was called but is not bound to any function.".format(self.getName())))


class CollectorMulticast(Delegate):
    def execute(self, *args, **kwargs):
        results = []
        for func in self._functions:
            results.append(func.call(*args, **kwargs))

        return results





class owner(NObject):
    def __init__(self):
        super(owner, self).__init__()

class Custom(NObject):

    def printsomething(self):
        print("hey, that worked")

    def printelse(self):
        print("cool")



obj = Custom(None, 'testobj')
d = DelegateMulticast('my delegate', obj)
d.bindFunction(obj, 'getName')
a = NArray(NString)
a.append(NString('hi'))
a.append(NString('heee'))

Ar = NArchive()
Ar << obj
Ar << d
Ar << a

d2 = DelegateMulticast()
obj2 = Custom()
a2 = NArray(NString)
# print(Ar.getData())
mem = NMemoryReader(Ar.getData())

mem << obj2
mem << d2
mem << a2

print(a2)
# print(d2.getName(), obj2.getName())