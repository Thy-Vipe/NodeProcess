from PySide2 import QtCore, QtGui, QtWidgets
import sys, os

# Get the local path to add to sys.path to properly load custom modules.
if __name__ == "__main__":
    lp = __file__.rsplit("/", 2)[0]; sys.path.extend([lp, lp.replace("/", "\\")]); del lp

from Nodes.Core import NObject


class NMainWindow(NObject, QtWidgets.QMainWindow):
    def __init__(self, owningObject, windowParent=None):
        NObject.__init__(self, "MAIN_WINDOW", owningObject)
        QtWidgets.QMainWindow.__init__(self, windowParent)

        self._windowGraph = None

    def initializeGraph(self):
        pass


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = NMainWindow(None)
    win.show()
    sys.exit(app.exec_())
