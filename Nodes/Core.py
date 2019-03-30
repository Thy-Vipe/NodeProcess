import uuid
import multiprocessing, sys, os

class NObject(object):
    """
        This is the root object for all node-based logic in this software. It holds a few functions that serve as the base
        for every other NObject subclass. It is made of overridable functions that are expected to be used everywhere in many different instances.
        Every NObject has a 64-bit UUID that is used to have every object be "unique".
    """
    def __init__(self, name="", inOwner=None):
        self.__uuid = uuid.uuid4()
        self.__name = name
        self._owner = inOwner

    def getUUID(self):
        return self.__uuid

    def setUUID(self, inUUID):
        self.__uuid = inUUID

    def getName(self):
        return self.__name

    def setName(self, inName):
        self.__name = inName

    def getOwner(self):
        """
        Get the object that owns this, if defined. Can be None.
        :return: The object owning this object.
        """
        return self._owner

    def serialize(self, InArchive):
        """
        Automatically serializes any property that is marked as serializable using the 'SP_' tag at the start of the property name.
        Any property marked as serializable must hold an object that overrides the 'serialize(NArchive*)' command, or the property will be ignored.
        :param InArchive: The archive to use for serialization.
        :return: Nothing. The passed-in NArchive is filled with data from this.
        """
        for prop in dir(self):
            if prop.startswith("SP_", 0, 3):
                try:
                    InArchive << getattr(self, prop)
                except TypeError:
                    print(Warning("%s.%s is not serializable." % (self.__name__, prop)))


    def __str__(self):
        return "%s.%s" % (self.__name__, self.__name)


class NMain(NObject):
    """
        This is the main object that is ultimately the base of every logic going on in this software.
        It runs independently from the Ui parts of the code, and handles the logical side of it.
    """
    def __init__(self):
        super(NMain, self).__init__("Main")
        self.CPU_COUNT = multiprocessing.cpu_count()
        # Can be defined when the window is spawned.
        self._WindowReference = None
        self._graphReference = None

    def getInterfaceRef(self):
        """
        Get the main window reference.
        :return: A reference to the main window instance. It can be None if the program is running with no gui.
        """
        return self._WindowReference

    def getGraphRef(self):
        """
        Get the graph, which should be nested in the main window.
        :return: A reference to the graph instance. It can be None.
        """
        return self._graphReference

    def _setGraph(self, InObj):
        """
        Should be called in child classes. Pass the reference of the graph.
        :param InObj: The graph reference.
        """
        self._graphReference = InObj

    def spawnInterface(self):
        """
        Is expected to be overriden in subclasses.
        """
        pass

