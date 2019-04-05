from Delegates import InternalDelegates as NDel
from Nodes.Core import NObject, NScript
import threading


class NThread(threading.Thread, NObject):
    def __init__(self, threadName, owner=None):
        threading.Thread.__init__(self)
        NObject.__init__(self, name=threadName, owner=owner)
        self.__dispatchedTicks = NDel.Delegate("%s_Delegate" % threadName, self)
        self._globalData = {}
        self.script_to_run = None
        self.aliveStatus = True
        self.threadSpawnedFrom = threading.get_ident()

    def run(self):
        assert threading.get_ident() != self.threadSpawnedFrom, "ASSERTION ERROR: Thread was not started properly. currentThread != thisThread"
        print("Starting thread. ID: %s" % threading.get_ident())
        if self.script_to_run:
            self.script_to_run.exec()
        else:
            while self.aliveStatus:
                self.__dispatchedTicks.execute()

    def addTask(self, objRef, funcName=""):
        self.__dispatchedTicks.bindFunction(objRef, funcName)

    def asyncTask(self, code: NScript):
        self.script_to_run = code

    def removeTask(self, objRef, funcName=""):
        self.__dispatchedTicks.removeFunction(objRef, funcName)

    def kill(self):
        self.aliveStatus = False