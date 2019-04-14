
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

        if not isinstance(o, DATACLASSES[self._dataType]):
            return DATACLASSES[self._dataType](o)
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


class Tester(NFunctionBase):
    """
    A simple <button> node to execute a script.
    """
    def __init__(self, funcName):
        super(Tester, self).__init__(funcName, None, EFuncType.FT_Callable)

        NATTR(self, 'then', EAttrType.AT_kSlot)  # Mark this method as a slot for an execute button.

        # execute not used for Tester.
        delattr(NFunctionBase, 'execute')


class Print(NFunctionBase):
    def __init__(self, funcName):
        super(Print, self).__init__(funcName, None, EFuncType.FT_Callable)

        NATTR(self, 'inputStr', EAttrType.AT_ReadWrite, EAttrType.AT_Serializable)
        self.inputStr = NDynamicAttr('input string', EDataType.DT_String, '', self)

    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate)
    def execute(self):
        print(self.inputStr.get())
        self.then()


class PyScript(NFunctionBase):
    def __init__(self, funcName):
        super(PyScript, self).__init__(funcName, None, EFuncType.FT_Callable)

        NATTR(self, '_script', EAttrType.AT_Serializable)

        glob = {'world': GA,
                'Core': globals()}
        loc = {'this': self}
        self._script = NScript('', glob, loc)
        self._rawScript = ''

        REGISTER_GETTER(self, 'script', self.getRawStr)


    def getRawStr(self):
        return self._rawScript

    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate)
    def execute(self):
        self._script.exec()
        self.then()

    @Property(EPropType.PT_Input, dataType=EDataType.DT_Script)
    def script(self, string):
        assert isinstance(string, (str, NScript)), "input is not str or NScript. Input is %s" % string.__class__.__name__

        if isinstance(string, NScript):
            self._script = string
            self._rawScript = string.getCode()
        elif isinstance(string, str):
            self._rawScript = string

        self.findInputs()

    def findInputs(self):
        code = self._rawScript
        j = code.rfind('}')
        i = 0
        inputs = []
        allblocks = []
        while i+1 < j:
            start, end, name = UCoreUtils.findBlock(code, i+1)
            if end == -1 or start == -1:
                break
            i = end
            inputs.append(name)
            allblocks.append((start, end, name))

        attrs = map(lambda x: x.split(':'), inputs)
        attrmap = map(lambda x: x[0], attrs)

        idx = self._generatedAttributes.__len__() - 1
        while idx >= 0:
            idx -= 1
            attr = self._generatedAttributes[idx]
            if attr not in attrmap:
                inst = getattr(self, attr)
                self._generatedAttributes.pop(idx)
                self._script.removeLocal([attr])
                self.onAttributeChanged.execute(attr, EAttrChange.AC_Removed, inst.dataType())
                delattr(self, attr)

        for at, typ in attrs:
            typ = DATATYPES_STR[typ]
            setattr(self, at, NDynamicAttr(at, typ, None, self))
            self._generatedAttributes.append(at)
            self._script.addLocal({at: getattr(self, at)})
            self.onAttributeChanged.execute(at, EAttrChange.AC_Added, typ)

        # finally clean up the actual script:
        cleanScript = self._rawScript
        for block in allblocks:
            cleanScript = cleanScript.replace(cleanScript[block[0]-1:block[1]+1], "%s.get()" % block[2].split(':')[0])

        self._script.setCode(cleanScript); print(cleanScript)


class ForLoop(NFunctionBase):
    def __init__(self, funcName):
        super(ForLoop, self).__init__(funcName, None, EFuncType.FT_Callable)

        self._loopDelegate = DelegateSingle("loopDelegate_%s" % self.getName(), self)

        self.start = NDynamicAttr('start', EDataType.DT_Int, NInt(0), self)
        self.end = NDynamicAttr('end', EDataType.DT_Int, NInt(10), self)

        NATTR(self, 'index', EAttrType.AT_ReadOnly)
        self.index = NDynamicAttr('index', EDataType.DT_Int, NInt(0), self, noInput=True)

        REGISTER_HOOK(self, 'loop', self._loopDelegate)

    @Property(EPropType.PT_FuncDelegateOut, dataType=EDataType.DT_Delegate)
    def loop(self):
        self._loopDelegate.execute()

    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate)
    def execute(self):
        s, e = self.start.get().get(), self.end.get().get()
        for idx in range(s, e):
            self.index.set(idx)
            self.loop()

        self.then()


class ForEachLoop(NFunctionBase):
    def __init__(self, funcName):
        super(ForEachLoop, self).__init__(funcName, None, EFuncType.FT_Callable)

        self._loopDelegate = DelegateSingle("loopDelegate_%s" % self.getName(), self)
        self._counter = []

        NATTR(self, 'value', EAttrType.AT_ReadOnly)
        self.value = NDynamicAttr('value', EDataType.DT_Variant, None, self)

        REGISTER_HOOK(self, 'loop', self._loopDelegate)

    @Property(EPropType.PT_FuncDelegateOut, dataType=EDataType.DT_Delegate)
    def loop(self, v):
        self._loopDelegate.execute()

    @Property(EPropType.PT_Input, dataType=EDataType.DT_Variant)
    def iterable(self, it: (list, tuple)):
        self._counter = map(lambda x: NVariant(x), it)

    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate)
    def execute(self):
        for item in self._counter:
            self.value.set(item)
            self.loop()


class Reroute(NFunctionBase):
    def __init__(self, funcName):
        super(Reroute, self).__init__(funcName, None, EFuncType.FT_Pure)

        # @TODO finish reroute node


class ToString(NFunctionBase):
    def __init__(self, funcName):
        super(ToString, self).__init__(funcName, None, EFuncType.FT_Pure)

        self._convert = DelegateMulticast('convertDelegate_%s' % self.getName(), self)
        self._val = ''
        REGISTER_HOOK(self, 'result', self._convert)

    @Property(EPropType.PT_Input, dataType=EDataType.DT_Variant)
    def input(self, v):
        self._val = str(v)

    @Property(EPropType.PT_Output, dataType=EDataType.DT_String)
    def result(self):
        self._convert.execute(self._val)
