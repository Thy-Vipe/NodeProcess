from PySide2 import QtCore, QtGui, QtWidgets
import sys, os

# Get the local path to add to sys.path to properly load custom modules.
if __name__ == "__main__":
    lp = __file__.rsplit("/", 2)[0]; sys.path.extend([lp, lp.replace("/", "\\")]); del lp

from Nodes.Core import NObject
from Windows.NWindowsUtils import NAnchor


class NWidget(NObject, QtWidgets.QWidget):
    """
    Base class for widgets. Designed to be used as a friend class of any QWidget subclass.
    """
    # Shared signal. Fired when the widget's geometry changes.
    OnGeometryChange = QtCore.SIGNAL(QtCore.QRect)

    def __init__(self, parent, name=""):
        NObject.__init__(self, "", parent)
        QtWidgets.QWidget.__init__(self, parent)

        self.__anchor = None


    def setGeometry(self, geo):
        super(NWidget, self).setGeometry(geo)
        self.OnGeometryChange.emit(geo)

    def getAnchor(self):
        """
        Get the anchor of this Widget. None if non-existing.
        :return: The anchor object reference.
        """

    def addAnchor(self, inPosA, inPosB):
        self.__anchor = NAnchor(self.getParent(), self, inPosA, inPosB)
        self.__anchor.update()



