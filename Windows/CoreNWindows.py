from PySide2 import QtCore, QtGui, QtWidgets
import sys, os

# Get the local path to add to sys.path to properly load custom modules.
if __name__ == "__main__":
    lp = __file__.rsplit("/", 2)[0]; sys.path.extend([lp, lp.replace("/", "\\")]); del lp

from Nodes.Core import NObject
from Nodes.CoreUtils import UCoreUtils
from Windows import NWindowsUtils


class ECurrentState:
    """
    Enum used for NGraphics View states.
    """
    DEFAULT = 0
    ZOOM_VIEW = 1
    DRAG_VIEW = 2
    SELECT = 3
    DRAG_ITEM = 4
    ADD_SELECT = 5
    SUB_SELECT = 6
    TGL_SELECT = 7


class NWidget(NObject):
    """
    Base class for widgets. Designed to be used as a friend class of any QWidget subclass.
    Cannot function on its own and needs to be wrapped with a QWidget.
    """
    # Shared signal. Fired when the widget's geometry changes.
    OnGeometryChange = QtCore.Signal(QtCore.QRect)

    def __init__(self, owner, name=""):
        NObject.__init__(self, name, owner)


        self.__anchor = None

    def setGeometry(self, geo):
        super(NWidget, self).setGeometry(geo)
        self.OnGeometryChange.emit(geo)

    def setObjectName(self, name):
        super(NWidget, self).setObjectName(name)
        self.setName(name)

    def getAnchor(self):
        """
        Get the anchor of this Widget. None if non-existing.
        :return: The anchor object reference.
        """
        return self.__anchor

    def addAnchor(self, inPosA, inPosB):
        self.__anchor = NWindowsUtils.NAnchor(self.getParent(), self, inPosA, inPosB)
        self.__anchor.update()


