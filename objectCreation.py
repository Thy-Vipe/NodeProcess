# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Programming\NodeProcess\objectCreation.ui',
# licensing of 'D:\Programming\NodeProcess\objectCreation.ui' applies.
#
# Created: Thu Apr  4 14:28:45 2019
#      by: pyside2-uic  running on PySide2 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Object_spawner(object):
    def setupUi(self, Object_spawner):
        Object_spawner.setObjectName("Object_spawner")
        Object_spawner.setWindowModality(QtCore.Qt.ApplicationModal)
        Object_spawner.resize(383, 318)
        Object_spawner.setAutoFillBackground(False)
        Object_spawner.setStyleSheet("background-color: rgba(46, 49, 54, 90);\nborder-radius: 5px;")
        Object_spawner.setInputMethodHints(QtCore.Qt.ImhNone)
        self.verticalLayoutWidget = QtWidgets.QWidget(Object_spawner)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(0, 0, 381, 321))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.textEdit = QtWidgets.QTextEdit(self.verticalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.textEdit.sizePolicy().hasHeightForWidth())
        self.textEdit.setSizePolicy(sizePolicy)
        self.textEdit.setMinimumSize(QtCore.QSize(0, 17))
        self.textEdit.setMaximumSize(QtCore.QSize(16777215, 30))
        self.textEdit.setStyleSheet("background-color: rgb(128, 128, 135);\n")
        self.textEdit.setFrameShape(QtWidgets.QFrame.Box)
        self.textEdit.setFrameShadow(QtWidgets.QFrame.Raised)
        self.textEdit.setLineWidth(1)
        self.textEdit.setMidLineWidth(1)
        self.textEdit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit.setTabStopWidth(20)
        self.textEdit.setPlaceholderText("")
        self.textEdit.setObjectName("textEdit")
        self.verticalLayout.addWidget(self.textEdit)
        self.listWidget = QtWidgets.QListWidget(self.verticalLayoutWidget)
        self.listWidget.setFrameShape(QtWidgets.QFrame.Box)
        self.listWidget.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout.addWidget(self.listWidget)



