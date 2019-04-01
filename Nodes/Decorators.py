from Nodes.CoreProperties import *


def Property(*PropTypes):
    def register_wrapper(func):
        Values = list(PropTypes)
        Values.append(EPropType.PT_Readable)
        func.propTypes = tuple(Values)
        return func

    return register_wrapper
