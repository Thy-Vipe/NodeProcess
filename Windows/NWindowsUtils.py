from PySide2 import QtCore
from Nodes.Core import NObject
from Windows.CoreNWindows import NWidget
from Nodes.CoreProperties import NPoint2D, NVector


class NQWrap:
    """
    Simple enum for certain utilities from QtCore.
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
        super(NAnchor, self).__init__("kAnchor", InObj)

        self._posOrig = PtA
        self._posExtent = PtB - PtA

        if not (isinstance(InOwningObj, NWidget) and isinstance(InObj, NWidget)):
            raise RuntimeError("Cannot bind NAnchor to non NWidgets!")

        self._OwningObj = InOwningObj
        self._CtrObj = InObj
        InOwningObj.OnGeometryChange.connect(self.__updateWrappedObjectGeo)

    def __updateWrappedObjectGeo(self, InGeo):
        parentGeo = self._OwningObj.getGeometry()
        origPx = NPoint2D(parentGeo.x(), parentGeo.y()) * NPoint2D.fromQPoint(self._posOrig)
        endPx = NPoint2D(parentGeo.width(), parentGeo.height()) * NPoint2D.fromQPoint(self._posExtent)
        self._CtrObj.setGeometry(NQWrap.Rec(origPx.toQPoint(), NQWrap.Size(*endPx.toList())))
