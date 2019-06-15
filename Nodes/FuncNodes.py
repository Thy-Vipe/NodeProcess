from Nodes.Core import *
from Nodes.CoreUtils import *
import shutil


class Tester(NFunctionBase):
    """
    A simple <button> node to execute a script.
    """
    def __init__(self, funcName):
        super(Tester, self).__init__(funcName, None, EFuncType.FT_Callable)

        NATTR(self, 'then', EAttrType.AT_kSlot)  # Mark this method as a slot for an execute button.

        # execute not used for Tester.

    def execute(self):
        pass


class Print(NFunctionBase):
    def __init__(self, funcName):
        super(Print, self).__init__(funcName, None, EFuncType.FT_Callable)

        NATTR(self, 'inputStr', EAttrType.AT_ReadWrite, EAttrType.AT_Serializable, pos=1)
        self.inputStr = NDynamicAttr('input string', EDataType.DT_String, '', self)

    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate, pos=0)
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
        self._blocks = []

        self.registerGetters()


    def _get_script(self):
        return self._rawScript

    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate, pos=0)
    def execute(self):
        self.evaluate()
        if isinstance(self._script, NBatchScript):
            self.updateCode()  # re-evaluate the script if type is batch script, to parse the proper data.
        self._script.exec()
        self.then()

    def update(self):
        self.findInputs()

    @Property(EPropType.PT_Input, dataType=EDataType.DT_Script, pos=2)
    def script(self, inString: (str, NScript)):
        assert isinstance(inString, (str, NScript)), "input is not str or NScript. Input is %s" % inString.__class__.__name__

        if isinstance(inString, NScript):
            self._script = inString
            self._rawScript = inString.getCode()
        elif isinstance(inString, str):
            self._rawScript = inString

        self.findInputs()

    def findInputs(self):
        code = self._rawScript
        j = code.rfind('}')
        i = 0
        inputs = []
        self._blocks = []
        while i+1 < j:
            start, end, name = UCoreUtils.findBlock(code, i+1)
            if end == -1 or start == -1:
                break
            i = end
            inputs.append(name)
            bIsOutput = code[start-2] == '@' if start - 2 >= 0 else False
            print(bIsOutput)
            self._blocks.append((start, end, name, bIsOutput))

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
                RNATTR(self, attr)
                delattr(self, attr)

        idx = 0
        for at, typ in attrs:
            typ = DATATYPES_STR[typ]
            bNoIn = self._blocks[idx][3]
            NATTR(self, at, (EAttrType.AT_ReadOnly if bNoIn else EAttrType.AT_ReadWrite))
            setattr(self, at, NDynamicAttr(at, typ, None, self, noInput=bNoIn))
            self._generatedAttributes.append(at)
            self._script.addLocal({at: getattr(self, at)})
            self.onAttributeChanged.execute(at, EAttrChange.AC_Added, typ)
            idx += 1

        # finally clean up the actual script:
        cleanScript = self._cleanupStr(self._rawScript, self._blocks)

        self._script.setCode(cleanScript); print(cleanScript)

    def _cleanupStr(self, rawScript, blocks):
        cleanScript = rawScript
        for block in blocks:
            var = block[2].split(':')[0]
            cleanScript = cleanScript.replace(cleanScript[block[0] - 1:block[1] + 1], ("%s.get()" % var if not block[3] else "%s.set" % var))

        cleanScript = cleanScript.replace("@", "")

        return cleanScript

    def updateCode(self):
        self._script.setCode(self._cleanupStr(self._rawScript, self._blocks))

    @Property(EPropType.PT_Input, dataType=EDataType.DT_Bool, pos=1)
    def bAsync(self, v: bool):
        """
        Make this batch script execution asynchronous. This will be executed in the process thread.
        """
        self._script.setAsync(v)

    def _get_bAsync(self):
        return self._script.getAsync()


