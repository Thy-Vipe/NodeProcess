
import multiprocessing, sys, os
from Nodes.Decorators import *
from Delegates.InternalDelegates import *
from Nodes.CoreProperties import *
from Nodes.CoreObject import *


class NWorld(NObject):
    """
        This is the main object that is ultimately the base of every logic going on in this software.
        It runs independently from the Ui parts of the code, and handles the logical side of it.
    """
    def __init__(self):
        super(NWorld, self).__init__(name="Main")
        self.CPU_COUNT = multiprocessing.cpu_count()
        # Can be defined when the window is spawned.
        self._WindowReference = None
        self._graphReference = None
        self._registered_objects = {}

    def getInterfaceRef(self):
        """
        Get the main window reference.
        :return: A reference to the main window instance. It can be None if the program is running with no gui.
        """
        return self._WindowReference

    def getGraphRef(self):
        """
        Get the graph, which should be nested in the main window.
        :return: A reference to the graph instance. It can be None.
        """
        return self._graphReference

    def _setGraph(self, InObj):
        """
        Should be called in child classes. Pass the reference of the graph.
        :param InObj: The graph reference.
        """
        self._graphReference = InObj

    def spawnInterface(self):
        """
        Is expected to be overridden in subclasses.
        """
        pass

    def registerObjectWithWorld(self, obj):
        if isinstance(obj, NObject):
            self._registered_objects[obj.getUUID()] = obj
        else:
            raise TypeError("%s is not of type NObject." % obj.__class__.__name__)


class NScript(object):
    """
    Class representing a dynamic script to be executed with the python interpreter.
    It is fully serializable as string, but does not preserve the class references,
    and therefore needs to be spawned non-dynamically with the expected globals, locals and extras.
    """
    def __init__(self, script, global_vars=None, local_vars=None, **extraVars):
        self._script = script
        self._globals = global_vars if global_vars else {}
        self._locals = local_vars if local_vars else {}

        for k, v in extraVars.items():
            self._locals[k] = v

    def exec(self):
        exec(self._script, self._globals, self._locals)

    def __archive__(self, Ar):
        Ar << NString(self._script)

    def __reader__(self, data):
        new = NString()
        new.__reader__(data)
        self._script = new.get()


class NDynamicAttr(NObject):
    """
    This is an "attribute object" that can be spawned dynamically into a class. It allows to hold and retrieve wildcard data from such.
    Any property that isn't a function flagged as Property using @Property(..) must use this class in order to be connectible / readable.
    """
    def __init__(self, name, initialValue=None, Owner=None):
        super(NDynamicAttr, self).__init__(name, Owner)

        self._value = initialValue
        self._valueChanged = Delegate("%s_ValueChangedDelegate" % self.getName(), self)

        # Becomes true whenever the input of this attribute is connected.
        self._hasPlug = False
        self._plugDelegate = CollectorSingle("%s_ValueQueryListener" % self.getName(), self)

    def set(self, value, bMute=False):
        self._value = value
        if not bMute:
            self._valueChanged.execute(value)

    def get(self, bUpdate=True):
        if bUpdate:
            self._value = self._plugDelegate.call()
        return self._value

    def hasPlug(self):
        return self._hasPlug

    def connect(self, other):
        if isinstance(other, NDynamicAttr):
            self._plugDelegate.bindFunction(other.get)
            other.getOutDelegate().bindFunction(self.set)
        elif callable(other) and hasattr(other, EXPOSEDPROPNAME) and EPropType.PT_Readable in getattr(other, EXPOSEDPROPNAME):
            self._plugDelegate.bindFunction(other)

    def getOutDelegate(self):
        return self._valueChanged


class NFunctionBase(NObject):
    def __init__(self, FuncName, Owner=None, FuncType=EFuncType.FT_Callable):
        super(NFunctionBase, self).__init__(name=FuncName, owner=Owner)

        self._exposedPropsValues = {}

        NATTR(self, '_thenDelegate', EAttrType.AT_Serializable, EAttrType.AT_SingleCastDelegate)
        self._thenDelegate = DelegateSingle("ThenDelegate_%s" % self.getName())

        self._funcType = FuncType

        if FuncType == EFuncType.FT_Pure:
            del self.execute; del self.bindThenTo; del self.then


    @Property(EPropType.PT_FuncDelegateIn)
    def execute(self):
        self.then()

    @Property(EPropType.PT_FuncDelegateOut)
    def then(self):
        self._thenDelegate.execute()

    def bindThenTo(self, obj: NObject, funcname: str):
        func = getattr(obj, funcname)
        # <then> cannot be bound to non-DelegateIn functions if the property it's being attached to is exposed to nodes.
        bHasExposedProp = hasattr(func, EXPOSEDPROPNAME)
        if bHasExposedProp and func.propType == EPropType.PT_FuncDelegateIn:
            self._thenDelegate.bindFunction(obj, funcname)
        elif not bHasExposedProp:
            self._thenDelegate.bindFunction(obj, funcname)

    def type_(self):
        return self._funcType
