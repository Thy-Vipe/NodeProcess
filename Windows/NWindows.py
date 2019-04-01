from PySide2 import QtCore, QtGui, QtWidgets
import sys, os

# Get the local path to add to sys.path to properly load custom modules.
if __name__ == "__main__":
    lp = __file__.rsplit("/", 2)[0]; sys.path.extend([lp, lp.replace("/", "\\")]); del lp

from Windows import CoreNWindows


class NMainWindow(CoreNWindows.NWidget, QtWidgets.QMainWindow):
    def __init__(self, owningObject, windowParent=None):
        CoreNWindows.NWidget.__init__(self, owningObject, "MAIN_WINDOW")
        QtWidgets.QMainWindow.__init__(self, windowParent)

        self._windowGraph = None

    def initializeGraph(self):
        pass


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = NMainWindow(None)
    win.show()
    sys.exit(app.exec_())
