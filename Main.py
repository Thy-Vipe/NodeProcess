import sys, os
from PySide2 import QtWidgets
from Windows import NWindows as Win
from Nodes import FuncNodes as funcs
from Nodes import Core, CoreUtils
from NThreads import NThreading
import global_accessor as g_a
import threading

# Get the local path to add to sys.path to properly load custom modules.
if __name__ == "__main__":
    lp = __file__.rsplit("/", 1)[0]; sys.path.extend([lp, lp.replace("/", "\\")]); del lp


class APPLICATION(Core.NWorld):
    def __init__(self):
        super(APPLICATION, self).__init__()

        APPLICATION.registerFunctions()

    @staticmethod
    def registerFunctions():
        for k, cls in funcs.__dict__.items():
            if CoreUtils.UCoreUtils.checkBases(cls, Core.NFunctionBase):
                g_a.registerFunction(cls)

    @property
    def path(self):
        return os.path.realpath(os.path.dirname(__file__))


    def spawnInterface(self):
        self._WindowReference = Win.NMainWindow(self)
        self._setGraph(self._WindowReference.graphicsView)
        self._WindowReference.show()
        print("Spawning interface, thread ID: %s" % threading.get_ident())


if __name__ == "__main__":
    MAIN_THREAD = NThreading.NThread('MAIN_THREAD')
    g = globals()
    g['Main_thread'] = MAIN_THREAD
    script = NThreading.NScript("app = QtWidgets.QApplication(sys.argv);app_obj = APPLICATION();app_obj.spawnInterface();sys.exit(app.exec_())", g, locals())
    MAIN_THREAD.asyncTask(script)
    MAIN_THREAD.start()

