from PySide2 import QtCore, QtGui, QtWidgets
import sys, os

# Get the local path to add to sys.path to properly load custom modules.
if __name__ == "__main__":
    lp = __file__.rsplit("/", 2)[0]; sys.path.extend([lp, lp.replace("/", "\\")]); del lp

from Nodes.CoreObject import NObject
from Nodes.CoreUtils import UCoreUtils
from Nodes.CoreProperties import *
from Nodes import Core
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
    CREATE_OBJECT = 8


class NWidget(NObject):
    """
    Base class for widgets. Designed to be used as a friend class of any QWidget subclass.
    Cannot function on its own and needs to be wrapped with a QWidget.
    """
    # Shared signal. Fired when the widget's geometry changes.
    OnGeometryChange = QtCore.Signal(QtCore.QRect)
    sg_enterPressed = QtCore.Signal(QtCore.QObject)

    def __init__(self, owner, name=""):
        NObject.__init__(self, owner=owner, name=name, UseHardRef=True)



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


class NTextEdit(NWidget, QtWidgets.QLineEdit):

    def __init__(self, p):
        NWidget.__init__(self, p)
        QtWidgets.QLineEdit.__init__(self, p)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Enter or e.key() == QtCore.Qt.Key_Return:
            self.sg_enterPressed.emit(self)
        else:
            super(NTextEdit, self).keyPressEvent(e)


class NListItem(NWidget, QtWidgets.QListWidgetItem):
    def __init__(self, p=None, **kwargs):
        NWidget.__init__(self, p)
        QtWidgets.QListWidgetItem.__init__(self, p)
        self._classToSpawn = kwargs.get('cls', kwargs.get('class', None))
        self.setText(kwargs.get("tx", kwargs.get("text", "UNAMMED")))


class NListWidget(NWidget, QtWidgets.QListWidget):
    def __init__(self, p):
        NWidget.__init__(self, p)
        QtWidgets.QListWidget.__init__(self, p)

    def keyPressEvent(self, event):
        if (event.key() == QtCore.Qt.Key_Return or
                event.key() == QtCore.Qt.Key_Enter):
            self.sg_enterPressed.emit(self)
        else:
            super(NListWidget, self).keyPressEvent(event)




class NCreationDialog(NWidget, QtWidgets.QWidget):
    def __init__(self, p, pos, **kwargs):
        NWidget.__init__(self, p)
        QtWidgets.QWidget.__init__(self, p)
        self.setObjectName("Object_spawner")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.resize(383, 318)
        self.move(pos)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background-color: rgba(46, 49, 54, 90); border-radius: 5px;")
        self.setInputMethodHints(QtCore.Qt.ImhNone)

        # Widgets
        self.verticalLayoutWidget = None
        self.verticalLayout = None
        self.lineInput = None
        self.listWidget = None

        self._constructWidget()

        self.listWidget.itemClicked.connect(self._receiveItem)
        self.listWidget.sg_enterPressed.connect(self._receiveEnter)
        self.lineInput.sg_enterPressed.connect(self._receiveEnter)

        d = kwargs.get("ViewportClickedDelegate", None)
        if d:
            d.connect(self._onViewportClick)

        self._populateQlist()
        self.show()

    def _constructWidget(self):
        self.verticalLayoutWidget = QtWidgets.QWidget(self)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(0, 0, 381, 321))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lineInput = NTextEdit(self.verticalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.lineInput.sizePolicy().hasHeightForWidth())
        self.lineInput.setSizePolicy(sizePolicy)
        self.lineInput.setMinimumSize(QtCore.QSize(0, 17))
        self.lineInput.setMaximumSize(QtCore.QSize(16777215, 30))
        self.lineInput.setStyleSheet("background-color: rgb(128, 128, 135);")
        self.lineInput.setObjectName("textEdit")
        self.verticalLayout.addWidget(self.lineInput)
        self.listWidget = NListWidget(self.verticalLayoutWidget)
        self.listWidget.setFrameShape(QtWidgets.QFrame.Box)
        self.listWidget.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout.addWidget(self.listWidget)

    def _onViewportClick(self, event: QtCore.QEvent):
        self.close()

    def _receiveItem(self, item: NListItem):
        self.lineInput.setText(item.text())

    def _receiveEnter(self, obj: QtCore.QObject):
        text = self.lineInput.text()
        new_object = GA.functionClasses.get(text, Error_Type)(text)

        if not isinstance(new_object, Error_Type):
            print('try create node')
            new_node = NUiNodeObject(new_object)
            # self.parent().scene().addItem(new_node)

        g = QtGui.QBrush(QtCore.Qt.green)

        out = QtGui.QPen(QtCore.Qt.black)
        out.setWidth(2)

        rectangle = self.parent().scene().addRect(100, 0, 80, 100, out, g)
        self.parent().scene().addItem(new_node)


    def _populateQlist(self):
        availableFuncs = GA.functionClasses.values()

        for obj in availableFuncs:
            newItem = NListItem(tx=obj.__name__, cls=obj)
            self.listWidget.addItem(newItem)


