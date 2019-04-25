
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


class NDynamicAttr(NObject):
    """
    This is an "attribute object" that can be spawned dynamically into a class. It allows to hold and retrieve wildcard data from such.
    Any property that isn't a function flagged as Property using @Property(..) must use this class in order to be connectible / readable.
    """
    def __init__(self, name: (str, NString), dataType: EDataType, initialValue=None, Owner=None, **kwargs):
        super(NDynamicAttr, self).__init__(name=name, owner=Owner)

        NATTR(self, '_dataType', EAttrType.AT_Serializable)
        self._dataType = dataType

        NATTR(self, '_value', EAttrType.AT_Serializable)
        self._value = self.check(initialValue)

        self._valueChanged = self._plugDelegate = None

        self._valueChanged = DelegateMulticast("%s_ValueChangedDelegate" % self.getName(), self)

        if not kwargs.get('noInput', False):
            self._plugDelegate = CollectorSingle("%s_ValueQueryListener" % self.getName(), self)

    def set(self, value, bMute=False):
        self._value = self.check(value)
        if not bMute:
            self._valueChanged.execute(value)

    def get(self, bUpdate=True):
        if bUpdate and self._plugDelegate and self._plugDelegate.isBound():
            self._value = self.check(self._plugDelegate.call())
        return self._value

    def hasConnection(self):
        return self._plugDelegate.isBound() if self._plugDelegate else False

    def connect(self, *args):
        # from -> to ex output.connect(input)
        res = []
        if isinstance(args[0], NDynamicAttr):
            obj = args[0]
            res.append(self.getOutDelegate().bindFunction(obj, 'set'))
            res.append(obj.getInDelegate().bindFunction(self, 'get'))
        elif len(args) == 2 and args[0] and isinstance(args[1], str):
            res.append(self.getOutDelegate().bindFunction(args[0], args[1]))

        return res

    def getOutDelegate(self):
        return self._valueChanged

    def getInDelegate(self):
        return self._plugDelegate

    def dataType(self):
        return self._dataType

    def check(self, o):
        """
        Automatically attempt to cast the value to the proper type. Ex: str to NString
        :param o: The input value.
        :return: The casted value.
        """
        if not o:
            return DATACLASSES[self._dataType]()

        if self._dataType == EDataType.DT_Variant:
            return o

        if not isinstance(o, DATACLASSES[self._dataType]):
            obj = DATACLASSES[self._dataType](o)
            return obj
        else:
            return o


class NFunctionBase(NObject):
    def __init__(self, funcName, Owner=None, FuncType=EFuncType.FT_Callable):
        super(NFunctionBase, self).__init__(name=funcName, owner=Owner)

        # Holds a list of generated attributes. Can be used if the function is modified at runtime.
        self._generatedAttributes = []

        # Can be called if the function is being dynamically modified at runtime.
        self.onClassChanged = DelegateMulticast("onClassChangedDelegate_%s" % self.getName(), self)
        self.onAttributeChanged = DelegateMulticast('onAttributeAddedDelegate_%s' % self.getName(), self)

        NATTR(self, '_thenDelegate', EAttrType.AT_Serializable, EAttrType.AT_SingleCastDelegate)
        self._thenDelegate = DelegateSingle("ThenDelegate_%s" % self.getName(), self)

        self._funcType = FuncType

        if FuncType == EFuncType.FT_Pure:
            NATTR(self, 'execute', EAttrType.AT_Blacklisted); NATTR(self, 'then', EAttrType.AT_Blacklisted)
        else:
            REGISTER_HOOK(self, 'then', self._thenDelegate)

    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate)
    def execute(self):
        # print("Node executed! Do awesome logic here...")
        self.then()

    @Property(EPropType.PT_FuncDelegateOut, dataType=EDataType.DT_Delegate)
    def then(self):
        # print("Then..call whatever needs calling.")
        self._thenDelegate.execute()

    def type_(self):
        return self._funcType




