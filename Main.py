import sys, os
from PySide2 import QtWidgets


# Get the local path to add to sys.path to properly load custom modules.
if __name__ == "__main__":
    lp = __file__.rsplit("/", 1)[0]; sys.path.extend([lp, lp.replace("/", "\\")]); del lp

# Dependencies for Visual Scripting
from Nodes import FuncNodes
from MayaLib import MayaNodes
from NukeLib import NukeNodes
from RenderingLib import UtilsNodes

from Windows import NWindows as Win
from Nodes import Core, CoreUtils
from NThreads import NThreading
import global_accessor as g_a
import threading, types



"""
# =============================================================================================
                Define all modules to be used in the nodal system here.
# =============================================================================================
"""
DEPENDENCY_LIST = [FuncNodes, MayaNodes, NukeNodes, UtilsNodes]









class APPLICATION(Core.NWorld):
    def __init__(self):
        super(APPLICATION, self).__init__(name='APPLICATION')

        APPLICATION.registerFunctions()

    @staticmethod
    def registerFunctions():
        all_ = {}
        for lib in DEPENDENCY_LIST:
            all_.update(lib.__dict__)

        for k, cls in all_.items():
            if CoreUtils.UCoreUtils.checkBases(cls, Core.NFunctionBase):
                if not getattr(cls, 'NO_DISPLAY', False):
                    g_a.registerFunction(cls)

            elif callable(cls) and isinstance(cls, types.FunctionType):
                if getattr(cls, '__VisibleFunc__', False):
                    g_a.registerFunction(cls)


    @property
    def path(self):
        return os.path.realpath(os.path.dirname(LOCAL_DIR))


    def spawnInterface(self):
        self._WindowReference = Win.NMainWindow(self)
        self._setGraph(self._WindowReference.graphicsView)
        self._WindowReference.show()
        print("Spawning interface, thread ID: %s" % threading.get_ident())


if __name__ == "__main__":
    MAIN_THREAD = NThreading.NThread('MAIN_THREAD')
    EXEC_THREAD = NThreading.NThread('EXEC_THREAD')
    g = globals()
    g['Main_thread'] = MAIN_THREAD
    g['Exec_thread'] = EXEC_THREAD
    g['LOCAL_DIR'] = __file__
    script = NThreading.NScript("app = QtWidgets.QApplication(sys.argv);app_obj = APPLICATION();app_obj.spawnInterface();sys.exit(app.exec_())", g, locals())
    MAIN_THREAD.asyncTask(script)
    MAIN_THREAD.start()

