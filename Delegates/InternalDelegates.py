from Nodes.CoreObject import NObject
from Nodes import CoreUtils


class BoundMethod:
    def __init__(self, owner, o, fname, fRef):
        self.__Owner = owner
        self.__ObjectRef = o
        self.__FuncRef = fRef
        self.__FuncName = fname

    def call(self, *args, **kwargs):
        return self.__FuncRef(*args, **kwargs)

    def getFuncName(self):
        return self.__FuncName

    def getLinkedObject(self):
        return self.__ObjectRef

    def getOwner(self):
        return self.__Owner


class Delegate(NObject):
    """
    This class allows to dynamically link NObject's functions together.
    It keeps track of the objects the functions are attached to, allowing a fairly simple access of relatives.
    """
    def __init__(self, name, Owner=None):
        super(Delegate, self).__init__(name, Owner)
        self._functions = []

    def bindFunction(self, *args):
        """
        Expects either a function reference or an object and a function name string.
        :param args: either a single method, or an object instance, followed by a name string.
        :return: No return value.
        """
        bError = False

        if callable(args[0]):
            owningClass = CoreUtils.UCoreUtils.get_class_that_defined_method(args[0])
            name = args[0].__name__
            self._functions.append(BoundMethod(self.getOwner(), owningClass, name, args[0]))
        elif isinstance(args[0], NObject):
            funcRef = getattr(args[0], args[1], None)

            if funcRef is not None and callable(funcRef):
                self._functions.append(BoundMethod(self.getOwner(), args[0], args[1], funcRef))
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
                if bm.FuncName == funcNameOrObj:
                    if obj is not None:
                        if bm.ObjectRef == obj:
                            return bm
                    else:
                        return bm

            elif callable(funcNameOrObj):
                if bm.FuncRef == funcNameOrObj:
                    return bm

            else:
                raise TypeError("Input param 1 is not callable and is not a string.")

        return None


class DelegateSingle(Delegate):
    def __init__(self, name, Owner=None):
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
    def __init__(self, name, Owner=None):
        super(DelegateMulticast, self).__init__(name, Owner)


class Listener(DelegateSingle):

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


class Collector(Delegate):
    def execute(self, *args, **kwargs):
        results = []
        for func in self._functions:
            results.append(func.call(*args, **kwargs))

        return results
