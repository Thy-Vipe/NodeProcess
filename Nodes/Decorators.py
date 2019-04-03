from Nodes.CoreProperties import *
import os, sys

# ========================================== Class generators ==========================================

def CLASS_BODY(ClassObj):
    setattr(ClassObj, '__PropFlags__', {})


def NATTR(ClassObj, PropName, *args):
    if hasattr(ClassObj, '__PropFlags__'):
        ClassObj.__PropFlags__[PropName] = args
    else:
        raise AttributeError("%s does not use the generator macro CLASS_BODY()." % ClassObj.__class__.__name__)


# ========================================== Function decorators ==========================================

def Property(*PropTypes, **kwargs):
    def register_wrapper(func):
        Values = list(PropTypes)
        Values.append(EPropType.PT_Readable)
        func.propTypes = tuple(Values)
        func.extra_data = kwargs
        return func

    return register_wrapper