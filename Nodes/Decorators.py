import modulefinder, warnings
import global_accessor as g_a
from Nodes.CoreUtils import *

#  ========================================== Class generators ==========================================

class AttrType:
    """
    Dummy for visibility
    """
    pass


def CLASS_BODY(ClassObj, **kwargs):
    setattr(ClassObj, '__PropFlags__', {})
    setattr(ClassObj, '__PropHooks__', {})
    setattr(ClassObj, '__PropGetters__', {})
    g_a.addToGlobal(ClassObj.__class__.__name__, ClassObj.__class__)


def CLASS_REGISTER(ClassObj, **kwargs):
    if not kwargs.get('noReferencing', False):
        g_a.addInstance(ClassObj)


def CLASS_PROP_BODY(ClassObj):
    g_a.addToGlobal(ClassObj.__class__.__name__, ClassObj.__class__)


def NATTR(ClassObj, PropName, *args: AttrType):
    if hasattr(ClassObj, '__PropFlags__'):
        ClassObj.__PropFlags__[PropName] = args
    else:
        raise AttributeError("%s does not use the generator macro CLASS_BODY()." % ClassObj.__class__.__name__)


def REGISTER_HOOK(ClassObj, PropName, hook):
    """
    Bind a delegate (hook) to a property. Will raise an error if the class it is being used on does not use CLASS_BODY()
    :param ClassObj: The class instance.
    :param PropName: The property name.
    :param hook: The delegate to bind.
    """
    if hasattr(ClassObj, '__PropHooks__'):
        ClassObj.__PropHooks__[PropName] = hook
    else:
        raise AttributeError("%s does not use the generator macro CLASS_BODY()." % ClassObj.__class__.__name__)


def REGISTER_GETTER(ClassObj, PropName: str, Getter: classmethod):
    """
    Bind a getter for a function that sets values. Can be used to recover previously set data.
    :param ClassObj: The owning class
    :param PropName: the owning property to bind a getter to
    :param Getter:  the property to read value from.
    :type Getter: method or classmethod
    """
    if hasattr(ClassObj, '__PropGetters__'):
        ClassObj.__PropGetters__[PropName] = Getter
    else:
        raise AttributeError("%s does not use the generator macro CLASS_BODY()." % ClassObj.__class__.__name__)


def GET_GETTER(ClassObj, PropName):
    if hasattr(ClassObj, '__PropGetters__'):
        return ClassObj.__PropGetters__.get(PropName, None)
    else:
        raise AttributeError("%s does not use the generator macro CLASS_BODY()." % ClassObj.__class__.__name__)


def GET_HOOK(ClassObj, PropName: str):
    if hasattr(ClassObj, '__PropHooks__'):
        return ClassObj.__PropHooks__[PropName]
    else:
        raise AttributeError("%s does not use the generator macro CLASS_BODY()." % ClassObj.__class__.__name__)

#  ========================================== Function decorators ==========================================


class EAttrType:
    AT_Persistent = -1
    AT_Serializable = 0
    AT_ReadOnly = 1
    AT_WriteOnly = 2
    AT_ReadWrite = 3
    AT_MulticastDelegate = 4
    AT_SingleCastDelegate = 5
    AT_Getter = 6
    AT_kSlot = 7
    AT_Blacklisted = 8


class EPropType:
    PT_Input = 0
    PT_Output = 1
    PT_FuncDelegateIn = 2
    PT_FuncDelegateOut = 3
    PT_Readable = 4


class EDataType:
    DT_Delegate = 0x6b44656c6567617465
    DT_String = 0x4e537472696e67
    DT_Script = 0x4e536372697074
    DT_Array = 0x4e4172726179
    DT_Dict = 0x44696374
    DT_Float = 0x4e466c6f6174
    DT_Int = 0x4e496e74
    DT_Struct = 0x4e537472756374
    DT_Point = 0x4e506f696e74
    DT_Vector = 0x4e566563746f72
    DT_Variant = 0x4e56617269616e74


def Property(*PropTypes: EPropType, **kwargs):
    """
    Decorator for NProperties. Must be used for properties (methods) that are readable in visual scripting, in order
    to define the behavior to adopt to read / use these properties on the VS node.
    :param PropTypes: Must be value(s) from EPropType.
    :param kwargs: Extra keyword arguments.
    """
    def register_wrapper(func):
        Values = list(PropTypes)
        Values.append(EPropType.PT_Readable)
        func.propTypes = tuple(Values)
        func.extra_data = kwargs
        return func

    return register_wrapper

