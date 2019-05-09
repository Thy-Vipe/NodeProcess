from Nodes.Core import *
from Nodes.CoreUtils import *
import json


class ESMMode(TEnum):
    TXMAKE = 'TXMAKE'
    SHO = 'sho'
    OSLC = 'oslc'
    OptiX = 'optiX'
    Hyperion = 'hyperion'


class Seemlessman(NFunctionBase):
    def __init__(self, funcName):
        super(Seemlessman, self).__init__(funcName, None, EFuncType.FT_Callable)

        """
        -help
        -txmake
        -sho
        -oslc
        -optix
        -hyperion
        """
        self._path = os.path.dirname(os.path.realpath(__file__))
        self._dynamicAttrs = []
        self._activeUsage = ESMMode(ESMMode.TXMAKE)
        self._config = {}
        self._flagCmd = ''
        self._SeemlessmanBinary = UCoreUtils.parsePath(UCoreUtils.getMainConfig()["APPLICATION"]["SeemlessmanDir"])
        self._cmdFmt = "\"{sm}\" {flag} {cmd}"

        self._jobFinishedDelegate = DelegateMulticast('%s_jobFinishedDelegate' % self.getName(), self)
        REGISTER_HOOK(self, 'jobFinished', self._jobFinishedDelegate)

        self._batchScript = NBatchScript('', jobFinishedCmd=self.jobFinished)
        self._batchScript.setAsync(True)  # Seemlessman always runs asynchronously

        self.registerGetters()
        self.Usage(self._activeUsage)

    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate, pos=0)
    def execute(self):
        self.evaluate()
        outCmdArgs = ''
        for item in self._dynamicAttrs:
            dynamicAttr = getattr(self, item)
            value = dynamicAttr.get()
            if isinstance(value, str):
                if value == "AUTODETECT" and item.lower() == 'padding':
                    p = getattr(self, 'filePath')
                    value = UCoreUtils.findIncremental(p)

            if item.lower() == 'lastframe' and value == -1:
                adir, f = getattr(self, 'filePath').rsplit('\\', 1)
                pattern = UCoreUtils.makePattern(f)
                cnt = 0
                for x in os.listdir(adir):
                    if UCoreUtils.makePattern(x) == pattern:
                        cnt += 1

                value = cnt

            print(value)
            outCmdArgs += " %s" % str(value)

        cmd = self._cmdFmt.format(sm=self._SeemlessmanBinary, flag=self._flagCmd, cmd=outCmdArgs)
        self._batchScript.setCode(cmd)
        self._batchScript.exec()
        self.then()

    @Property(EPropType.PT_FuncDelegateOut, dataType=EDataType.DT_Delegate, pos=1)
    def jobFinished(self):
        self._jobFinishedDelegate.execute()

    def clear(self):
        for attr in self._dynamicAttrs:
            self.onAttributeChanged.execute(attr, EAttrChange.AC_Removed)
            RNATTR(self, attr)
            delattr(self, attr)

        self._dynamicAttrs.clear()
        self._flagCmd = ''

    @Property(EPropType.PT_Input, dataType=EDataType.DT_Enum, pos=2)
    def Usage(self, val: ESMMode):
        mode = val.value()
        self.clear()
        with open('%s\\RenderingNodes.config' % self._path, 'r') as f:
            data = json.load(f)

            self._config = data[self.__class__.__name__][mode]
            idx = 3
            for k, v in self._config.items():
                if k != "flag":
                    at = CLASSTYPES[v.__class__]
                    new = NDynamicAttr(k, at, v, self)

                    NATTR(self, k, EAttrType.AT_WriteOnly, EAttrType.AT_Serializable, pos=idx)
                    setattr(self, k, new)
                    self._dynamicAttrs.append(k)
                    self.onAttributeChanged.execute(k, EAttrChange.AC_Added, new.dataType(), mode=1)
                    idx += 1
                else:
                    self._flagCmd = v

        assert self._flagCmd != '', "Fatal Error: No 'flag' key provided in the configuration for %s" % mode

        self._activeUsage = val

    def _get_Usage(self):
        return self._activeUsage