class BatchScript(PyScript):
    def __init__(self, funcName):
        super(BatchScript, self).__init__(funcName)

        self._script = NBatchScript('')

    def _cleanupStr(self, rawScript, blocks):
        cleanScript = self._rawScript
        for block in blocks:
            v = getattr(self, block[2].split(':')[0]).get()
            cleanScript = cleanScript.replace(cleanScript[block[0] - 1:block[1] + 1], "%s" % str(v))

        return cleanScript


class ForLoop(NFunctionBase):
    def __init__(self, funcName):
        super(ForLoop, self).__init__(funcName, None, EFuncType.FT_Callable)

        self._loopDelegate = DelegateSingle("loopDelegate_%s" % self.getName(), self)

        self.start = NDynamicAttr('start', EDataType.DT_Int, NInt(0), self)
        self.end = NDynamicAttr('end', EDataType.DT_Int, NInt(10), self)

        NATTR(self, 'index', EAttrType.AT_ReadOnly, pos=2)
        self.index = NDynamicAttr('index', EDataType.DT_Int, NInt(0), self, noInput=True)

        REGISTER_HOOK(self, 'loop', self._loopDelegate)

    @Property(EPropType.PT_FuncDelegateOut, dataType=EDataType.DT_Delegate, pos=1)
    def loop(self):
        self._loopDelegate.execute()

    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate, pos=0)
    def execute(self):
        s, e = self.start.get().get(), self.end.get().get()
        for idx in range(s, e):
            self.index.set(idx)
            self.loop()

        self.then()

    @Property(EPropType.PT_FuncDelegateOut, dataType=EDataType.DT_Delegate, pos=3)
    def then(self):
        super(ForLoop, self).then()


class ForEachLoop(NFunctionBase):
    def __init__(self, funcName):
        super(ForEachLoop, self).__init__(funcName, None, EFuncType.FT_Callable)

        self._loopDelegate = DelegateSingle("loopDelegate_%s" % self.getName(), self)
        self._counter = []

        NATTR(self, 'value', EAttrType.AT_ReadOnly, pos=3)
        self.value = NDynamicAttr('value', EDataType.DT_Variant, None, self)

        NATTR(self, 'index', EAttrType.AT_ReadOnly, pos=4)
        self.index = NDynamicAttr('index', EDataType.DT_Int, NInt(0), self, noInput=True)

        REGISTER_HOOK(self, 'loop', self._loopDelegate)

    @Property(EPropType.PT_FuncDelegateOut, dataType=EDataType.DT_Delegate, pos=2)
    def loop(self):
        self._loopDelegate.execute()

    @Property(EPropType.PT_Input, dataType=EDataType.DT_Iterable, pos=1)
    def iterable(self, it: (list, tuple, collections.UserList, ByRefVar)):
        if isinstance(it, ByRefVar):
            it = it.get()

        self._counter = map(lambda x: NVariant(x), it)

    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate, pos=0)
    def execute(self):
        self.evaluate()
        idx = 0
        for item in self._counter:
            self.value.set(item)
            self.index.set(idx)
            self.loop()
            idx += 1

        self.then()

    @Property(EPropType.PT_FuncDelegateOut, dataType=EDataType.DT_Delegate, pos=5)
    def then(self):
        super(ForEachLoop, self).then()


class Condition(NFunctionBase):
    def __init__(self, funcName):
        super(Condition, self).__init__(funcName, None, EFuncType.FT_Callable)

        NATTR(self, 'condition', EAttrType.AT_WriteOnly, pos=1)
        self.condition = NDynamicAttr('condition', EDataType.DT_Bool, False, self)

        self.trueDelegate = DelegateSingle('trueDelegate_%s' % self.getName(), self)
        self.falseDelegate = DelegateSingle('trueDelegate_%s' % self.getName(), self)

        REGISTER_HOOK(self, 'true', self.trueDelegate)
        REGISTER_HOOK(self, 'false', self.falseDelegate)

    def then(self):
        pass

    @Property(EPropType.PT_FuncDelegateOut, dataType=EDataType.DT_Delegate, pos=2)
    def true(self):
        self.trueDelegate.execute()

    @Property(EPropType.PT_FuncDelegateOut, dataType=EDataType.DT_Delegate, pos=3)
    def false(self):
        self.falseDelegate.execute()

    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate, pos=0)
    def execute(self):
        if self.condition.get():
            self.true()
        else:
            self.false()


