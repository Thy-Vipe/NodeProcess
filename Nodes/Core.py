
import multiprocessing, sys, os
from Nodes.Decorators import *
from Delegates.InternalDelegates import *
from Nodes.CoreProperties import *
from Nodes.CoreObject import *
from Nodes.WeakReferences import *
import types



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

        NATTR(self, '_valueChanged', EAttrType.AT_Serializable, EAttrType.AT_Persistent); NATTR(self, '_sktDelegate', EAttrType.AT_Serializable, EAttrType.AT_Persistent)
        self._valueChanged = self._sktDelegate = None

        self._valueChanged = DelegateMulticast("%s_ValueChangedDelegate" % self.getName(), self)

        if not kwargs.get('noInput', False):
            self._sktDelegate = CollectorSingle("%s_ValueQueryListener" % self.getName(), self)

        self._onEvaluated = None
        ehook = kwargs.get("EvaluationHook", None)
        if ehook:
            self._onEvaluated = NWeakMethod(ehook)

    def set(self, value, bMute=False, bFromCaller=False):
        if not bFromCaller and self._onEvaluated and self._onEvaluated.isValid():
            self._onEvaluated()()

        self._value = self.check(value)
        if not bMute:
            self._valueChanged.execute(value)

    def get(self, bUpdate=True, bFromCaller=False):
        if not bFromCaller and self._onEvaluated and self._onEvaluated.isValid() and bUpdate:
            self._onEvaluated()()

        if bUpdate and self._sktDelegate and self._sktDelegate.isBound():
            self._value = self.check(self._sktDelegate.call(bUpdate=False))

        return self._value

    def evaluate(self):
        self._valueChanged.execute(self._value)

    def hasConnection(self):
        return self._sktDelegate.isBound() if self._sktDelegate else False

    def connect(self, *args):
        # from -> to ex output.connect(input)
        res = []
        if isinstance(args[0], NDynamicAttr) or isinstance(getattr(args[0], args[1]), NDynamicAttr):
            obj = args[0]
            dyn = getattr(args[0], args[1]) if not isinstance(obj, NDynamicAttr) else obj
            res.append(self.getOutDelegate().bindFunction(dyn, 'set'))
            res.append(dyn.getInDelegate().bindFunction(self, 'get'))
            dyn.set(self._value)
        elif len(args) == 2 and args[0] and isinstance(args[1], str):
            res.append(self.getOutDelegate().bindFunction(args[0], args[1]))
            func = getattr(args[0], args[1])
            func.extra_data['UpdateHook'] = NWeakRef(self)

        return res

    def getOutDelegate(self):
        return self._valueChanged

    def getInDelegate(self):
        return self._sktDelegate

    def dataType(self):
        return self._dataType

    def check(self, o):
        """
        Automatically attempt to cast the value to the proper type. Ex: str to NString
        :param o: The input value.
        :return: The casted value.
        """
        if not o and not isinstance(o, (bool, float, int)):
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
        self._thenDelegate = DelegateMulticast("ThenDelegate_%s" % self.getName(), self)

        self._funcType = FuncType

        if FuncType == EFuncType.FT_Pure:
            NATTR(self, 'execute', EAttrType.AT_Blacklisted); NATTR(self, 'then', EAttrType.AT_Blacklisted)
        else:
            REGISTER_HOOK(self, 'then', self._thenDelegate)

    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate, pos=-2)
    def execute(self):
        # print("Node executed! Do awesome logic here...")
        self.then()

    @Property(EPropType.PT_FuncDelegateOut, dataType=EDataType.DT_Delegate, pos=-1)
    def then(self):
        # print("Then..call whatever needs calling.")
        self._thenDelegate.execute()

    def type_(self):
        return self._funcType

    def classInfo(self):
        """
        Can be used to get the class name. It can be overriden if specific data is expected.
        :return a tuple with the class name, and 'None' by default. The intent is to specify a value there if the base class is a wrapper.
        """
        return self.__class__.__name__, 0

    def registerGetters(self, getter_syntax: str = '_get_{n}'):
        """
        Call this method to automatically register all getters from a class. It is not called by default.
        :param getter_syntax: The syntax to use to parse the getter name. Its default value is '_get_{n}' with n being the original setter's name.
        :type getter_syntax: str
        """
        properties = []
        for x in dir(self):
            ref = getattr(self, x)
            if callable(ref) and isinstance(ref, types.MethodType):
                properties.append(ref)

        for prop in properties:
            getter_name = getter_syntax.format(n=prop.__name__)
            for p in properties:
                if p != prop:
                    if p.__name__.lower() == getter_name.lower():
                        REGISTER_GETTER(self, prop.__name__, p)

    def getExposedProps(self):

        mapping = {}
        for attr in dir(self):
            val = getattr(self, attr)
            if callable(val):
                propInfo = getattr(val, EXPOSEDPROPNAME, None)
                propDetails = getattr(val, EXPOSED_EXTRADATA, None)
                if propInfo and propDetails:
                    p = propDetails['pos']
                    keys = mapping.keys()
                    if p in keys:
                        p = max(keys) + 1
                    mapping[p] = attr

            elif isinstance(val, NDynamicAttr):
                info = self.__PropFlags__.get(attr, (None, None, -1))
                p = info[2]
                keys = mapping.keys()
                if p in mapping.keys():
                    p = max(keys) + 1
                mapping[p] = attr

        keys = list(mapping.keys())
        keys.sort()

        return [mapping[idx] for idx in keys]

    def evaluate(self):
        for item in self.getExposedProps():
            val = getattr(self, item)
            if callable(val):
                propInfo = getattr(val, EXPOSEDPROPNAME, None)
                propDetails = getattr(val, EXPOSED_EXTRADATA, None)
                if propInfo and propDetails:
                    setter = propDetails.get('UpdateHook', None)
                    if setter and setter.isValid():
                        setter().evaluate()

    def update(self):
        """
        Update is called after a node was deserialized. It is meant to be overridden if the data that the node holds
        possibly changes the state of the node (by adding attributes, for instance),
        in which case this function should be overridden to regenerate the attributes.
        """
        pass
