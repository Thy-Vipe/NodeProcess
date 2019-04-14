from PySide2 import QtCore
from Nodes.Core import NObject
from Windows.CoreNWindows import *
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
    def __init__(self, anchorType: EAnchorType, InOwningObj: QtWidgets.QWidget, InObj: QtWidgets.QWidget, **kwargs):
        """
        Initialize the anchor object.
        :param anchorType: The anchor mode to use, from EAnchorType.
        :param InOwningObj: The widget owning the child to control. Must inherit from NWidget.
        :param InObj: The child to control. Must inherit from NWidget.
        :param kwargs: Extra parameters for this anchor: bParentIsWindow,...
        """
        super(NAnchor, self).__init__(name="%s's Anchor" % InObj.objectName(), owner=InObj, noClassRegister=True)

        geo = InObj.geometry(); pgeo = InOwningObj.geometry()
        if kwargs.get("bParentIsWindow", False):
            pgeo = NQWrap.Rec(0, 0, pgeo.width(), pgeo.height())

        self._baseGeometry = geo; self._baseParentGeo = pgeo
        PtA = NPoint2D(geo.x(), geo.y()) / NPoint2D(pgeo.width(), pgeo.height()); PtB = NPoint2D(geo.width(), geo.height()) / NPoint2D(pgeo.width(), pgeo.height())

        self._posOrigRelative = PtA; self._posOrig = NQWrap.Pt(geo.x(), geo.y())
        self._posExtentRelative = PtB; self._posExtent = NQWrap.Pt(geo.width(), geo.height())

        # Used if the position is calculated Fixed
        tmp = NPoint2D(geo.x(), geo.y()) - NPoint2D(pgeo.x(), pgeo.y()); self._origOffset = tmp.toQPoint()

        # Used if the position is calculated Fixed
        tmp = NPoint2D(geo.width(), geo.height()) - NPoint2D(pgeo.width(), pgeo.height()); self._extentOffset = tmp.toQPoint()

        self._anchor = anchorType
        self._OwningObj = InOwningObj
        self._owningObjIsWindow = kwargs.get("bParentIsWindow", False)
        self._CtrObj = InObj
        InOwningObj.OnGeometryChange.connect(self.__updateWrappedObjectGeo)

    def __updateWrappedObjectGeo(self, InGeo):
        """
        Update the child widget geometry according to the anchor's parameters.
        :param InGeo: The new geometry to update from. This assumes that this geo is the parent's geo.
        """
        InGeo = NQWrap.Rec(0, 0, InGeo.width(), InGeo.height()) if self._owningObjIsWindow else InGeo

        newGeo = NQWrap.Rec(self.getPosition(InGeo), self.getExtent(InGeo))
        self._CtrObj.setGeometry(newGeo)

    def getExtent(self, newGeo, bAsSize=True):
        """
        Calculate the new extent for this anchor.
        :param newGeo: The new geometry to calculate the output geometry from.
        :param bAsSize: True by default. Returns the extent as QSize instead of QPoint.
        :return: The new extent.
        """
        if self._anchor in (EAnchorType.FixedRelative, EAnchorType.RelativeRelative):
            endPx = NPoint2D(newGeo.width(), newGeo.height()) * NPoint2D.fromQPoint(self._posExtent)
            return endPx.toQPoint() if not bAsSize else NQWrap.Size(*endPx.toList())

        elif self._anchor in (EAnchorType.FixedFixed, EAnchorType.RelativeFixed):
            endPx = NQWrap.Pt(newGeo.width(), newGeo.height()) - self._extentOffset
            return endPx if not bAsSize else NQWrap.Size(endPx.x(), endPx.y())

    def getPosition(self, newGeo):
        """
        Calculate the new position for this anchor.
        :param newGeo: The new geometry to calculate the output geometry from.
        :return: The new position.
        """
        if self._anchor in (EAnchorType.RelativeFixed, EAnchorType.RelativeRelative):
            origPx = NPoint2D(newGeo.width(), newGeo.height()) * NPoint2D.fromQPoint(self._posOrig)
            return origPx.toQPoint()

        elif self._anchor in (EAnchorType.FixedRelative, EAnchorType.FixedFixed):
            origPx = NQWrap.Pt(newGeo.x(), newGeo.y()) - self._origOffset
            return origPx

    def update(self):
        self.__updateWrappedObjectGeo(self._OwningObj.geometry())

    def setAnchors(self, inStart, inEnd, bEndIsExtent=False):
        self._posOrig = inStart
        self._posExtent = inEnd - inStart if not bEndIsExtent else inEnd

    def getRectangle(self):
        return self._CtrObj.geometry()
