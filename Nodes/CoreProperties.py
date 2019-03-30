
class NArchive(object):
    def __init__(self):
        super(NArchive, self).__init__(self)
        self.__dataBinary = []

    def addData(self, binary):
        pass


class NString(str):
    """
    Extension of class "str" with more methods used for NodeProcess.
    """
    def __new__(cls, content):
        return str.__new__(cls, content)

    def __lshift__(self, other):
        if isinstance(other, NArchive):
            other.addData(self.encode())

    def __rshift__(self, other):
        raise ArithmeticError("Wrong operand order for serialization.")

    @staticmethod
    def fromString(inString):
        """
        Casts a string/stringifiable object into NString.
        :param inString: The string to cast from
        :return: The new NString.
        """
        return NString(str(inString))

