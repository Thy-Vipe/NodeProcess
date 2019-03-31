from PySide2 import QtCore
from Nodes.Core import NObject
from Windows.CoreNWindows import NWidget
from Nodes.CoreProperties import NPoint2D, NVector


class NQWrap:
    """
    Simple namespace for certain utilities from QtCore.
    """
    Rec = QtCore.QRect
    Pt = QtCore.QPoint
    PtF = QtCore.QPointF
    RecF = QtCore.QRectF
    Size = QtCore.QSize
    SizeF = QtCore.QSizeF


class NAnchor(NObject):
    """
    Anchor that dynamically resize a widget according to its owning widget.
    """
    def __init__(self, InOwningObj, InObj, PtA=NQWrap.PtF(0.0, 0.0), PtB=NQWrap.PtF(1.0, 1.0)):
        """
        Initialize the anchor object.
        :param InOwningObj: The widget owning the child to control. Must inherit from NWidget.
        :param InObj: The child to control. Must inherit from NWidget.
        :param PtA: The parametric QPointF() representing the x and y start position of the child inside the parent.
        :param PtB: The parametric QPointF() representing the x and y end position of the child inside the parent.
        """
        super(NAnchor, self).__init__("kAnchor", InObj)

        self._posOrig = PtA
        self._posExtent = PtB - PtA

        if not (isinstance(InOwningObj, NWidget) and isinstance(InObj, NWidget)):
            raise RuntimeError("Cannot bind NAnchor to non NWidgets!")

        self._OwningObj = InOwningObj
        self._CtrObj = InObj
        InOwningObj.OnGeometryChange.connect(self.__updateWrappedObjectGeo)

    def __updateWrappedObjectGeo(self, InGeo):
        """
        Update the child widget geometry according to the anchor's parameters.
        :param InGeo: The new geometry to update from. This assumes that this geo is the parent's geo.
        """
        origPx = NPoint2D(InGeo.x(), InGeo.y()) * NPoint2D.fromQPoint(self._posOrig)
        endPx = NPoint2D(InGeo.width(), InGeo.height()) * NPoint2D.fromQPoint(self._posExtent)
        self._CtrObj.setGeometry(NQWrap.Rec(origPx.toQPoint(), NQWrap.Size(*endPx.toList())))

    def update(self):
        self.__updateWrappedObjectGeo(self._OwningObj.getGeometry())

    def setAnchors(self, inStart, inEnd, bEndIsExtent=False):
        self._posOrig = inStart
        self._posExtent = inEnd - inStart if not bEndIsExtent else inEnd

    def getRectangle(self):
        return self._CtrObj.getGeometry()