class Reroute(NFunctionBase):
    def __init__(self, funcName):
        super(Reroute, self).__init__(funcName, None, EFuncType.FT_Pure)

        # @TODO finish reroute node


class ReadDir(NFunctionBase):
    def __init__(self, funcName):
        super(ReadDir, self).__init__(funcName, None, EFuncType.FT_Callable)

        self._bRecursive = False

        NATTR(self, 'result', EAttrType.AT_ReadOnly, DESC="The output, an iterable of strings representing full path to a file.", pos=3)
        self.result = NDynamicAttr('result', EDataType.DT_Iterable, [], self, noInput=True)

        NATTR(self, 'directory', EAttrType.AT_ReadWrite, DESC="The read directory, a full path.", pos=1)
        self.directory = NDynamicAttr('directory', EDataType.DT_String, '', self)

        self.registerGetters()

    @Property(EPropType.PT_Input, dataType=EDataType.DT_Bool, pos=2)
    def isRecursive(self, v: bool):
        """
        When true, find all sub-folders' files from the provided directory. It can be a slow operation.
        """
        self._bRecursive = bool(v)

    def _get_isRecursive(self):
        return self._bRecursive

    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate, pos=0)
    def execute(self):
        self.result.set(self.goThroughDir(self.directory.get()))
        self.then()

    def goThroughDir(self, path):
        p = os.listdir(str(path))
        files = []
        for item in p:
            fp = "%s\\%s" % (path, item)  # Parse the full path for the current item.
            # Check if the item we're going through is a directory or a file.
            if os.path.isfile(fp):
                files.append(NString(fp))

            elif self._bRecursive and os.path.isdir(fp):
                files.extend(self.goThroughDir(fp))

        return files


class RenameFile(NFunctionBase):
    def __init__(self, funcName):
        super(RenameFile, self).__init__(funcName, None, EFuncType.FT_Callable)

        NATTR(self, 'file', EAttrType.AT_ReadWrite, DESC="The file to rename.")
        self.file = NDynamicAttr('file', EDataType.DT_String, '')

        NATTR(self, 'outFile', EAttrType.AT_ReadOnly, DESC="The new name for this file.")
        self.outFile = NDynamicAttr('outFile', EDataType.DT_String, '', noInput=True)

        self._replaceStatement = ''

        self.registerGetters()

    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate, pos=0)
    def execute(self):
        fp = str(self.file.get())
        path = fp.rsplit('\\', 1)[0]
        new = "%s\\%s" % (path, self._replaceStatement)
        os.rename(fp, new)
        self.outFile.set(new)
        self.then()

    @Property(EPropType.PT_Input, dataType=EDataType.DT_String)
    def newName(self, v: str):
        self._replaceStatement = str(v)

    def _get_newName(self):
        return self._replaceStatement


class Sequence(NFunctionBase):
    def __init__(self, funcName):
        super(Sequence, self).__init__(funcName, EFuncType.FT_Callable)

        self._idx = 2
        self.then_1 = self.then

        NATTR(self, 'addEntry', EAttrType.AT_kSlot)
        NATTR(self, 'removeEntry', EAttrType.AT_kSlot)

    @Property(EPropType.PT_Internal)
    def addEntry(self):
        attr = 'then_%d' % self._idx
        setattr(self, attr, self.then)
        self.onAttributeChanged.execute(attr, EAttrChange.AC_Added, typ=EDataType.DT_Delegate, mode=2)
        self._idx += 1

    @Property(EPropType.PT_Internal)
    def removeEntry(self):
        if self._idx == 2: return

        attr = 'then_%d' % (self._idx - 1)
        delattr(self, attr)
        self.onAttributeChanged.execute(attr, EAttrChange.AC_Removed)
        self._idx -= 1


