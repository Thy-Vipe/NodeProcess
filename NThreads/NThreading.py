from Delegates import InternalDelegates as NDel
from Nodes.Core import NObject, NScript
import threading


class NThread(threading.Thread, NObject):
    def __init__(self, threadName, owner=None, bDestroyAfterWork=False):
        threading.Thread.__init__(self)
        NObject.__init__(self, name=threadName, owner=owner)
        self.__dispatchedTicks = NDel.Delegate("%s_Delegate" % threadName, self)
        self.__workDone = NDel.DelegateMulticast('%s_DoneWorking' % threadName, self)
        self._globalData = {}
        self.script_to_run = None
        self.aliveStatus = True
        self.threadSpawnedFrom = threading.get_ident()
        self.bShouldDestroyOnceDone = bDestroyAfterWork

    def run(self):
        assert threading.get_ident() != self.threadSpawnedFrom, "ASSERTION ERROR: Thread was not started properly. currentThread != thisThread"
        print("Starting thread. ID: %s" % threading.get_ident())
        r = 0
        if self.script_to_run:
            r = self.script_to_run.exec(bFromThread=True)

            if self.bShouldDestroyOnceDone:
                self.kill()

        else:
            while self.aliveStatus:
                self.__dispatchedTicks.execute()

        self.__workDone.execute(r)

    def addTask(self, objRef, funcName=""):
        self.__dispatchedTicks.bindFunction(objRef, funcName)

    def asyncTask(self, code: NScript):
        self.script_to_run = code

    def removeTask(self, objRef, funcName=""):
        self.__dispatchedTicks.removeFunction(objRef, funcName)

    def kill(self):
        self.aliveStatus = False

    def bindFinishedEvent(self, obj: object, func: str):
        self.__workDone.bindFunction(obj, func)

    def removeFinishedEvent(self, obj: object, func: str):
        self.__workDone.removeFunction(obj, func)