class NGraphicsView(NWidget, QtWidgets.QGraphicsView):
    signal_KeyPressed = QtCore.Signal(str)
    sg_ViewportClicked = QtCore.Signal(QtCore.QEvent)

    def __init__(self, parent):
        NWidget.__init__(self, parent)
        QtWidgets.QGraphicsView.__init__(self, parent)
        self.setMouseTracking(True)
        self.gridVisToggle = True
        self.gridSnapToggle = False
        self._nodeSnap = False
        self.selectedNodes = None
        self._creationDialog = None

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

        elif (event.button() == QtCore.Qt.RightButton and
                event.modifiers() == QtCore.Qt.NoModifier):
            self.currentState = ECurrentState.CREATE_OBJECT
            self.initMousePos = event.pos()
            print('got right click')
            # @TODO spawn UI object spawner here.


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

        self.sg_ViewportClicked.emit(event)
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

        elif self.currentState == ECurrentState.CREATE_OBJECT:
            self.SpawnCreateObjDialog(event.pos())

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

    def SpawnCreateObjDialog(self, pos):
        if self._creationDialog:
            self._creationDialog.close()

        self._creationDialog = NCreationDialog(self, pos, ViewportClickedDelegate=self.sg_ViewportClicked)

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
        self.gridSize = 50  # This is the size of grid to use. In pixels.
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


