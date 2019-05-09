from Nodes.Core import *
from Nodes.CoreUtils import *


class Mayabatch(NFunctionBase):
    def __init__(self, funcName):
        super(Mayabatch, self).__init__(funcName, None, EFuncType.FT_Callable)

