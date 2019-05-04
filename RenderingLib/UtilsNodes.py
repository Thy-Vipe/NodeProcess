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

        self.registerGetters()
        self.Usage(self._activeUsage)


    def execute(self):
        pass

    def clear(self):
        for attr in self._dynamicAttrs:
            self.onAttributeChanged.execute(attr, EAttrChange.AC_Removed)
            RNATTR(self, attr)
            delattr(self, attr)

    @Property(EPropType.PT_Input, dataType=EDataType.DT_Enum, pos=1)
    def Usage(self, val):
        mode = val.value()
        self.clear()
        with open('%s\\RenderingNodes.NConfig' % self._path, 'r') as f:
            data = json.load(f)

            cfg = data[self.__class__.__name__][mode]
            idx = 2
            for k, v in cfg.items():
                print(k)
                at = CLASSTYPES[v.__class__]
                new = NDynamicAttr(k, at, v, self)

                NATTR(self, k, EAttrType.AT_WriteOnly, EAttrType.AT_Serializable, pos=idx)
                setattr(self, k, new)
                self._dynamicAttrs.append(k)
                self.onAttributeChanged.execute(k, EAttrChange.AC_Added, new.dataType())
                idx += 1

        self._activeUsage = ESMMode(mode)

    def _get_Usage(self):
        return self._activeUsage
