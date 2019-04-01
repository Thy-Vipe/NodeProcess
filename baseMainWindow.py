# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Programming\NodeProcess\baseMainWindow.ui',
# licensing of 'D:\Programming\NodeProcess\baseMainWindow.ui' applies.
#
# Created: Mon Apr  1 13:00:45 2019
#      by: pyside2-uic  running on PySide2 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1118, 676)
        MainWindow.setAutoFillBackground(False)
        MainWindow.setStyleSheet("QMainWindow {\n"
"    background-color: rgb(77, 82, 90);\n"
"    border: 1px solid black;\n"
"}\n"
"QMainWindow::separator {\n"
"    background: blue;\n"
"    width: 10px;\n"
"    height: 10px; \n"
"}\n"
"QWidget {\n"
"    background-color: rgb(77, 82, 90);\n"
"}\n"
"QLabel {\n"
"    font: 10pt \"MS Shell Dlg 2\";\n"
"    color: #fff;\n"
"}\n"
"QMenuBar {\n"
"    color: #fff\n"
"}\n"
"\n"
"")
        MainWindow.setDocumentMode(False)
        MainWindow.setDockNestingEnabled(False)
        MainWindow.setUnifiedTitleAndToolBarOnMac(False)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.widget = QtWidgets.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(0, 0, 271, 641))
        self.widget.setObjectName("widget")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.widget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(0, 0, 271, 631))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.outlinerFrame = QtWidgets.QFrame(self.verticalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.outlinerFrame.sizePolicy().hasHeightForWidth())
        self.outlinerFrame.setSizePolicy(sizePolicy)
        self.outlinerFrame.setMinimumSize(QtCore.QSize(28, 30))
        self.outlinerFrame.setBaseSize(QtCore.QSize(0, 0))
        self.outlinerFrame.setAutoFillBackground(False)
        self.outlinerFrame.setStyleSheet("background-color:rgb(46, 49, 54)")
        self.outlinerFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.outlinerFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.outlinerFrame.setObjectName("outlinerFrame")
        self.horizontalLayoutWidget = QtWidgets.QWidget(self.outlinerFrame)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(0, 0, 271, 31))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.OutlinerTopLayt = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.OutlinerTopLayt.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.OutlinerTopLayt.setContentsMargins(0, 0, 0, 0)
        self.OutlinerTopLayt.setObjectName("OutlinerTopLayt")
        self.label = QtWidgets.QLabel(self.horizontalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label.setAutoFillBackground(False)
        self.label.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.OutlinerTopLayt.addWidget(self.label)
        self.verticalLayout.addWidget(self.outlinerFrame)
        self.listView = QtWidgets.QListView(self.verticalLayoutWidget)
        self.listView.setObjectName("listView")
        self.verticalLayout.addWidget(self.listView)
        self.graphicsView = QtWidgets.QGraphicsView(self.centralwidget)
        self.graphicsView.setGeometry(QtCore.QRect(270, 0, 841, 631))
        self.graphicsView.setStyleSheet("background-color: qradialgradient(spread:pad, cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 rgba(46, 49, 54, 255), stop:1 rgb(73, 78, 86));")
        self.graphicsView.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.graphicsView.setFrameShadow(QtWidgets.QFrame.Raised)
        self.graphicsView.setObjectName("graphicsView")
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setEnabled(False)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1118, 21))
        self.menubar.setObjectName("menubar")
        self.menuFIle = QtWidgets.QMenu(self.menubar)
        self.menuFIle.setObjectName("menuFIle")
        self.menuTools = QtWidgets.QMenu(self.menubar)
        self.menuTools.setObjectName("menuTools")
        MainWindow.setMenuBar(self.menubar)
        self.menubar.addAction(self.menuFIle.menuAction())
        self.menubar.addAction(self.menuTools.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "MainWindow", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("MainWindow", "Outliner", None, -1))
        self.menuFIle.setTitle(QtWidgets.QApplication.translate("MainWindow", "File", None, -1))
        self.menuTools.setTitle(QtWidgets.QApplication.translate("MainWindow", "Tools", None, -1))