class NUiNodeObject(QtWidgets.QGraphicsItem):
    def __init__(self, baseNode: NObject = None):
        # NWidget.__init__(self, None, baseNode.getName() if baseNode else "UNDEFINED")
        super(NUiNodeObject, self).__init__()

        self._wrappedNode = None
        self._exposedAttributes = {}
        # self._createStyle()
        print('spawned ui node, base: %s' % baseNode)
        if baseNode:
            self._wrappedNode = baseNode
            # self._initializeAttrs()

    def height(self):
        """
        Increment the final height of the node every time an attribute
        is created.
        """
        count = self._exposedAttributes.__len__()
        if count > 0:
            return (self.baseHeight +
                    self.attrHeight * count +
                    self.border +
                    0.5 * self.radius)
        else:
            return self.baseHeight

    def _initializeAttrs(self):
        for prop in dir(self._wrappedNode):
            item = getattr(self._wrappedNode, prop)
            if callable(item):
                attr = getattr(item, EXPOSEDPROPNAME, None)
                attrDetails = getattr(item, EXPOSED_EXTRADATA, None)
                if attr and EPropType.PT_Readable in attr:
                    niceName = attrDetails.get('niceName', "")
                    attr = NAttribute(prop, niceName, self)
                    self._exposedAttributes[prop] = attr

            elif isinstance(item, Core.NDynamicAttr):
                pass

    def _createStyle(self, config=None):
        """
        Read the node style from the configuration file.
        """
        self.setAcceptHoverEvents(True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)

        # Dimensions.
        self.baseWidth = 100 #config['node_width']
        self.baseHeight = 150 #config['node_height']
        self.attrHeight = 20 #config['node_attr_height']
        self.border = 2 #config['node_border']
        self.radius = 5 #config['node_radius']

        self.nodeCenter = QtCore.QPointF()
        self.nodeCenter.setX(self.baseWidth / 2.0)
        self.nodeCenter.setY(self.height() / 2.0)

        defaultcolor = QtGui.QColor(128, 128, 128)

        self._brush = QtGui.QBrush()
        self._brush.setStyle(QtCore.Qt.SolidPattern)
        self._brush.setColor(defaultcolor)

        self._pen = QtGui.QPen()
        self._pen.setStyle(QtCore.Qt.SolidLine)
        self._pen.setWidth(self.border)
        self._pen.setColor(defaultcolor)

        self._penSel = QtGui.QPen()
        self._penSel.setStyle(QtCore.Qt.SolidLine)
        self._penSel.setWidth(self.border)
        self._penSel.setColor(defaultcolor)

        self._textPen = QtGui.QPen()
        self._textPen.setStyle(QtCore.Qt.SolidLine)
        self._textPen.setColor(defaultcolor)

        self._nodeTextFont = QtGui.QFont()
        self._attrTextFont = QtGui.QFont()

        self._attrBrush = QtGui.QBrush()
        self._attrBrush.setStyle(QtCore.Qt.SolidPattern)

        self._attrBrushAlt = QtGui.QBrush()
        self._attrBrushAlt.setStyle(QtCore.Qt.SolidPattern)

        self._attrPen = QtGui.QPen()
        self._attrPen.setStyle(QtCore.Qt.SolidLine)

    def boundingRect(self):
        """
        The bounding rect based on the width and height variables.
        """
        rect = QtCore.QRect(0, 0, self.baseWidth, self.height)
        rect = QtCore.QRectF(rect)
        return rect

    def shape(self):
        """
        The shape of the item.
        """
        path = QtGui.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def paint(self, painter, option, widget=None):
        """
        Paint the node and attributes.
        """
        # Node base.
        painter.setBrush(self._brush)
        painter.setPen(self.pen)

        painter.drawRoundedRect(0, 0,
                                self.baseWidth,
                                self.height,
                                self.radius,
                                self.radius)

        # Node label.
        painter.setPen(self._textPen)
        painter.setFont(self._nodeTextFont)

        metrics = QtGui.QFontMetrics(painter.font())
        text_width = metrics.boundingRect(self.name).width() + 14
        text_height = metrics.boundingRect(self.name).height() + 14
        margin = (text_width - self.baseWidth) * 0.5
        textRect = QtCore.QRect(-margin,
                                -text_height,
                                text_width,
                                text_height)

        painter.drawText(textRect,
                         QtCore.Qt.AlignCenter,
                         self.name)

        # Attributes.
        offset = 0
        for attr in self.attrs:
            nodzInst = self.scene().views()[0]
            config = nodzInst.config

            # Attribute rect.
            rect = QtCore.QRect(self.border / 2,
                                self.baseHeight - self.radius + offset,
                                self.baseWidth - self.border,
                                self.attrHeight)

            attrData = self.attrsData[attr]
            name = attr

            preset = attrData['preset']

            # Attribute base.
            tmpcolor = QtGui.QColor(128,128,128)
            self._attrBrush.setColor(tmpcolor)
            if self.alternate:
                self._attrBrushAlt.setColor(tmpcolor)

            self._attrPen.setColor(QtGui.QColor.black)
            painter.setPen(self._attrPen)
            painter.setBrush(self._attrBrush)
            if (offset / self.attrHeight) % 2:
                painter.setBrush(self._attrBrushAlt)

            painter.drawRect(rect)

            # Attribute label.
            painter.setPen(QtGui.QColor.black)
            painter.setFont(self._attrTextFont)

            # Search non-connectable attributes.
            if nodzInst.drawingConnection:
                if self == nodzInst.currentHoveredNode:
                    if (attrData['dataType'] != nodzInst.sourceSlot.dataType or
                            (nodzInst.sourceSlot.slotType == 'plug' and attrData['socket'] == False or
                             nodzInst.sourceSlot.slotType == 'socket' and attrData['plug'] == False)):
                        # Set non-connectable attributes color.
                        painter.setPen(tmpcolor)

            textRect = QtCore.QRect(rect.left() + self.radius,
                                    rect.top(),
                                    rect.width() - 2 * self.radius,
                                    rect.height())
            painter.drawText(textRect, QtCore.Qt.AlignVCenter, name)

            offset += self.attrHeight


class NAttribute(NWidget, QtWidgets.QWidget):
    def __init__(self, name, niceName="", parent=None):
        """
        Initialize a UI attribute. They represent an actual attribute on the node / function.
        :param name: The attribute name.
        :type name: String.
        :param niceName: The attribute display name if wanted.
        :type niceName: String.
        :param parent: A reference to a parent widget.
        :type parent: Subclass of QWidget reference.
        """
        NWidget.__init__(self, parent, name)
        QtWidgets.QWidget.__init__(self, None)
        self._attrName = name
        self._displayName = niceName if niceName != "" else name

        #  Widget refs
        self.horizontalLayout = None
        self.widget = None
        self.label = None
        self.widget_2 = None

        self._construct()

        self.setGeometry(QtCore.QRect(0, 0, 192, 24))

    def _construct(self):
        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.widget = QtWidgets.QWidget(self)
        self.widget.setFixedSize(QtCore.QSize(20, 20))
        self.widget.setStyleSheet("background-color: rgb(132, 132, 132); border: 2px solid rgba(0, 170, 230, 128); border-radius: 10px")
        self.widget.setObjectName("widget")
        self.horizontalLayout.addWidget(self.widget)
        self.label = QtWidgets.QLabel(self)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.widget_2 = QtWidgets.QWidget(self)
        self.widget_2.setFixedSize(QtCore.QSize(20, 20))
        self.widget_2.setStyleSheet("background-color: rgb(132, 132, 132); border: 2px solid rgba(0, 170, 230, 128); border-radius: 10px")
        self.widget_2.setObjectName("widget_2")
        self.horizontalLayout.addWidget(self.widget_2)