class NGraphicsView(NWidget, QtWidgets.QGraphicsView):
    signal_KeyPressed = QtCore.Signal(str)

    def __init__(self, parent):
        NWidget.__init__(self, parent)
        QtWidgets.QGraphicsView.__init__(self, parent)
        self.setMouseTracking(True)
        self.gridVisToggle = True
        self.gridSnapToggle = False
        self._nodeSnap = False
        self.selectedNodes = None

        # Connections data.
        self.drawingConnection = False
        self.currentHoveredNode = None
        self.sourceSlot = None

        # Display options.
        self.currentState = ECurrentState.DEFAULT
        self.pressedKeys = list()

        # Momentous data.
        self.initMousePos = None
        self.zoomInitialPos = None
        self.prevPos = None
        self.initMouse = None
        self.previousMouseOffset = 0.0
        self.offset = 0.0
        self.zoomDirection = 0.0
        self.zoomIncr = 0.0

        self.initialize()

    def initialize(self):
        """
        Setup the view's behavior.
        """
        # Setup view.
        self.setRenderHint(QtGui.QPainter.Antialiasing, 8)
        self.setRenderHint(QtGui.QPainter.TextAntialiasing, 8)
        self.setRenderHint(QtGui.QPainter.HighQualityAntialiasing, 1)
        self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, 1)
        self.setRenderHint(QtGui.QPainter.NonCosmeticDefaultPen, True)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.rubberband = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)

        # Setup scene.
        scene = NGraphicsScene(self)
        sceneWidth = self.geometry().width()
        sceneHeight = self.geometry().height()
        scene.setSceneRect(QtCore.QRect(0, 0, sceneWidth, sceneHeight))
        self.setScene(scene)

        # Tablet zoom.
        self.previousMouseOffset = 0
        self.zoomDirection = 0
        self.zoomIncr = 0

    def wheelEvent(self, event):
        """
        Zoom in the view with the mouse wheel.
        """
        self.currentState = ECurrentState.ZOOM_VIEW
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

        inFactor = 1.15
        outFactor = 1 / inFactor

        if event.delta() > 0:
            zoomFactor = inFactor
        else:
            zoomFactor = outFactor

        self.scale(zoomFactor, zoomFactor)
        self.currentState = ECurrentState.DEFAULT

    def mousePressEvent(self, event):
        """
        Initialize tablet zoom, drag canvas and the selection.
        """
        # Tablet zoom
        if (event.button() == QtCore.Qt.RightButton and
                event.modifiers() == QtCore.Qt.AltModifier):
            self.currentState = ECurrentState.ZOOM_VIEW
            self.initMousePos = event.pos()
            self.zoomInitialPos = event.pos()
            self.initMouse = QtGui.QCursor.pos()
            self.setInteractive(False)


        # Drag view
        elif event.button() == QtCore.Qt.MiddleButton:
            self.currentState = ECurrentState.DRAG_VIEW
            self.prevPos = event.pos()
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            self.setInteractive(False)


        # Rubber band selection
        elif (event.button() == QtCore.Qt.LeftButton and
              event.modifiers() == QtCore.Qt.NoModifier and
              self.scene().itemAt(self.mapToScene(event.pos()), QtGui.QTransform()) is None):
            self.currentState = ECurrentState.SELECT
            self._initRubberBand(event.pos())
            self.setInteractive(False)


        # Drag Item
        elif (event.button() == QtCore.Qt.LeftButton and
              event.modifiers() == QtCore.Qt.NoModifier and
              self.scene().itemAt(self.mapToScene(event.pos()), QtGui.QTransform()) is not None):
            self.currentState = ECurrentState.DRAG_ITEM
            self.setInteractive(True)


        # Add selection
        elif (event.button() == QtCore.Qt.LeftButton and
              QtCore.Qt.Key_Shift in self.pressedKeys and
              QtCore.Qt.Key_Control in self.pressedKeys):
            self.currentState = ECurrentState.ADD_SELECT
            self._initRubberBand(event.pos())
            self.setInteractive(False)


        # Subtract selection
        elif (event.button() == QtCore.Qt.LeftButton and
              event.modifiers() == QtCore.Qt.ControlModifier):
            self.currentState = ECurrentState.SUB_SELECT
            self._initRubberBand(event.pos())
            self.setInteractive(False)


        # Toggle selection
        elif (event.button() == QtCore.Qt.LeftButton and
              event.modifiers() == QtCore.Qt.ShiftModifier):
            self.currentState = ECurrentState.TGL_SELECT
            self._initRubberBand(event.pos())
            self.setInteractive(False)


        else:
            self.currentState = ECurrentState.DEFAULT

        super(NGraphicsView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Update tablet zoom, canvas dragging and selection.
        """
        # Zoom.
        if self.currentState == ECurrentState.ZOOM_VIEW:
            offset = self.zoomInitialPos.x() - event.pos().x()

            if offset > self.previousMouseOffset:
                self.previousMouseOffset = offset
                self.zoomDirection = -1
                self.zoomIncr -= 1

            elif offset == self.previousMouseOffset:
                self.previousMouseOffset = offset
                if self.zoomDirection == -1:
                    self.zoomDirection = -1
                else:
                    self.zoomDirection = 1

            else:
                self.previousMouseOffset = offset
                self.zoomDirection = 1
                self.zoomIncr += 1

            if self.zoomDirection == 1:
                zoomFactor = 1.03
            else:
                zoomFactor = 1 / 1.03

            # Perform zoom and re-center on initial click position.
            pBefore = self.mapToScene(self.initMousePos)
            self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
            self.scale(zoomFactor, zoomFactor)
            pAfter = self.mapToScene(self.initMousePos)
            diff = pAfter - pBefore

            self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
            self.translate(diff.x(), diff.y())

        # Drag canvas.
        elif self.currentState == ECurrentState.DRAG_VIEW:
            offset = self.prevPos - event.pos()
            self.prevPos = event.pos()
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + offset.y())
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + offset.x())

        # RuberBand selection.
        elif (self.currentState == ECurrentState.SELECT or
              self.currentState == ECurrentState.ADD_SELECT or
              self.currentState == ECurrentState.SUB_SELECT or
              self.currentState == ECurrentState.TGL_SELECT):
            self.rubberband.setGeometry(QtCore.QRect(self.origin, event.pos()).normalized())

        super(NGraphicsView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Apply tablet zoom, dragging and selection.
        """
        # Zoom the View.
        if self.currentState == ECurrentState.ZOOM_VIEW:
            self.offset = 0
            self.zoomDirection = 0
            self.zoomIncr = 0
            self.setInteractive(True)


        # Drag View.
        elif self.currentState == ECurrentState.DRAG_VIEW:
            self.setCursor(QtCore.Qt.ArrowCursor)
            self.setInteractive(True)


        # Selection.
        elif self.currentState == ECurrentState.SELECT:
            self.rubberband.setGeometry(QtCore.QRect(self.origin,
                                                     event.pos()).normalized())
            painterPath = self._releaseRubberBand()
            self.setInteractive(True)
            self.scene().setSelectionArea(painterPath)


        # Add Selection.
        elif self.currentState == ECurrentState.ADD_SELECT:
            self.rubberband.setGeometry(QtCore.QRect(self.origin,
                                                     event.pos()).normalized())
            painterPath = self._releaseRubberBand()
            self.setInteractive(True)
            for item in self.scene().items(painterPath):
                item.setSelected(True)


        # Subtract Selection.
        elif self.currentState == ECurrentState.SUB_SELECT:
            self.rubberband.setGeometry(QtCore.QRect(self.origin,
                                                     event.pos()).normalized())
            painterPath = self._releaseRubberBand()
            self.setInteractive(True)
            for item in self.scene().items(painterPath):
                item.setSelected(False)


        # Toggle Selection
        elif self.currentState == ECurrentState.TGL_SELECT:
            self.rubberband.setGeometry(QtCore.QRect(self.origin,
                                                     event.pos()).normalized())
            painterPath = self._releaseRubberBand()
            self.setInteractive(True)
            for item in self.scene().items(painterPath):
                if item.isSelected():
                    item.setSelected(False)
                else:
                    item.setSelected(True)

        self.currentState = ECurrentState.DEFAULT

        super(NGraphicsView, self).mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        """
        Save pressed key and apply shortcuts.
        Shortcuts are:
        DEL - Delete the selected nodes
        F - Focus view on the selection
        """
        if event.key() not in self.pressedKeys:
            self.pressedKeys.append(event.key())

        if event.key() in (QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace):
            self._deleteSelectedNodes()

        if event.key() == QtCore.Qt.Key_F:
            self._focus()

        if event.key() == QtCore.Qt.Key_S:
            self._nodeSnap = True

        # Emit signal.
        self.signal_KeyPressed.emit(event.key())

    def keyReleaseEvent(self, event):
        """
        Clear the key from the pressed key list.
        """
        if event.key() == QtCore.Qt.Key_S:
            self._nodeSnap = False

        if event.key() in self.pressedKeys:
            self.pressedKeys.remove(event.key())

    def _initRubberBand(self, position):
        """
        Initialize the rubber band at the given position.
        """
        self.rubberBandStart = position
        self.origin = position
        self.rubberband.setGeometry(QtCore.QRect(self.origin, QtCore.QSize()))
        self.rubberband.show()

    def _releaseRubberBand(self):
        """
        Hide the rubber band and return the path.
        """
        painterPath = QtGui.QPainterPath()
        rect = self.mapToScene(self.rubberband.geometry())
        painterPath.addPolygon(rect)
        self.rubberband.hide()
        return painterPath

    def _focus(self):
        """
        Center on selected nodes or all of them if no active selection.
        """
        if self.scene().selectedItems():
            itemsArea = self._getSelectionBoundingBox()
            self.fitInView(itemsArea, QtCore.Qt.KeepAspectRatio)
        else:
            itemsArea = self.scene().itemsBoundingRect()
            self.fitInView(itemsArea, QtCore.Qt.KeepAspectRatio)

    def _getSelectionBoundingBox(self):
        """
        Return the bounding box of the selection.
        """
        bbx_min = None
        bbx_max = None
        bby_min = None
        bby_max = None
        bbw = 0
        bbh = 0
        for item in self.scene().selectedItems():
            pos = item.scenePos()
            x = pos.x()
            y = pos.y()
            w = x + item.boundingRect().width()
            h = y + item.boundingRect().height()

            # bbx min
            if bbx_min is None:
                bbx_min = x
            elif x < bbx_min:
                bbx_min = x
            # end if

            # bbx max
            if bbx_max is None:
                bbx_max = w
            elif w > bbx_max:
                bbx_max = w
            # end if

            # bby min
            if bby_min is None:
                bby_min = y
            elif y < bby_min:
                bby_min = y
            # end if

            # bby max
            if bby_max is None:
                bby_max = h
            elif h > bby_max:
                bby_max = h
            # end if
        # end if
        bbw = bbx_max - bbx_min
        bbh = bby_max - bby_min
        return QtCore.QRectF(QtCore.QRect(bbx_min, bby_min, bbw, bbh))

    def _deleteSelectedNodes(self):
        """
        Delete selected nodes.
        """
        selected_nodes = list()
        for node in self.scene().selectedItems():
            selected_nodes.append(node.name)
            node._remove()

        # Emit signal.
        self.signal_NodeDeleted.emit(selected_nodes)

    def _returnSelection(self):
        """
        Wrapper to return selected items.
        """
        selected_nodes = list()
        if self.scene().selectedItems():
            for node in self.scene().selectedItems():
                selected_nodes.append(node.name)

        # Emit signal.
        self.signal_NodeSelected.emit(selected_nodes)


class NGraphicsScene(QtWidgets.QGraphicsScene):

    """
    The scene displaying all the nodes.
    """
    signal_NodeMoved = QtCore.Signal(str, object)

    def __init__(self, parent):
        """
        Initialize the class.
        """
        super(NGraphicsScene, self).__init__(parent)

        # General.
        self.gridSize = 50 # This is the size of grid to use. In pixels.
        self.pen = None

        # Nodes storage.
        self.nodes = dict()

    def dragEnterEvent(self, event):
        """
        Make the dragging of nodes into the scene possible.
        """
        event.setDropAction(QtCore.Qt.MoveAction)
        event.accept()

    def dragMoveEvent(self, event):
        """
        Make the dragging of nodes into the scene possible.
        """
        event.setDropAction(QtCore.Qt.MoveAction)
        event.accept()

    def dropEvent(self, event):
        """
        Create a node from the dropped item.
        """
        # Emit signal.
        self.signal_Dropped.emit(event.scenePos())

        event.accept()

    def drawBackground(self, painter, rect):
        """
        Draw a grid in the background.
        """
        if self.views()[0].gridVisToggle:
            leftLine = rect.left() - rect.left() % self.gridSize
            topLine = rect.top() - rect.top() % self.gridSize
            lines = list()

            i = int(leftLine)
            while i < int(rect.right()):
                lines.append(QtCore.QLineF(i, rect.top(), i, rect.bottom()))
                i += self.gridSize

            u = int(topLine)
            while u < int(rect.bottom()):
                lines.append(QtCore.QLineF(rect.left(), u, rect.right(), u))
                u += self.gridSize

            self.pen = QtGui.QPen()
            self.pen.setColor(QtGui.QColor(101, 110, 124, 64))
            self.pen.setWidth(0)
            painter.setPen(self.pen)
            painter.drawLines(lines)

    def updateScene(self):
        """
        Update the connections position.
        """
        for connection in [i for i in self.items() if isinstance(i, NConnection)]:
            connection.target_point = connection.target.center()
            connection.source_point = connection.source.center()
            connection.updatePath()


class NConnection(NWidget, QtWidgets.QGraphicsPathItem):

    """
    A graphics path representing a connection between two attributes.
    """

    def __init__(self, source_point, target_point, source, target):
        """
        Initialize the class.
        :param sourcePoint: Source position of the connection.
        :type  sourcePoint: QPoint.
        :param targetPoint: Target position of the connection
        :type  targetPoint: QPoint.
        :param source: Source item (plug or socket).
        :type  source: class.
        :param target: Target item (plug or socket).
        :type  target: class.
        """
        super(NConnection, self).__init__(None)

        self.setZValue(1)

        # Storage.
        self.socketNode = None
        self.socketAttr = None
        self.plugNode = None
        self.plugAttr = None

        self.source_point = source_point
        self.target_point = target_point
        self.source = source
        self.target = target

        self.plugItem = None
        self.socketItem = None

        self.movable_point = None

        self.data = tuple()

        # Methods.
        self._createStyle()

    def _createStyle(self):
        """
        Create style for this path.
        """
        self.setAcceptHoverEvents(True)
        self.setZValue(-1)

        self._pen = QtGui.QPen(QtGui.QColor(255, 128, 0))
        self._pen.setWidth(5.0)

    def mousePressEvent(self, event):
        """
        Snap the Connection to the mouse.
        """
        GraphicsView = self.scene().views()[0]

        for item in GraphicsView.scene().items():
            if isinstance(item, NConnection):
                item.setZValue(0)

        GraphicsView.drawingConnection = True

        d_to_target = (event.pos() - self.target_point).manhattanLength()
        d_to_source = (event.pos() - self.source_point).manhattanLength()
        if d_to_target < d_to_source:
            self.target_point = event.pos()
            self.movable_point = 'target_point'
            self.target.disconnect(self)
            self.target = None
            GraphicsView.sourceSlot = self.source
        else:
            self.source_point = event.pos()
            self.movable_point = 'source_point'
            self.source.disconnect(self)
            self.source = None
            GraphicsView.sourceSlot = self.target

        self.updatePath()

    def mouseMoveEvent(self, event):
        """
        Move the Connection with the mouse.
        """
        GraphicsView = self.scene().views()[0]
        config = GraphicsView.config

        mbb = UCoreUtils.createPointerBoundingBox(pointerPos=event.scenePos().toPoint(),
                                              bbSize=config['mouse_bounding_box'])

        # Get nodes in pointer's bounding box.
        targets = self.scene().items(mbb)

        '''if any(isinstance(target, NodeItem) for target in targets):

            if GraphicsView.sourceSlot.parentItem() not in targets:
                for target in targets:
                    if isinstance(target, NodeItem):
                        GraphicsView.currentHoveredNode = target
        else:
            GraphicsView.currentHoveredNode = None'''

        if self.movable_point == 'target_point':
            self.target_point = event.pos()
        else:
            self.source_point = event.pos()

        self.updatePath()

    def mouseReleaseEvent(self, event):
        """
        Create a Connection if possible, otherwise delete it.
        """
        GraphicsView = self.scene().views()[0]
        GraphicsView.drawingConnection = False

        slot = self.scene().itemAt(event.scenePos().toPoint(), QtGui.QTransform())

        if not isinstance(slot, SlotItem):
            self._remove()
            self.updatePath()
            super(NConnection, self).mouseReleaseEvent(event)
            return

        if self.movable_point == 'target_point':
            if slot.accepts(self.source):
                # Plug reconnection.
                self.target = slot
                self.target_point = slot.center()
                plug = self.source
                socket = self.target

                # Reconnect.
                socket.connect(plug, self)

                self.updatePath()
            else:
                self._remove()

        else:
            if slot.accepts(self.target):
                # Socket Reconnection
                self.source = slot
                self.source_point = slot.center()
                socket = self.target
                plug = self.source

                # Reconnect.
                plug.connect(socket, self)

                self.updatePath()
            else:
                self._remove()

    def _remove(self):
        """
        Remove this Connection from the scene.
        """
        if self.source is not None:
            self.source.disconnect(self)
        if self.target is not None:
            self.target.disconnect(self)

        scene = self.scene()
        scene.removeItem(self)
        scene.update()

    def updatePath(self):
        """
        Update the path.
        """
        self.setPen(self._pen)

        path = QtGui.QPainterPath()
        path.moveTo(self.source_point)
        dx = (self.target_point.x() - self.source_point.x()) * 0.5
        dy = self.target_point.y() - self.source_point.y()
        ctrl1 = QtCore.QPointF(self.source_point.x() + dx, self.source_point.y() + dy * 0)
        ctrl2 = QtCore.QPointF(self.source_point.x() + dx, self.source_point.y() + dy * 1)
        path.cubicTo(ctrl1, ctrl2, self.target_point)

        self.setPath(path)


class NUiNodeObj(QtWidgets.QGraphicsItem):
    def __init__(self):
        super(self, QtWidgets.QGraphicsItem).__init__()