class MoveToDir(NFunctionBase):
    def __init__(self, funcName):
        super(MoveToDir, self).__init__(funcName, EFuncType.FT_Callable)

        NATTR(self, 'src', EAttrType.AT_Serializable, EAttrType.AT_ReadWrite,
              DESC="The source path, can be either\n a directory or a file", pos=1)
        self.src = NDynamicAttr('src', EDataType.DT_String, '', self)

        NATTR(self, 'dst', EAttrType.AT_Serializable, EAttrType.AT_ReadWrite,
              DESC="The destination path. It must be a directory.", pos=2)
        self.dst = NDynamicAttr('dst', EDataType.DT_String, '', self)

        self._createDir = True

        self.registerGetters()

    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate, pos=0)
    def execute(self):
        srcPath = self.src.get().toString().replace('/', '\\')
        dstPath = self.dst.get().toString().replace('/', '\\')
        if not os.path.exists(dstPath) and self._createDir:
            os.mkdir(dstPath)
        elif not os.path.exists(dstPath):
            raise FileNotFoundError("Destination directory does not exist. If you want to automatically create non-existing directories, set bCreateDirectory to true.")

        if os.path.isdir(srcPath):
            if not os.path.isdir(dstPath):
                raise FileNotFoundError("Source is a directory but destination isn't! Aborting.")

            shutil.move(srcPath, dstPath)
        else:
            p, f = srcPath.rsplit('\\', 1)
            destfp = "%s\\%s" % (dstPath, f)
            shutil.move(srcPath, destfp)

        self.then()


    @Property(EPropType.PT_Input, dataType=EDataType.DT_Bool)
    def bCreateDirectory(self, v: bool):
        self._createDir = bool(v)

    def _get_bCreateDirectory(self):
        return self._createDir


class NFunctionWrapper(NFunctionBase):
    NO_DISPLAY = True  # This class is NOT visible by the UI

    def __init__(self, funcName, baseMethod):
        assert IsDynamicMethod(baseMethod), "%s must be marked as dynamic using @ExposedMethod() decorator." % baseMethod.__name__

        super(NFunctionWrapper, self).__init__(funcName, None, baseMethod.__mode__)

        self._methodRef = baseMethod
        self.inputs = []
        self.outputs = []

        self.buildNodeFromFunc()

    def buildNodeFromFunc(self):
        sig = inspect.signature(self._methodRef)
        print(sig.return_annotation)
        null = inspect.Parameter.empty
        for k, v in sig.parameters.items():
            name = k
            typ = v.annotation
            default = v.default
            valueType = CLASSTYPES[typ] if typ is not null else EDataType.DT_Variant
            defaultValue = default if default is not null else None
            hook = self.execute if self._methodRef.__mode__ == EFuncType.FT_Pure else None
            newAttr = NDynamicAttr(name, valueType, defaultValue, self, EvaluationHook=hook)

            NATTR(self, name, EAttrType.AT_WriteOnly, EAttrType.AT_Serializable)
            setattr(self, name, newAttr)
            self.inputs.append(newAttr)

        for k, v in self._methodRef.__returnValues__.items():
            valueType = CLASSTYPES[v]
            ohook = self.execute if self._methodRef.__mode__ == EFuncType.FT_Pure else None
            newoAttr = NDynamicAttr(k, valueType, None, self, EvaluationHook=ohook)

            NATTR(self, k, EAttrType.AT_ReadOnly)
            setattr(self, k, newoAttr)
            self.outputs.append(newoAttr)

    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate)
    def execute(self):
        vals = map(lambda x: x.get(bFromCaller=True), self.inputs)
        res = self._methodRef(*vals)

        j = self.outputs.__len__()
        if j == 1:
            self.outputs[0].set(res, bFromCaller=True)
        elif j > 1:
            for idx in range(j):
                self.outputs[idx].set(res[idx], bFromCaller=True)

        self.then()

    def getFunc(self):
        return self._methodRef

    def classInfo(self):
        return self.__class__.__name__, self._methodRef.__name__


