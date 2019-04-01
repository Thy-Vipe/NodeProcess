# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Programming\NodeProcess\baseMainWindow.ui',
# licensing of 'D:\Programming\NodeProcess\baseMainWindow.ui' applies.
#
# Created: Mon Apr  1 13:00:45 2019
#      by: pyside2-uic  running on PySide2 5.12.2
#


from PySide2 import QtCore, QtGui, QtWidgets
import os, sys

# Get the local path to add to sys.path to properly load custom modules.
if __name__ == "__main__":
    lp = __file__.rsplit("/", 2)[0]; sys.path.extend([lp, lp.replace("/", "\\")]); del lp

from Windows import CoreNWindows





class MainWindowBuild(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1118, 676)
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
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.OutlinerTopLayt.addWidget(self.label)
        self.verticalLayout.addWidget(self.outlinerFrame)
        self.listView = QtWidgets.QListView(self.verticalLayoutWidget)
        self.listView.setObjectName("listView")
        self.verticalLayout.addWidget(self.listView)
        self.graphicsView = CoreNWindows.NGraphicsView(self.centralwidget)
        self.graphicsView.setGeometry(QtCore.QRect(270, 0, 841, 631))
        self.graphicsView.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.graphicsView.setFrameShadow(QtWidgets.QFrame.Raised)
        self.graphicsView.setStyleSheet("background-color: #373b44;")
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

        with open("%s\\mainwindow.qss" % (os.path.dirname(os.path.realpath(__file__))), "r") as f:
            MainWindow.setStyleSheet(f.read())

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "MainWindow", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("MainWindow", "Outliner", None, -1))
        self.menuFIle.setTitle(QtWidgets.QApplication.translate("MainWindow", "File", None, -1))
        self.menuTools.setTitle(QtWidgets.QApplication.translate("MainWindow", "Tools", None, -1))

