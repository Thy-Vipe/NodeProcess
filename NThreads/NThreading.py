from Delegates import InternalDelegates as NDel
from Nodes.Core import NObject
from threading import Thread


class NThread(Thread, NObject):
    def __init__(self, threadName, owner=None):
        Thread.__init__(self)
        NObject.__init__(self, threadName, owner)
        self.__dispatchedTicks = NDel.Delegate("%s_Delegate" % threadName, self)

    def run(self):
        self.__dispatchedTicks.fire()

    def addTask(self, objRef, funcName=""):
        self.__dispatchedTicks.bindFunction(objRef, funcName)

    def removeTask(self, objRef, funcName=""):
        self.__dispatchedTicks.removeFunction(objRef, funcName)