class FormatString(NFunctionBase):
    def __init__(self, funcName):
        super(FormatString, self).__init__(funcName, None, EFuncType.FT_Pure)

        self.fmtArgs = {}
        self._string = ''

        NATTR(self, 'source', EAttrType.AT_WriteOnly, EAttrType.AT_Serializable, UPDATEHOOK=self.applyAttrs)
        self.source = NDynamicAttr('source', EDataType.DT_String, '', self)

        NATTR(self, 'result', EAttrType.AT_ReadOnly)
        self.result = NDynamicAttr('result', EDataType.DT_String, '', self, noInput=True, EvaluationHook=self.applyFmt)

    def applyFmt(self):
        fmtArgs = {}
        for k, v in self.fmtArgs.items():
            fmtArgs[k] = v.get()

        self.result.set(self._string.format(**fmtArgs), bFromCaller=True)

    def applyAttrs(self):
        newStr = self.source.get(bFromCaller=True).toString()
        print(newStr, self._string)
        if newStr == self._string:
            return

        self.clearAttrs()
        args = UCoreUtils.findFmtArgs(newStr)
        for arg in args:
            newInput = NDynamicAttr(arg, EDataType.DT_Variant, None, self)
            self.fmtArgs[arg] = newInput

            NATTR(self, arg, EAttrType.AT_WriteOnly)
            setattr(self, arg, newInput)
            self.onAttributeChanged.execute(arg, EAttrChange.AC_Added, EDataType.DT_Variant)

        self._string = newStr

    def clearAttrs(self):
        for k, v in self.fmtArgs.items():
            RNATTR(self, k)
            delattr(self, k)
            self.onAttributeChanged.execute(k, EAttrChange.AC_Removed)

        self.fmtArgs.clear()


class EIterableDataType(TEnum):
    String = EDataType.DT_String
    Int = EDataType.DT_Int
    Float = EDataType.DT_Float
    Bool = EDataType.DT_Bool


class Iterable(NFunctionBase):
    def __init__(self, funcName):
        super(Iterable, self).__init__(funcName, None, EFuncType.FT_Pure)

        self.iterable = []

        NATTR(self, 'iterableRef', EAttrType.AT_ReadOnly)
        self.iterableRef = NDynamicAttr('iterableRef', EDataType.DT_AttrRef, ByRefVar(self, 'iterable'), self, noInput=True)


class MakeIterable(Iterable):
    def __init__(self, funcName):
        super(MakeIterable, self).__init__(funcName)

        self.dataMode = EIterableDataType(EIterableDataType.Int)

        self._content = []
        self._idx = 0

        self.iterableRef = NDynamicAttr('iterableRef', EDataType.DT_AttrRef, ByRefVar(self, 'iterable'), self, noInput=True, EvaluationHook=self.refresh)

        NATTR(self, 'addItem', EAttrType.AT_kSlot); NATTR(self, 'removeItem', EAttrType.AT_kSlot)
        self.registerGetters()

    @Property(EPropType.PT_Input, dataType=EDataType.DT_Enum, pos=2)
    def Type(self, v):
        self.dataMode = v

    def _get_Type(self):
        return self.dataMode

    @Property(EPropType.PT_Internal)
    def addItem(self):
        name = "Item_%d" % self._idx
        t = self.dataMode.value()
        new = NDynamicAttr(name, t, None, self)
        NATTR(self, name, EAttrType.AT_Serializable, EAttrType.AT_WriteOnly)
        setattr(self, name, new)
        self._content.append((name, t))
        self.onAttributeChanged.execute(name, EAttrChange.AC_Added, typ=t, mode=1)
        self.iterable.insert(self._idx, new.get())
        self._idx += 1

    @Property(EPropType.PT_Internal)
    def removeItem(self):
        if self._idx > 0:
            self._idx -= 1
            name = self._content[self._idx][0]
            RNATTR(self, name)
            delattr(self, name)
            self._content.pop(self._idx)
            self.onAttributeChanged.execute(name, EAttrChange.AC_Removed)

    def refresh(self):
        """
        Updates all first entries of the iterable when it is called.
        """
        values = [getattr(self, x[0]).get() for x in self._content]
        for i in range(values.__len__()):
            self.iterable[i] = values[i]


