from PySide2 import QtCore, QtGui, QtWidgets
import sys, os

# Get the local path to add to sys.path to properly load custom modules.
if __name__ == "__main__":
    lp = __file__.rsplit("/", 2)[0]; sys.path.extend([lp, lp.replace("/", "\\")]); del lp

from Windows import CoreNWindows, Main_Interface


class NMainWindow(Main_Interface.MainWindowBuild, CoreNWindows.NWidget, QtWidgets.QMainWindow):
    def __init__(self, owningObject, windowParent=None):
        Main_Interface.MainWindowBuild.__init__(self)
        CoreNWindows.NWidget.__init__(self, owningObject)
        QtWidgets.QMainWindow.__init__(self, windowParent)
        self.setupUi(self)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = NMainWindow(None)
    win.show()
    sys.exit(app.exec_())
