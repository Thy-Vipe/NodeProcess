from Nodes.CoreObject import NObject, NWeakRef, NWeakMethod
from Nodes import CoreUtils
from Nodes.Decorators import *
from Nodes.CoreProperties import *
import global_accessor as GA
import warnings


class BoundMethod(object):
    def __init__(self, owning_del=None, owner=None, o=None, fname='', fRef=None):
        CLASS_BODY(self)

        NATTR(self, '_owningDelegate', EAttrType.AT_Serializable)
        self._owningDelegate = NWeakRef(owning_del)

        NATTR(self, '_Owner', EAttrType.AT_Serializable)
        self._Owner = NWeakRef(owner)

        NATTR(self, '_ObjectRef', EAttrType.AT_Serializable)
        self._ObjectRef = NWeakRef(o)

        self._FuncRef = NWeakMethod(fRef)

        NATTR(self, 'FuncName', EAttrType.AT_Serializable)
        self._FuncName = fname


    def call(self, ResultStatus, *args, **kwargs):
        if self._FuncRef:
            ResultStatus.set(EStatus.kSuccess)
            return self._FuncRef()(*args, **kwargs)
        else:
            # Mark current item for garbage collection if function reference is dead.
            ResultStatus.set(EStatus.kError)

    def getFuncName(self):
        return self._FuncName

    def getLinkedObject(self):
        return self._ObjectRef()

    def getOwner(self):
        return self._Owner()

    def getDelegate(self):
        return self._owningDelegate()

    def kill(self):
        """
        Kill this connection and remove it from the delegate.
        """
        print('Disconnecting %s' % str(self))
        self._owningDelegate().removeFunction(self)

    def _onConnectionDead(self, weakRef):
        self._owningDelegate().connectionDied(self)

    def __archive__(self, Ar):
        # print('BOUND METHOD OBJECTS', self._Owner, self._ObjectRef, self._owningDelegate)
        ownerID = self._Owner().getUUID() if self._Owner and self._Owner.isValid() else NString("None")
        ObjectID = self._ObjectRef().getUUID() if self._ObjectRef and self._ObjectRef.isValid() else NString("None")
        Ar << ownerID
        Ar << ObjectID
        Ar << self._owningDelegate().getUUID()
        Ar << NString(self._FuncName)

    def __reader__(self, data):
        # print('BOUND METHOD DATA:', data)
        ownerObj = GA.getInstance(data[0])
        linkedObj = GA.getInstance(data[1])
        owningDel = GA.getInstance(data[2])
        funcObj = getattr(self._ObjectRef(), data[3])
        self._Owner = NWeakRef(ownerObj) if ownerObj else None
        self._ObjectRef = NWeakRef(linkedObj) if linkedObj else None
        self._owningDelegate = NWeakRef(owningDel) if owningDel else None
        self._FuncRef = NWeakMethod(funcObj) if funcObj else None
        pass


