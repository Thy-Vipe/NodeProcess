from Nodes.Core import *
from Nodes.CoreUtils import *


class Mayabatch(NFunctionBase):
    def __init__(self, funcName):
        super(Mayabatch, self).__init__(funcName, None, EFuncType.FT_Callable)

        self.mayaCmd = NBatchScript("", jobFinishedCmd=self.workDone)
        self.mayaCmdScript = ""
        self.mayaScene = ""
        self.mayaCmd.setAsync(True)
        self.maya_path_override = "C:\\Program Files\\Autodesk\\Maya2018\\bin\\mayabatch.exe" # if set, will use this instead of default maya path.

        self._workDoneDelegate = DelegateMulticast('%s_jobFinishedDelegate' % self.getName(), self)
        REGISTER_HOOK(self, "workDone", self._workDoneDelegate)

        self.registerGetters()

    def getCmdFmt(self, script: bool = True):
        if script:
            fmt = "\"{mpath}\" -file \"{fpath}\" -script {scrf}"
        else:
            fmt = "\"{mpath}\" -file \"{fpath}\""
        return fmt

    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate, pos=0)
    def execute(self):
        self.evaluate()

        cmd = self.getCmdFmt(self.mayaCmdScript != "")
        mayapath = self.maya_path_override if self.maya_path_override != "" else "mayabatch.exe"
        if self.mayaScene == "":
            raise RuntimeError("No maya scene specified, aborting.")

        r = cmd.format(mpath=mayapath, fpath=self.mayaScene, scrf=self.mayaCmdScript)
        self.mayaCmd.setCode(r)
        self.mayaCmd.exec()

        self.then()

    @Property(EPropType.PT_FuncDelegateOut, dataType=EDataType.DT_Delegate, pos=-2)
    def workDone(self):
        self._workDoneDelegate.execute()

    @Property(EPropType.PT_Input, dataType=EDataType.DT_String, pos=2)
    def inputScript(self, v: str):
        """
        Optional, run a script if wanted.
        """
        self.mayaCmdScript = v

    @Property(EPropType.PT_Input, dataType=EDataType.DT_String, pos=3)
    def inputScene(self, v: str):
        self.mayaScene = v

    @Property(EPropType.PT_Input, dataType=EDataType.DT_String, pos=4)
    def mayaPath(self, v: str):
        """
        Optional, will default to %PATH% if not plugged in.
        """
        self.maya_path_override = v

    def _get_mayaPath(self):
        return self.maya_path_override

    def _get_inputScene(self):
        return self.mayaScene

    def _get_inputScript(self):
        return self.mayaCmdScript


class MayaCmd(Mayabatch):
    def __init__(self, funcName):
        super(MayaCmd, self).__init__(funcName)


    @Property(EPropType.PT_FuncDelegateIn, dataType=EDataType.DT_Delegate, pos=0)
    def execute(self):
        cmd = self.getCmdFmt(self.mayaCmdScript != "")
        mayapath = self.maya_path_override if self.maya_path_override != "" else "maya.exe"
        if self.mayaScene == "":
            raise RuntimeError("No maya scene specified, aborting.")

        cmd.format(mpath=mayapath, fpath=self.mayaScene, scrf=self.mayaCmdScript)
        self.mayaCmd.setCode(cmd)
        self.mayaCmd.exec()
        self.then()