@ExposedMethod(EFuncType.FT_Pure, result=str)
def toString(val):
    return str(val)


@ExposedMethod(EFuncType.FT_Pure, isContained=bool)
def stringContains(src: str, value: str, caseSensitive: bool = False):

    if caseSensitive:
        return src.__contains__(value)
    else:
        return src.lower().__contains__(value.lower())


@ExposedMethod(EFuncType.FT_Callable, isContained=bool)
def stringContainsAny(src: str, items: ByRefVar, caseSensitive: bool = False):

    for item in items.get():
        v = stringContains(src, str(item), caseSensitive)
        if v is True:
            return True

    return False


@ExposedMethod(EFuncType.FT_Callable, isContained=bool)
def stringContainsAll(src: str, items: ByRefVar, caseSensitive: bool = False):

    for item in items.get():
        v = stringContains(src, str(item), caseSensitive)
        if v is False:
            return False

    return True


@ExposedMethod(EFuncType.FT_Pure, result=NVariant)
def add(a, b):
    return a + b


@ExposedMethod(EFuncType.FT_Pure, result=NVariant)
def minus(a, b):
    return a - b


@ExposedMethod(EFuncType.FT_Pure, result=NVariant)
def multiply(a, b):
    return a * b


@ExposedMethod(EFuncType.FT_Pure, v=bool)
def operator_or(a: bool, b: bool):
    return a or b


@ExposedMethod(EFuncType.FT_Pure, v=bool)
def operator_and(a: bool, b: bool):
    return a and b


@ExposedMethod(EFuncType.FT_Pure, result=int)
def literalInt(value: int):
    return value


@ExposedMethod(EFuncType.FT_Pure, result=float)
def literalFloat(value: float):
    return value


@ExposedMethod(EFuncType.FT_Pure, result=str)
def literalStr(value: str):
    return value


@ExposedMethod(EFuncType.FT_Callable)
def iterable_Add(iterable: ByRefVar, value):
    iterable.get().append(value)


@ExposedMethod(EFuncType.FT_Callable, removed=NVariant)
def iterable_RemoveAt(iterable: ByRefVar, idx: int):
    return iterable.get().pop(idx)


@ExposedMethod(EFuncType.FT_Callable)
def iterable_Extend(iterable: ByRefVar, other: list):
    iterable.get().extend(other)


@ExposedMethod(EFuncType.FT_Callable)
def iterable_Clear(iterable: ByRefVar):
    iterable.get().clear()


@ExposedMethod(EFuncType.FT_Pure, result=NVariant)
def iterable_Get(iterable: ByRefVar, idx: int):
    return iterable.get()[idx]


@ExposedMethod(EFuncType.FT_Callable, result=str)
def convert_Py_to_Mel(scriptPath: str, outFile: str):
    converterPath = UCoreUtils.parsePath(UCoreUtils.getMainConfig()["UTILS"]["P2MPath"])
    outFile = outFile.replace('.py', '.mel')
    subprocess.call("\"%s\" -i %s -o %s" % (converterPath, scriptPath, outFile))

    return outFile


