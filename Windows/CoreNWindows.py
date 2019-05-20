from PySide2 import QtCore, QtGui, QtWidgets
import sys, os, types

# Get the local path to add to sys.path to properly load custom modules.
if __name__ == "__main__":
    lp = __file__.rsplit("/", 2)[0]; sys.path.extend([lp, lp.replace("/", "\\")]); del lp

from Nodes.CoreObject import NObject
from Nodes.CoreUtils import UCoreUtils
from Nodes.CoreProperties import *
from Nodes import Core, FuncNodes
from Windows import NWindowsUtils


class ECurrentState:
    """
    Enum used for NGraphicsView states.
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


class NWidgetBase(NObject):
    """
    Base class for widgets. Designed to be used as a friend class of any QWidget subclass.
    Cannot function on its own and needs to be wrapped with a QWidget.
    """
    # Shared signal. Fired when the widget's geometry changes.
    OnGeometryChange = QtCore.Signal(QtCore.QRect)
    sg_enterPressed = QtCore.Signal(QtCore.QObject)
    sg_updated = QtCore.Signal()

    def __init__(self, owner, name=""):
        NObject.__init__(self, owner=owner, name=name, UseHardRef=True, noClassRegister=True)

        self.__anchor = None

    def setGeometry(self, geo):
        super(NWidgetBase, self).setGeometry(geo)
        self.OnGeometryChange.emit(geo)

    def setObjectName(self, name):
        super(NWidgetBase, self).setObjectName(name)
        self.setName(name)

    def getAnchor(self):
        """
        Get the anchor of this Widget. None if non-existing.
        :return: The anchor object reference.
        """
        return self.__anchor

    def anchor(self, anchorType, inOwnerOverride=None, bParentIsWindow=False):
        """
        Anchor this widget to the parent with the current position.
        """
        self.__anchor = NWindowsUtils.NAnchor(anchorType, self.parent() if not inOwnerOverride else inOwnerOverride, self, bParentIsWindow=bParentIsWindow)
        self.__anchor.update()

    def resizeEvent(self, event):
        super(NWidgetBase, self).resizeEvent(event)
        self.OnGeometryChange.emit(self.geometry())


class NWidget(NWidgetBase, QtWidgets.QWidget):
    def __init__(self, parent):
        NWidgetBase.__init__(self, parent)
        QtWidgets.QWidget.__init__(self, parent)


class NPropertyDisplay(QtWidgets.QWidget):
    def __init__(self, parent, label=None):
        super(NPropertyDisplay, self).__init__(parent)

        self._layout = QtWidgets.QHBoxLayout(self)
        self.content = []

        if label:
            lbl = QtWidgets.QLabel(self)
            lbl.setText(label)
            self.addItem(lbl)

    def addItem(self, obj):
        obj.setParent(self)
        self._layout.addWidget(obj)
        self.content.append(obj)


class NLineEdit(NWidgetBase, QtWidgets.QLineEdit):
    def __init__(self, p):
        NWidgetBase.__init__(self, p)
        QtWidgets.QLineEdit.__init__(self, p)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Enter or e.key() == QtCore.Qt.Key_Return:
            self.sg_enterPressed.emit(self)
            self.sg_updated.emit()

        else:
            super(NLineEdit, self).keyPressEvent(e)


class NSpinBox(NWidgetBase, QtWidgets.QSpinBox):
    def __init__(self, p):
        NWidgetBase.__init__(self, p)
        QtWidgets.QSpinBox.__init__(self, p)
        self.setButtonSymbols(QtWidgets.QSpinBox.NoButtons)
        self.valueChanged.connect(self.onChanged)
        self.setMinimum(-sys.maxsize-1)
        self.setMaximum(sys.maxsize)

    def onChanged(self, *args, **kwargs):
        self.sg_updated.emit()


class NDoubleBox(NWidgetBase, QtWidgets.QDoubleSpinBox):
    def __init__(self, p):
        NWidgetBase.__init__(self, p)
        QtWidgets.QDoubleSpinBox.__init__(self, p)
        self.setButtonSymbols(QtWidgets.QDoubleSpinBox.NoButtons)
        self.valueChanged.connect(self.onChanged)
        self.setMinimum(-sys.maxsize - 1)
        self.setMaximum(sys.maxsize)

    def onChanged(self, *args, **kwargs):
        self.sg_updated.emit()


class NScriptEd(NWidgetBase, QtWidgets.QTextEdit):
    sg_newText = QtCore.Signal(str)
    sg_enterPressed_get = QtCore.Signal(str)

    def __init__(self, parent):
        NWidgetBase.__init__(self, parent)
        QtWidgets.QTextEdit.__init__(self, parent)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Enter or e.key() == QtCore.Qt.Key_Return:
            self.sg_enterPressed.emit(self)
            self.sg_enterPressed_get.emit(self.toPlainText())

        self.sg_newText.emit(self.toPlainText())
        self.sg_updated.emit()
        super(NScriptEd, self).keyPressEvent(e)


class NListItem(NWidgetBase, QtWidgets.QListWidgetItem):
    def __init__(self, p=None, **kwargs):
        NWidgetBase.__init__(self, p)
        QtWidgets.QListWidgetItem.__init__(self, p)
        self._classToSpawn = kwargs.get('cls', kwargs.get('class', None))
        self.setText(kwargs.get("tx", kwargs.get("text", "UNAMMED")))


class NListWidget(NWidgetBase, QtWidgets.QListWidget):
    def __init__(self, p):
        NWidgetBase.__init__(self, p)
        QtWidgets.QListWidget.__init__(self, p)

    def keyPressEvent(self, event):
        if (event.key() == QtCore.Qt.Key_Return or
                event.key() == QtCore.Qt.Key_Enter):
            self.sg_enterPressed.emit(self)
        else:
            super(NListWidget, self).keyPressEvent(event)


class NEnumView(NWidgetBase, QtWidgets.QComboBox):
    ValueChanged = QtCore.Signal(object)

    def __init__(self, p, baseEnum: TEnum):
        NWidgetBase.__init__(self, p)
        QtWidgets.QComboBox.__init__(self, p)

        self.enumClass = baseEnum.__class__

        for k, v in baseEnum.items():
            self.addItem(k)

        self.currentIndexChanged.connect(self._onChanged)

    def _onChanged(self, v):
        print('changed')
        text = self.currentText()
        new = self.enumClass(self.enumClass.from_text(text))
        self.ValueChanged.emit(new)


class NPropertiesDialog(NWidgetBase, QtWidgets.QDialog):
    """
    When spawned, procedurally reads the attributes of the node it's attached to.
    """
    def __init__(self, parent, nodeObj):
        NWidgetBase.__init__(self, parent)
        QtWidgets.QDialog.__init__(self, parent)
        # self.setWindowModality(QtCore.Qt.ApplicationModal)

        assert isinstance(nodeObj, Core.NFunctionBase)
        self.resize(175, 100)
        self.nodeObj = Core.NWeakRef(nodeObj)
        # self._layoutWid = QtWidgets.QWidget(self)
        self._layout = QtWidgets.QVBoxLayout(self)
        self.setWindowTitle("%s's properties.." % self.nodeObj().getName().toString())
        self._generateItems()

    def _generateItems(self):

        for prop in self.nodeObj().getExposedProps():
            propInst = getattr(self.nodeObj(), prop)
            propData = self.nodeObj().__PropFlags__.get(prop, ())
            if isinstance(propInst, Core.NDynamicAttr) and EAttrType.AT_ReadOnly not in propData:
                dt = propInst.dataType()
                updater = GET_ATTRHOOK(self.nodeObj(), prop)
                tx = None
                if dt == EDataType.DT_String:
                    tx = NLineEdit(self)
                    tx.setText(str(propInst.get()))
                    tx.textChanged.connect(propInst.set)
                    obj = NPropertyDisplay(self, prop); obj.addItem(tx)
                    self._layout.addWidget(obj)

                elif dt == EDataType.DT_Script:
                    tx = NScriptEd(self)
                    tx.setText(str(propInst.get()))
                    tx.sg_enterPressed_get.connect(propInst.set)
                    self._layout.addWidget(tx)

                elif dt == EDataType.DT_Int:
                    tx = NSpinBox(self)
                    tx.valueChanged.connect(propInst.set)
                    tx.setValue(int(propInst.get()))
                    obj = NPropertyDisplay(self, prop); obj.addItem(tx)
                    self._layout.addWidget(obj)

                elif dt == EDataType.DT_Float:
                    tx = NDoubleBox(self)
                    tx.valueChanged.connect(propInst.set)
                    tx.setValue(float(propInst.get()))
                    obj = NPropertyDisplay(self, prop); obj.addItem(tx)
                    self._layout.addWidget(obj)

                elif dt == EDataType.DT_Bool:
                    tx = QtWidgets.QCheckBox(self)
                    tx.stateChanged.connect(propInst.set)
                    tx.setText(prop)
                    tx.setChecked(propInst.get())
                    self._layout.addWidget(tx)

                elif dt == EDataType.DT_Enum:
                    tx = NEnumView(self)
                    tx.ValueChanged.connet(propInst.set)
                    tx.setCurrentIndex(0)
                    obj = NPropertyDisplay(self, prop); obj.addItem(tx)
                    self._layout.addWidget(obj)

                if updater:
                    tx.sg_updated.connect(updater)

            elif callable(propInst) and isinstance(propInst, types.MethodType):
                if EAttrType.AT_kSlot in propData:
                    btn = QtWidgets.QPushButton(self)
                    btn.setText(prop)
                    btn.clicked.connect(propInst)
                    self._layout.addWidget(btn)

                else:
                    methData = getattr(propInst, EXPOSED_EXTRADATA, None)
                    getter = GET_GETTER(self.nodeObj(), prop)
                    updater = GET_ATTRHOOK(self.nodeObj(), prop)
                    typ = getattr(propInst, EXPOSEDPROPNAME, None)
                    if methData and typ:
                        dt = methData['dataType']
                        if EPropType.PT_Input in typ:
                            tx = None
                            if dt == EDataType.DT_String:
                                tx = NLineEdit(self)
                                tx.textChanged.connect(propInst)
                                if getter:
                                    tx.setText(getter())
                                obj = NPropertyDisplay(self, prop); obj.addItem(tx)
                                self._layout.addWidget(obj)

                            elif dt == EDataType.DT_Script:
                                tx = NScriptEd(self)
                                tx.sg_enterPressed_get.connect(propInst)
                                if getter:
                                    tx.setText(getter())
                                self._layout.addWidget(tx)

                            elif dt == EDataType.DT_Int:
                                tx = NSpinBox(self)
                                tx.valueChanged.connect(propInst)
                                if getter:
                                    tx.setValue(getter())
                                obj = NPropertyDisplay(self, prop); obj.addItem(tx)
                                self._layout.addWidget(obj)

                            elif dt == EDataType.DT_Float:
                                tx = NDoubleBox(self)
                                tx.valueChanged.connect(propInst)
                                if getter:
                                    tx.setValue(getter())
                                obj = NPropertyDisplay(self, prop); obj.addItem(tx)
                                self._layout.addWidget(obj)

                            elif dt == EDataType.DT_Bool:
                                tx = QtWidgets.QCheckBox(self)
                                tx.stateChanged.connect(propInst)
                                if getter:
                                    tx.setChecked(getter())
                                tx.setText(prop)
                                self._layout.addWidget(tx)

                            elif dt == EDataType.DT_Enum:
                                assert getter
                                tx = NEnumView(self, getter())
                                tx.setCurrentIndex(0)
                                tx.setCurrentText(getter().text())
                                tx.ValueChanged.connect(propInst)
                                obj = NPropertyDisplay(self, prop); obj.addItem(tx)
                                self._layout.addWidget(obj)

                            if updater:
                                tx.sg_updated.connect(updater)


            elif len(propData) != 0:
                pass


class NCreationDialog(NWidgetBase, QtWidgets.QWidget):
    def __init__(self, p, pos, **kwargs):
        NWidgetBase.__init__(self, p)
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
        self.lineInput = NLineEdit(self.verticalLayoutWidget)
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
        classObj = GA.functionClasses.get(text, Error_Type)
        new_object = Error_Type()

        if type(classObj) is type:
            new_object = classObj("%s_%d" % (text, len(GA.objectInstances(classObj))))

        elif callable(classObj) and isinstance(classObj, (types.FunctionType, types.MethodType)):
            count = GA.objectInstances(FuncNodes.NFunctionWrapper)
            n = 0
            for item in count:
                if item.getFunc().__name__ == classObj.__name__:
                    n += 1

            name = "%s_%d" % (classObj.__name__, n)
            new_object = FuncNodes.NFunctionWrapper(name, classObj)

        if not isinstance(new_object, Error_Type):
            new_node = NUiNodeObject(new_object.getName().toString(), new_object)
            self.parent().scene().addItem(new_node)


    def _populateQlist(self):

        for k, obj in GA.functionClasses.items():
            newItem = NListItem(tx=k, cls=obj)
            self.listWidget.addItem(newItem)


class NGraphicsView(NWidgetBase, QtWidgets.QGraphicsView):
    signal_KeyPressed = QtCore.Signal(str)
    sg_ViewportClicked = QtCore.Signal(QtCore.QEvent)
    sg_NodeDeleted = QtCore.Signal(str)
    sg_NodeDoubleClicked = QtCore.Signal(NObject)

    def __init__(self, parent):
        NWidgetBase.__init__(self, parent)
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
        self.sg_NodeDoubleClicked.connect(self.onNodeDoubleClick)

        # Tablet zoom.
        self.previousMouseOffset = 0
        self.zoomDirection = 0
        self.zoomIncr = 0

    def onNodeDoubleClick(self, obj):
        AttrDial = NPropertiesDialog(self, obj.node())
        AttrDial.show()

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
            node.remove()

        # Emit signal.
        self.sg_NodeDeleted.emit(selected_nodes)

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
            connection.target_point = connection.target.center() if connection.target else QPoint()
            connection.source_point = connection.source.center() if connection.source else QPoint()
            connection.updatePath()

    def addItem(self, item):
        super(NGraphicsScene, self).addItem(item)
        if isinstance(item, NUiNodeObject):
            self.nodes[item.name] = item


class NUiNodeObject(NWidgetBase, QtWidgets.QGraphicsItem):
    sg_Moved = QtCore.Signal(QtWidgets.QWidget, QtCore.QPoint)

    def __init__(self, name: str, baseNode: Core.NFunctionBase = None):

        self._wrappedNode = None
        if baseNode:
            self._wrappedNode = baseNode  # Keep a hard ref to this object
            baseNode.onClassChanged.bindFunction(self, 'onWrappedNodeChange')
            baseNode.onAttributeChanged.bindFunction(self, 'onWrappedNodeAttrChange')

        NWidgetBase.__init__(self, None, baseNode.getName() if baseNode else "UNDEFINED")
        QtWidgets.QGraphicsItem.__init__(self)

        self._exposedAttributes = {}
        self.attrs = []
        self.attrCount = 0

        self.name = name
        assert isinstance(name, str) and (not baseNode or isinstance(baseNode, NObject)), \
            "invalid input parameters for name or baseNode. Must be str and NObject or None"

        # Dimensions.
        self.baseWidth = 100
        self.baseHeight = 20
        self.attrHeight = 20
        self.border = 2
        self.radius = 5

        self.nodeCenter = QtCore.QPointF()

        self._createStyle()
        if self._wrappedNode:
            self._initializeAttrs()

        print('spawned ui node, base: %s' % baseNode)

    def initializeWith(self, obj: Core.NFunctionBase):
        assert isinstance(obj, Core.NFunctionBase)
        self._wrappedNode = obj

    def __jsonSerialize__(self, Serial: dict):
        geometry = self.geometry()
        Serial['pos'] = (geometry.x(), geometry.y())
        Serial['name'] = self.name
        visual_connections = []

        for item in self._exposedAttributes:
            data = {}
            item.__jsonSerialize__(data)
            visual_connections.append(data)

        Serial['vconnections'] = visual_connections

        instData = {}
        t = 0
        if self._wrappedNode:
            self._wrappedNode.__jsonSerialize__(instData)
            t = self._wrappedNode.classInfo()

        Serial['nodeData'] = instData
        Serial['nodeType'] = t

    def __jsonReader__(self, myDict: dict):
        self.setPos(QtCore.QPoint(*myDict['pos']))
        self.name = (myDict['name'])

        cls = g_a.functionClasses.get(myDict['nodeType'][0], None)

        if cls:
            if cls is FuncNodes.NFunctionWrapper:
                funcobj = g_a.functionClasses[myDict['nodeType'][1]]
                self._wrappedNode = cls(myDict['name'], funcobj)

            else:
                self._wrappedNode = cls(myDict['name'])
        else:
            raise RuntimeError("%s is not registered. Cannot deserialize data properly." % myDict['nodeType'][0])

        if self._wrappedNode:
            self._wrappedNode.__jsonReader__(myDict['nodeData'])
            self._wrappedNode.update()

        idx = 0
        for item in self._exposedAttributes:
            data = myDict['vconnections'][idx]

    def onWrappedNodeChange(self):
        print('detected wrapped node changed')
        pass

    def onWrappedNodeAttrChange(self, attr: str, state: EAttrChange, typ: EDataType = None, mode=0):
        if state == EAttrChange.AC_Removed and attr in self.attrs:
            self._deleteAttribute(self.attrs.index(attr))
        elif state == EAttrChange.AC_Added and typ:
            self._internal_addAttr(attr, -1, True if mode in (0, 2) else False, True if mode in (0, 1) else False, typ)

    @property
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
        for prop in self._wrappedNode.getExposedProps():
            item = getattr(self._wrappedNode, prop)
            itemInfo = self._wrappedNode.__PropFlags__.get(prop, ())
            if callable(item):
                attr = getattr(item, EXPOSEDPROPNAME, None)
                attrDetails = getattr(item, EXPOSED_EXTRADATA, None)
                if attr and EPropType.PT_Readable in attr and EPropType.PT_Internal not in attr and EAttrType.AT_Blacklisted not in itemInfo:
                    assert attrDetails.get('dataType', None) is not None  # all properties must have a data type.
                    self._internal_addAttr(prop, -1, EPropType.PT_Output in attr or EPropType.PT_FuncDelegateOut in attr,
                                           EPropType.PT_FuncDelegateIn in attr or EPropType.PT_Input in attr, attrDetails['dataType'])


            elif isinstance(item, Core.NDynamicAttr):
                bNoWrite = EAttrType.AT_ReadOnly not in itemInfo; bNoRead = EAttrType.AT_WriteOnly not in itemInfo
                self._internal_addAttr(prop, -1, bNoRead, bNoWrite, item.dataType())

    def _internal_addAttr(self, name, idx, bPlug, bSocket, dataType):
        """
        Create an attribute by expanding the node, adding a label and
        connection items.
        :type  name: str.
        :param name: The name of the attribute. The name has to be
                     unique as it is used as a key to store the node
                     object.
        :type  idx: int.
        :param idx: The index of the attribute in the node.
        :type  bPlug: bool.
        :param bPlug: Whether or not this attribute can emit connections.
        :type  bSocket: bool.
        :param bSocket: Whether or not this attribute can receive
                       connections.
        :type  dataType: type.
        :param dataType: Type of the data represented by this attribute
                         in order to highlight attributes of the same
                         type while performing a connection.
        """
        if name in self.attrs:
            print('An attribute with the same name already exists on this node : {0}'.format(name))
            print('Attribute creation aborted !')
            return

        numAllowedc = -1 if dataType != EDataType.DT_Delegate else 1
        # self.attrPreset = preset
        plugInst = socketInst = None
        # Create a plug connection item.
        if bPlug:
            plugInst = PlugItem(parent=self,
                                attribute=name,
                                index=self.attrCount,
                                preset=None,
                                dataType=dataType,
                                maxConnections=numAllowedc)

        # Create a socket connection item.
        if bSocket:
            socketInst = SocketItem(parent=self,
                                    attribute=name,
                                    index=self.attrCount,
                                    preset=None,
                                    dataType=dataType,
                                    maxConnections=1 if numAllowedc == -1 else -1)  # Can bind execs to multiple values.


        self.attrCount += 1

        # Add the attribute based on its index.
        if idx == -1 or idx > self.attrCount:
            self.attrs.append(name)
        else:
            self.attrs.insert(idx, name)

        # Store attr data.
        self._exposedAttributes[name] = NVisualAttribute(self, name, dataType, plugInst, socketInst)

        # Update node height.
        self.update()

    def _deleteAttribute(self, index):
        """
        Remove an attribute by reducing the node, removing the label
        and the connection items.
        :type  index: int.
        :param index: The index of the attribute in the node.
        """
        name = self.attrs[index]

        if self._exposedAttributes[name].getPlug():
            for connection in self._exposedAttributes[name].getPlug()().connections:
                self._exposedAttributes[name].getPlug()().disconnect(connection)

            self.scene().removeItem(self._exposedAttributes[name].getPlug()())

        # Remove plug and its connections.
        if self._exposedAttributes[name].getSocket():
            for connection in self._exposedAttributes[name].getSocket()().connections:
                self._exposedAttributes[name].getPlug().disconnect(connection)

            self.scene().removeItem(self._exposedAttributes[name].getSocket()())

        # Reduce node height.
        if self.attrCount > 0:
            self.attrCount -= 1

        # Remove attribute from node.
        if name in self.attrs:
            self.attrs.remove(name)

        del self._exposedAttributes[name]

        self.update()

    def _remove(self):
        """
        Remove this node instance from the scene.
        Make sure that all the connections to this node are also removed
        in the process
        """
        self.scene().nodes.pop(self.name)

        # Remove all connections.
        for k, v in self._exposedAttributes.items():
            p = v.getPlug()
            s = v.getSocket()
            if p:
                p().disconnect()
            if s:
                s().disconnect()


        # Remove node.
        scene = self.scene()
        g_a.killInstance(self._wrappedNode.getUUID())

        scene.removeItem(self)
        scene.update()

    def _createStyle(self, config=None):
        """
        Read the node style from the configuration file.
        """
        self.setAcceptHoverEvents(True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)

        self.nodeCenter = QtCore.QPointF()
        self.nodeCenter.setX(self.baseWidth / 2.0)
        self.nodeCenter.setY(self.height / 2.0)

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
        self._attrBrushAlt.setColor(QtGui.QColor(145, 145, 145))
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
        for attr in self._exposedAttributes.keys():
            scene = self.scene().views()[0]
            # config = nodzInst.config

            # Attribute rect.
            rect = QtCore.QRect(self.border / 2,
                                self.baseHeight - self.radius + offset,
                                self.baseWidth - self.border,
                                self.attrHeight)

            attrData = self._exposedAttributes[attr]
            name = attr

            # preset = attrData['preset']

            # Attribute base.
            tmpcolor = QtGui.QColor(128, 128, 128)
            self._attrBrush.setColor(tmpcolor)
            # if self.alternate:
            #     self._attrBrushAlt.setColor(tmpcolor)

            self._attrPen.setColor(tmpcolor)
            painter.setPen(self._attrPen)
            painter.setBrush(self._attrBrush)
            if (offset / self.attrHeight) % 2:
                painter.setBrush(self._attrBrushAlt)

            painter.drawRect(rect)

            # Attribute label.
            painter.setPen(QtGui.QColor().black())
            painter.setFont(self._attrTextFont)

            # Search non-connectable attributes.
            if scene.drawingConnection:
                if self == scene.currentHoveredNode:
                    if (attrData.dataType() != scene.sourceSlot.dataType or
                            (scene.sourceSlot.slotType == 'plug' and attrData.hasSocket() is False or
                             scene.sourceSlot.slotType == 'socket' and attrData.hasPlug() is False)):
                        # Set non-connectable attributes color.
                        painter.setPen(tmpcolor)

            textRect = QtCore.QRect(rect.left() + self.radius,
                                    rect.top(),
                                    rect.width() - 2 * self.radius,
                                    rect.height())
            painter.drawText(textRect, QtCore.Qt.AlignVCenter, name)

            offset += self.attrHeight

    @property
    def pen(self):
        """
        Return the pen based on the selection state of the node.
        """
        if self.isSelected():
            return self._penSel
        else:
            return self._pen

    def remove(self):
        self._remove()

    def getUUID(self):
        return self._wrappedNode.getUUID()

    def mousePressEvent(self, event):
        """
        Keep the selected node on top of the others.
        """
        nodes = self.scene().nodes
        for node in nodes.values():
            node.setZValue(1)

        for item in self.scene().items():
            if isinstance(item, NConnection):
                item.setZValue(1)

        self.setZValue(2)

        super(NUiNodeObject, self).mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """
        Emit a signal.
        """
        super(NUiNodeObject, self).mouseDoubleClickEvent(event)
        self.scene().parent().sg_NodeDoubleClicked.emit(self)

    def mouseMoveEvent(self, event):
        """
        .
        """
        if self.scene().views()[0].gridVisToggle:
            if self.scene().views()[0].gridSnapToggle or self.scene().views()[0]._nodeSnap:
                gridSize = self.scene().gridSize

                currentPos = self.mapToScene(QtCore.QPoint(event.pos().x() - self.baseWidth / 2,
                                             event.pos().y() - self.height / 2))

                snap_x = (round(currentPos.x() / gridSize) * gridSize) - gridSize / 4
                snap_y = (round(currentPos.y() / gridSize) * gridSize) - gridSize / 4
                snap_pos = QtCore.QPointF(snap_x, snap_y)
                self.setPos(snap_pos)

                self.scene().updateScene()
            else:
                self.scene().updateScene()
                super(NUiNodeObject, self).mouseMoveEvent(event)

        self.scene().signal_NodeMoved.emit(self.name, event.pos())
        # self.sg_Moved.emit(self, event.pos())

    def mouseReleaseEvent(self, event):
        """
        .
        """
        # Emit node moved signal.
        self.scene().signal_NodeMoved.emit(self.name, self.pos())
        super(NUiNodeObject, self).mouseReleaseEvent(event)

    def hoverLeaveEvent(self, event):
        """
        .
        """
        nodzInst = self.scene().views()[0]

        for item in nodzInst.scene().items():
            if isinstance(item, NConnection):
                item.setZValue(0)

        super(NUiNodeObject, self).hoverLeaveEvent(event)

    def node(self):
        return self._wrappedNode


class NVisualAttribute(NObject):
    """
    Represents an attribute with either an input, an output, or both. This class holds hard references to these and is only used
    in UI mode.
    """
    def __init__(self, owningObj, name, dataType, inPlug=None, inSocket=None, **extraData):
        super(NVisualAttribute, self).__init__(name=name, owner=owningObj, noClassRegister=True)

        self._plug = inPlug
        self._socket = inSocket
        self._data = extraData
        self._dataType = dataType

    def getPlug(self):
        """
        Get a weak reference to the plug object. Can be None.
        :return: A Weak Reference to the plug, or None if non existent.
        """
        return Core.NWeakRef(self._plug) if self._plug else None

    def getSocket(self):
        """
        Get a weak reference to the socket object. Can be None.
        :return: A Weak Reference to the socket, or None if non existent.
        """
        return Core.NWeakRef(self._socket) if self._socket else None

    def getExtraData(self):
        """
        Get extra info about this attribute, if any.
        :return: Return a dict with the extra info about the attribute. It can be empty and depends on the attribute being read.
        """
        return self._data

    def hasPlug(self):
        return self._plug is not None

    def hasSocket(self):
        return self._socket is not None

    def dataType(self):
        return self._dataType

    def __jsonSerialize__(self, Serial: dict):
        inConnections = []
        outConnections = []
        Serial['name'] = self.getName().toString()
        Serial['owningNode'] = self.getOwner().getName().toString()

        if self._plug:
            for c in self._plug.connections:
                if all(map(lambda x: x.isValid(), c.funcConnections)):
                    data = {}
                    c.__jsonSerialize__(data)
                    outConnections.append(data)
        if self._socket:
            for c in self._socket.connections:
                if all(map(lambda x: x.isValid(), c.funcConnections)):
                    data = {}
                    c.__jsonSerialize__(data)
                    inConnections.append(data)

        Serial['inConnections'] = inConnections
        Serial['outConnections'] = outConnections


class SlotItem(QtWidgets.QGraphicsItem):

    """
    The base class for graphics item representing attributes hook.
    """

    def __init__(self, parent, attribute, preset, index, dataType, maxConnections):
        """
        Initialize the class.
        :param parent: The parent item of the slot.
        :type  parent: QtWidgets.QGraphicsItem instance.
        :param attribute: The attribute associated to the slot.
        :type  attribute: String.
        :param index: int.
        :type  index: The index of the attribute in the node.
        :type  preset: str.
        :param preset: The name of graphical preset in the config file.
        :param dataType: The data type associated to the attribute.
        :type  dataType: Type.
        """
        super(SlotItem, self).__init__(parent)

        assert isinstance(parent, NUiNodeObject), "ASSERTION FAILURE: isinstance(parent, NUiNodeObject) == True"

        # Status.
        self.setAcceptHoverEvents(True)

        # Storage.
        self.slotType = None
        self.attribute = attribute
        self.preset = preset
        self.index = index
        self.dataType = dataType
        self.owner = parent

        # Style.
        self.brush = QtGui.QBrush()
        self.brush.setStyle(QtCore.Qt.SolidPattern)

        self.pen = QtGui.QPen()
        self.pen.setStyle(QtCore.Qt.SolidLine)

        # Connections storage.
        self.connected_slots = list()
        self.newConnection = None
        self.connections = list()
        self.maxConnections = maxConnections

    def accepts(self, slot_item: QtWidgets.QGraphicsItem):
        """
        Only accepts plug items that belong to other nodes, and only if the max connections count is not reached yet.
        """
        # no plug on plug or socket on socket
        hasPlugItem = isinstance(self, PlugItem) or isinstance(slot_item, PlugItem)
        hasSocketItem = isinstance(self, SocketItem) or isinstance(slot_item, SocketItem)
        if not (hasPlugItem and hasSocketItem):
            return False

        # no self connection
        if self.parentItem() == slot_item.parentItem():
            return False

        # no more than maxConnections
        if len(self.connected_slots) >= self.maxConnections and self.maxConnections > 0:
            return False

        # no connection with different types unless marked as NVariant or being Attr Ref and iterable
        if slot_item.dataType != self.dataType \
                and self.dataType != EDataType.DT_Variant \
                and slot_item.dataType != EDataType.DT_Variant\
                and (slot_item.dataType != EDataType.DT_AttrRef and self.dataType != EDataType.DT_Iterable):
            return False

        # otherwise, all fine.
        return True

    def mousePressEvent(self, event):
        """
        Start the connection process.
        """
        if event.button() == QtCore.Qt.LeftButton:
            self.newConnection = NConnection(self.center(),
                                                self.mapToScene(event.pos()),
                                                self,
                                                None)

            # self.parent().sg_Moved.connect(self.newConnection.onConnectedNodeMove)
            self.connections.append(self.newConnection)
            self.scene().addItem(self.newConnection)

            nodzInst = self.scene().views()[0]
            nodzInst.drawingConnection = True
            nodzInst.sourceSlot = self
            nodzInst.currentDataType = self.dataType
        else:
            super(SlotItem, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Update the new connection's end point position.
        """
        nodzInst = self.scene().views()[0]
        # config = nodzInst.config
        if nodzInst.drawingConnection:
            mbb = UCoreUtils.createPointerBoundingBox(pointerPos=event.scenePos().toPoint(),
                                                  bbSize=10)

            # Get nodes in pointer's bounding box.
            targets = self.scene().items(mbb)

            if any(isinstance(target, NUiNodeObject) for target in targets):
                if self.parentItem() not in targets:
                    for target in targets:
                        if isinstance(target, NUiNodeObject):
                            nodzInst.currentHoveredNode = target
            else:
                nodzInst.currentHoveredNode = None

            # Set connection's end point.
            self.newConnection.target_point = self.mapToScene(event.pos())
            self.newConnection.updatePath()
        else:
            super(SlotItem, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Apply the connection if target_slot is valid.
        """
        nodzInst = self.scene().views()[0]
        if event.button() == QtCore.Qt.LeftButton:
            nodzInst.drawingConnection = False
            nodzInst.currentDataType = None

            target = self.scene().itemAt(event.scenePos().toPoint(), QtGui.QTransform())

            if not isinstance(target, SlotItem):
                self.newConnection.remove()
                super(SlotItem, self).mouseReleaseEvent(event)
                return

            if target.accepts(self):
                self.newConnection.target = target
                self.newConnection.source = self
                self.newConnection.target_point = target.center()
                self.newConnection.source_point = self.center()

                # Perform the ui Connection.
                self.connect(target, self.newConnection)
                target.connect(self, self.newConnection)

                # Perform the logical connection. #LOGICAL_CONNECTION
                from_, to = (self, target) if self.slotType == 'plug' else (target, self)
                node = from_.owner.node()
                prop = getattr(node, from_.attribute)
                if callable(prop):
                    attr = getattr(prop, EXPOSEDPROPNAME, None); attrDetails = getattr(prop, EXPOSED_EXTRADATA, None)
                    assert attr and attrDetails
                    if 1:  # attrDetails['dataType'] == EDataType.DT_Delegate:
                        delegate = node.__PropHooks__.get(prop.__name__, None)
                        assert delegate, "Delegate for %s.%s not registered." % (node.getName(), self.attribute)

                        bm = delegate.bindFunction(to.owner.node(), to.attribute)
                        if bm:
                            self.newConnection.funcConnections.append(Core.NWeakRef(bm))
                            print("Successfully created connection {0} to {1}:".format(*self.newConnection.outputConnectionData()))
                        else:
                            print("can't connect to that..")
                            self.newConnection.remove()
                            # @TODO make it so that the delegate hook is automatically created. For now it needs to be predefined in the owning class.



                elif isinstance(prop, Core.NDynamicAttr):
                    bml = prop.connect(to.owner.node(), to.attribute)
                    print(bml)
                    if len(bml) != 0:
                        self.newConnection.funcConnections.extend([Core.NWeakRef(x) for x in bml])
                        print("Successfully created connection {0} to {1}:".format(*self.newConnection.outputConnectionData()))
                    else:
                        print("can't connect to that..")
                        self.newConnection.remove()

                else:
                    self.newConnection.remove()


                self.newConnection.updatePath()
            else:
                self.newConnection.remove()
        else:
            super(SlotItem, self).mouseReleaseEvent(event)

        nodzInst.currentHoveredNode = None

    def shape(self):
        """
        The shape of the Slot is a circle.
        """
        path = QtGui.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def paint(self, painter, option, widget=None):
        """
        Paint the Slot.
        """
        painter.setBrush(self.brush)
        painter.setPen(self.pen)

        nodzInst = self.scene().views()[0]
        # config = nodzInst.config
        if nodzInst.drawingConnection:
            if self.parentItem() == nodzInst.currentHoveredNode:
                painter.setBrush(QtGui.QColor(0, 0, 175)) # @TODO Add from config here too. Currently blue thing
                if self.slotType == nodzInst.sourceSlot.slotType or (self.slotType != nodzInst.sourceSlot.slotType and
                                                                     not self.accepts(nodzInst.sourceSlot)):
                    painter.setBrush(QtGui.QColor(128, 36, 36)) # not good
                else:
                    _penValid = QtGui.QPen()
                    _penValid.setStyle(QtCore.Qt.SolidLine)
                    _penValid.setWidth(2)
                    _penValid.setColor(QtGui.QColor(255, 255, 255, 255))
                    painter.setPen(_penValid)
                    painter.setBrush(self.brush)

        painter.drawEllipse(self.boundingRect())

    def center(self):
        """
        Return The center of the Slot.
        """
        rect = self.boundingRect()
        center = QtCore.QPointF(rect.x() + rect.width() * 0.5,
                                rect.y() + rect.height() * 0.5)

        return self.mapToScene(center)

    def connect(self, other, connection):
        pass

    def disconnect(self, connection=None):
        pass


class PlugItem(SlotItem):

    """
    A graphics item representing an attribute out hook.
    """

    def __init__(self, parent, attribute, index, preset, dataType, maxConnections):
        """
        Initialize the class.
        :param parent: The parent item of the slot.
        :type  parent: QtWidgets.QGraphicsItem instance.
        :param attribute: The attribute associated to the slot.
        :type  attribute: String.
        :param index: int.
        :type  index: The index of the attribute in the node.
        :type  preset: str.
        :param preset: The name of graphical preset in the config file.
        :param dataType: The data type associated to the attribute.
        :type  dataType: Type.
        """
        super(PlugItem, self).__init__(parent, attribute, preset, index, dataType, maxConnections)

        # Storage.
        self.attribute = attribute
        self.preset = preset
        self.slotType = 'plug'

        # Methods.
        self._createStyle(parent)

    def _createStyle(self, parent):
        """
        Read the attribute style from the configuration file.
        """
        # config = parent.scene().views()[0].config
        self.brush = QtGui.QBrush()
        self.brush.setStyle(QtCore.Qt.SolidPattern)
        self.brush.setColor(QtGui.QColor(*DATATYPES[self.dataType]))

    def boundingRect(self):
        """
        The bounding rect based on the width and height variables.
        """
        if self.parentItem():
            width = height = self.parentItem().attrHeight / 2.0

            if not self.scene():
                return QtCore.QRect(0,0,0,0)

            nodzInst = self.scene().views()[0]
            # config = nodzInst.config

            x = self.parentItem().baseWidth - (width / 2.0)
            y = (self.parentItem().baseHeight - 10 +  # @TODO Add config for radius, currently '10'
                 self.parentItem().attrHeight / 4 +
                 self.parentItem().attrs.index(self.attribute) * self.parentItem().attrHeight)

            rect = QtCore.QRectF(QtCore.QRect(x, y, width, height))
            return rect

        return QtCore.QRectF()

    def connect(self, socket_item, connection):
        """
        Connect to the given socket_item.
        <plug> -> <socket>
        """
        if self.maxConnections != -1 and len(self.connected_slots) >= self.maxConnections:
            # Already connected.
            self.connections[self.maxConnections - 1].remove()

        # Populate connection.
        connection.socketItem = socket_item
        connection.plugNode = self.parentItem().name
        connection.plugAttr = self.attribute

        # Add socket to connected slots.
        if socket_item in self.connected_slots:
            self.connected_slots.remove(socket_item)
        self.connected_slots.append(socket_item)

        # Add connection.
        if connection not in self.connections:
            self.connections.append(connection)
            # @TODO Make use of weak references here instead of hard references. There is a memory leak issue due to this when destroying connections.

        # Emit signal.
        # nodzInst = self.scene().views()[0]
        # nodzInst.signal_PlugConnected.emit(connection.plugNode, connection.plugAttr, connection.socketNode, connection.socketAttr)

    def disconnect(self, connection=None):
        """
        Disconnect the given connection from this plug item.
        """
        # Emit signal.
        # nodzInst = self.scene().views()[0]
        # nodzInst.signal_PlugDisconnected.emit(connection.plugNode, connection.plugAttr, connection.socketNode, connection.socketAttr)

        # Remove connected socket from plug
        if connection is not None:
            if connection.socketItem in self.connected_slots:
                self.connected_slots.remove(connection.socketItem)
            # Remove connection
            for cwf in connection.funcConnections:
                if cwf.isValid():
                    cwf().kill()

            connection.funcConnections = []

            self.connections.remove(connection)
            self.scene().removeItem(connection)
            print('PLUG: removing connection %s' % str(connection))
        else:
            scene = self.scene()
            for c in self.connections:
                if c in self.connected_slots:
                    self.connected_slots.remove(c.socketItem)

                for cwf in c.funcConnections:
                    if cwf.isValid():
                        cwf().kill()

                scene.removeItem(c)

            self.connections.clear()


class SocketItem(SlotItem):

    """
    A graphics item representing an attribute in hook.
    """

    def __init__(self, parent, attribute, index, preset, dataType, maxConnections):
        """
        Initialize the socket.
        :param parent: The parent item of the slot.
        :type  parent: QtWidgets.QGraphicsItem instance.
        :param attribute: The attribute associated to the slot.
        :type  attribute: String.
        :param index: int.
        :type  index: The index of the attribute in the node.
        :type  preset: str.
        :param preset: The name of graphical preset in the config file.
        :param dataType: The data type associated to the attribute.
        :type  dataType: Type.
        """
        super(SocketItem, self).__init__(parent, attribute, preset, index, dataType, maxConnections)

        # Storage.
        self.attributte = attribute
        self.preset = preset
        self.slotType = 'socket'

        # Methods.
        self._createStyle(parent)

    def _createStyle(self, parent):
        """
        Read the attribute style from the configuration file.
        """
        # config = parent.scene().views()[0].config
        self.brush = QtGui.QBrush()
        self.brush.setStyle(QtCore.Qt.SolidPattern)
        self.brush.setColor(QtGui.QColor(*DATATYPES[self.dataType]))

    def boundingRect(self):
        """
        The bounding rect based on the width and height variables.
        """
        width = height = self.parentItem().attrHeight / 2.0

        nodzInst = self.scene().views()[0]
        # config = nodzInst.config

        x = - width / 2.0
        y = (self.parentItem().baseHeight - 10 + # @TODO Add node radius here, currently '10'
            (self.parentItem().attrHeight/4) +
             self.parentItem().attrs.index(self.attribute) * self.parentItem().attrHeight )

        rect = QtCore.QRectF(QtCore.QRect(x, y, width, height))
        return rect

    def connect(self, plug_item, connection):
        """
        Connect to the given plug item.
        """
        print(self.connections)
        if self.maxConnections != -1 and len(self.connected_slots) >= self.maxConnections:
            # Already connected.
            self.connections[self.maxConnections-1].remove()
            # last.plugItem.disconnect(last)


        # Populate connection.
        connection.plugItem = plug_item
        connection.socketNode = self.parentItem().name
        connection.socketAttr = self.attribute

        # Add plug to connected slots.
        self.connected_slots.append(plug_item)

        # Add connection.
        if connection not in self.connections:
            self.connections.append(connection)
            # @TODO Make use of weak references here instead of hard references. There is a memory leak issue due to this when destroying connections.

        # Emit signal.
        # nodzInst = self.scene().views()[0]
        # nodzInst.signal_SocketConnected.emit(connection.plugNode, connection.plugAttr, connection.socketNode, connection.socketAttr)

    def disconnect(self, connection=None):
        """
        Disconnect the given connection from this socket item.
        """
        # Emit signal.
        # nodzInst = self.scene().views()[0]
        # nodzInst.signal_SocketDisconnected.emit(connection.plugNode, connection.plugAttr, connection.socketNode, connection.socketAttr)

        # Remove connected plugs
        if connection is not None:
            if connection.plugItem in self.connected_slots:
                self.connected_slots.remove(connection.plugItem)
            # Remove connections
            for cwf in connection.funcConnections:
                if cwf.isValid():
                    cwf().kill()

            self.connections.remove(connection)
            self.scene().removeItem(connection)
            print('SOCKET: removing connection %s' % str(connection))

        else:
            scene = self.scene()
            for c in self.connections:
                if c in self.connected_slots:
                    self.connected_slots.remove(c.socketItem)

                for cwf in c.funcConnections:
                    if cwf.isValid():
                        cwf().kill()

                scene.removeItem(c)

            self.connections.clear()


class NConnection(QtWidgets.QGraphicsPathItem):

    """
    A graphics path representing a connection between two attributes.
    """

    def __init__(self, source_point, target_point, source, target):
        """
        Initialize the class.
        :param source_point: Source position of the connection.
        :type  source_point: QPoint.
        :param target_point: Target position of the connection
        :type  target_point: QPoint.
        :param source: Source item (plug or socket).
        :type  source: class instance.
        :param target: Target item (plug or socket).
        :type  target: class instance.
        """
        super(NConnection, self).__init__()

        self.setZValue(1)

        # Storage.
        self.socketNode = None
        self.socketAttr = None
        self.plugNode = None
        self.plugAttr = None

        self.funcConnections = []

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
        Apply style from plug/socket data.
        """
        self.setAcceptHoverEvents(True)
        self.setZValue(-1)

        self._pen = QtGui.QPen(self.source.brush.color())
        self._pen.setWidth(5)  # @TODO Add connection radius from config here. currently '5'

    def outputConnectionData(self):
        """
        .
        """
        return ("{0}.{1}".format(self.plugNode, self.plugAttr),
                "{0}.{1}".format(self.socketNode, self.socketAttr))

    def __jsonSerialize__(self, Serial: dict):
        Serial['plugNodeName'] = self.plugNode if self.plugNode else 0
        Serial['plugNodeUID'] = g_a.getInstanceByName(self.plugNode).getUUID().toString() if self.plugNode else 0
        Serial['plugAttr'] = self.plugAttr

        Serial['socketNodeName'] = self.socketNode
        Serial['socketNodeUID'] = g_a.getInstanceByName(self.socketNode).getUUID().toString() if self.socketNode else 0
        Serial['socketAttr'] = self.socketAttr

        Serial['src_pos'] = (self.source_point.x(), self.source_point.y())
        Serial['tgt_pos'] = (self.target_point.x(), self.target_point.y())

    def __jsonReader__(self, myDict: dict):
        raise RuntimeError('__jsonReader__ on %s should not be called.' % self.__class__.__name__)

    def mousePressEvent(self, event):
        """
        Snap the Connection to the mouse.
        """
        nodzInst = self.scene().views()[0]

        for item in nodzInst.scene().items():
            if isinstance(item, NConnection):
                item.setZValue(0)

        nodzInst.drawingConnection = True

        d_to_target = (event.pos() - self.target_point).manhattanLength()
        d_to_source = (event.pos() - self.source_point).manhattanLength()
        if d_to_target < d_to_source:
            self.target_point = event.pos()
            self.movable_point = 'target_point'
            self.target.disconnect(self)
            self.target = None
            nodzInst.sourceSlot = self.source
        else:
            self.source_point = event.pos()
            self.movable_point = 'source_point'
            self.source.disconnect(self)
            self.source = None
            nodzInst.sourceSlot = self.target

        self.updatePath()

    def mouseMoveEvent(self, event):
        """
        Move the Connection with the mouse.
        """
        nodzInst = self.scene().views()[0]
        # config = nodzInst.config

        mbb = UCoreUtils.createPointerBoundingBox(pointerPos=event.scenePos().toPoint(),
                                              bbSize=20)

        # Get nodes in pointer's bounding box.
        targets = self.scene().items(mbb)

        if any(isinstance(target, NUiNodeObject) for target in targets):

            if nodzInst.sourceSlot.parentItem() not in targets:
                for target in targets:
                    if isinstance(target, NUiNodeObject):
                        nodzInst.currentHoveredNode = target
        else:
            nodzInst.currentHoveredNode = None

        if self.movable_point == 'target_point':
            self.target_point = event.pos()
        else:
            self.source_point = event.pos()

        self.updatePath()

    def mouseReleaseEvent(self, event):
        """
        Create a Connection if possible, otherwise delete it.
        """
        nodzInst = self.scene().views()[0]
        nodzInst.drawingConnection = False

        slot = self.scene().itemAt(event.scenePos().toPoint(), QtGui.QTransform())

        if not isinstance(slot, SlotItem):
            self.remove()
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
                self.remove()

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
                self.remove()

    def remove(self):
        """
        Remove this Connection from the scene.
        """
        print('removing %s' % str(self))
        if self.source is not None:
            self.source.disconnect(self)
        if self.target is not None:
            self.target.disconnect(self)

        scene = self.scene()
        # scene.removeItem(self)
        if scene:
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
