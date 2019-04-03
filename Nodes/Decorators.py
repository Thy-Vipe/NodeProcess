import modulefinder, warnings
import global_accessor as g_a
import os, sys

#  ========================================== Class generators ==========================================


def CLASS_BODY(ClassObj, **kwargs):
    setattr(ClassObj, '__PropFlags__', {})
    g_a.addToGlobal(ClassObj.__class__.__name__, ClassObj.__class__)


def CLASS_REGISTER(ClassObj, **kwargs):
    if not kwargs.get('noReferencing', False):
        g_a.addInstance(ClassObj)


def CLASS_PROP_BODY(ClassObj):
    g_a.addToGlobal(ClassObj.__class__.__name__, ClassObj.__class__)


def NATTR(ClassObj, PropName, *args):
    if hasattr(ClassObj, '__PropFlags__'):
        ClassObj.__PropFlags__[PropName] = args
    else:
        raise AttributeError("%s does not use the generator macro CLASS_BODY()." % ClassObj.__class__.__name__)


#  ========================================== Function decorators ==========================================

class EAttrType:
    AT_Transient = -1
    AT_Serializable = 0
    AT_ReadOnly = 1
    AT_ReadWrite = 2
    AT_MulticastDelegate = 3
    AT_SingleCastDelegate = 4
    AT_Getter = 5


class EPropType:
    PT_Input = 0
    PT_Output = 1
    PT_FuncDelegateIn = 2
    PT_FuncDelegateOut = 3
    PT_Readable = 4


def Property(*PropTypes, **kwargs):
    def register_wrapper(func):
        Values = list(PropTypes)
        Values.append(EPropType.PT_Readable)
        func.propTypes = tuple(Values)
        func.extra_data = kwargs
        return func

    return register_wrapper