class Delegate(NObject):
    """
    This class allows to dynamically link NObject's functions together.
    It keeps track of the objects the functions are attached to, allowing a fairly simple access of relatives.
    """
    def __init__(self, name, Owner=None, **kwargs):
        if Owner and not isinstance(Owner, NObject):
            raise RuntimeError("Delegate Owner must be NObject, got %s" % Owner.__class__.__name__)

        super(Delegate, self).__init__(world=Owner.getWorld() if Owner else None, name=name, owner=Owner, UseHardRef=True)

        NATTR(self, '_functions', EAttrType.AT_Serializable)
        self._functions = NArray(BoundMethod)

        self._mode = kwargs.get('mode', 0)  # Can be 0 or 1. If mode is 1, Delegate will be destroyed once all functions are cleared.


    def bindFunction(self, *args):
        """
        Expects either a function reference or an object and a function name string.
        :param args: either a single method, or an object instance, followed by a name string.
        """
        bError = False
        new = None
        if callable(args[0]):
            owningClass = args[0].__globals__.get('obj', None)
            name = args[0].__name__
            new = BoundMethod(self, self.getOwner(), owningClass, name, args[0])
            self._functions.append(new)

        elif not isinstance(args[0], str):
            funcRef = getattr(args[0], args[1], None)
            if funcRef is not None and callable(funcRef):
                new = BoundMethod(self, self.getOwner(), args[0], args[1], funcRef)
                self._functions.append(new)

            elif funcRef and hasattr(funcRef, 'set'):
                new = BoundMethod(self, self.getOwner(), args[0], args[1], funcRef.set)
                self._functions.append(new)

            else:
                bError = True
        else:
            bError = True

        if bError:
            raise TypeError("{input} is not a function type or NObject reference, or the passed-in function name is not valid.".format(input=str(args[0])))

        if len(args) == 3 and isinstance(args[2], NStatus):
            args[2].set(EStatus.kSuccess if not bError else EStatus.kError)

        return new

    def removeFunction(self, *args):
        """
        Expects either the function reference, an object and a function name string or the BoundMethod object instance.
        :param args: either a single method, or an object instance, followed by a name string.
        :return: No return value.
        """
        bError = False
        BoundFunc = self.findFunc(*args) if not isinstance(args[0], BoundMethod) else args[0]
        if BoundFunc:
            self._functions.remove(BoundFunc)
        else:
            bError = True

        if bError:
            raise TypeError("{input} is not a function type or NObject reference, or the passed-in function name is not valid.".format(input=str(args[0])))

        if self._mode == 1:
            if len(self._functions) == 0:
                g_a.killInstance(self.getUUID())
                pass

    def execute(self, *args, **kwargs):
        garbageFunctions = []
        for func in self._functions:
            Status = NStatus()
            func.call(Status, *args, **kwargs)

            if Status.get() != EStatus.kSuccess:
                garbageFunctions.append(func)

        for idx in range(len(garbageFunctions)).__reversed__():
            item = garbageFunctions.pop(idx)
            del item


        return

    def getBoundFunctions(self):
        """
        Get a list of weak references pointing to the bound function objects of this delegate.
        :return: List of NWeakRef objects pointing to the bound functions.
        """
        return [NWeakRef(func) for func in self._functions]

    def findFunc(self, funcNameOrObj, obj=None):
        for bm in self._functions:
            if isinstance(funcNameOrObj, str):
                if bm.getFuncName() == funcNameOrObj:
                    if obj is not None:
                        if bm.getLinkedObject() == obj:
                            return bm
                    else:
                        raise RuntimeError("Passed-in function is a string, but no owning object reference was passed for it.")

            elif callable(funcNameOrObj):
                if bm.getFuncRef() == funcNameOrObj:
                    return bm

            else:
                raise TypeError("Input param 1 is not callable and is not a string.")

        return None

    def connectionDied(self, connection):
        self._functions.remove(connection)
        print('Deleted connection %s' % str(connection))

    def clearAll(self):
        self._functions.clear()


class DelegateSingle(Delegate):
    def __init__(self, name="", Owner=None):
        super(DelegateSingle, self).__init__(name, Owner)

    def bindFunction(self, *args):
        if self._functions.__len__() == 0:
            return super(DelegateSingle, self).bindFunction(*args)
        else:
            warnings.warn("{0}, named {1} is already bound to a method.".format(str(self), self.getName().toString()))

    def removeFunction(self, *args):
        """
        /!\\ Not used by this class.
        """
        self.clear()

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
            status = NStatus()
            res = self._functions[0].call(status, *args, **kwargs)
            if not status.isError():
                return res
            else:
                del self._functions[0]
                return None
        else:
            print("{0} was called but is not bound to any function.".format(self.getName()))

    def isBound(self):
        return len(self._functions) != 0


class CollectorMulticast(Delegate):
    def execute(self, *args, **kwargs):
        results = []
        garbage = []
        for func in self._functions:
            status = NStatus()
            res = func.call(status, *args, **kwargs)
            if not status.isError():
                results.append(res)
            else:
                garbage.append(func)

        for idx in range(len(garbage)).__reversed__():
            item = garbage.pop(idx)
            del item

        return results
