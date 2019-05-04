import types
import global_accessor as g_a

#  ========================================== Class generators / Macros ==========================================


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


def NATTR(ClassObj, PropName, *args: AttrType, DESC: str = '', UPDATEHOOK=None, pos: int = 100):
    """
    Add extra data for a given property of a given class instance.
    :param ClassObj: The class instance reference.
    :param PropName: The property name. It must match the one declared within the class.
    :param args: Attribute types <EAttrType> to add info about what can be done with a given property.
    :param DESC: A description for this attribute. It is not required.
    :param UPDATEHOOK: A function with no parameters that can be called when the value of this attribute is changed from the Ui.
    :type UPDATEHOOK: Method or Function hard reference.
    :param pos: The position in which to display this attribute. (from top to bottom), with -1 being a normal add regardless of the order.
    :type pos: int.
    """
    if hasattr(ClassObj, '__PropFlags__'):
        data = list(args)
        data.insert(0, DESC)
        if UPDATEHOOK:
            assert isinstance(UPDATEHOOK, (types.MethodType, types.FunctionType))

        data.insert(1, UPDATEHOOK)
        data.insert(2, pos)
        ClassObj.__PropFlags__[PropName] = tuple(data)
    else:
        raise AttributeError("%s does not use the generator macro CLASS_BODY()." % ClassObj.__class__.__name__)


def HASHOOK(ClassObj, PropName):
    if hasattr(ClassObj, '__PropFlags__'):
        return ClassObj.__PropFlags__.get(PropName, (None, None))[1] is not None
    else:
        raise AttributeError("%s does not use the generator macro CLASS_BODY()." % ClassObj.__class__.__name__)


def GET_ATTRHOOK(ClassObj, PropName):
    if hasattr(ClassObj, '__PropFlags__'):
        return ClassObj.__PropFlags__.get(PropName, (None, None))[1]
    else:
        raise AttributeError("%s does not use the generator macro CLASS_BODY()." % ClassObj.__class__.__name__)


def RNATTR(ClassObj, PropName):
    if hasattr(ClassObj, '__PropFlags__'):
        del ClassObj.__PropFlags__[PropName]
    else:
        raise AttributeError("%s does not use the generator macro CLASS_BODY()." % ClassObj.__class__.__name__)


def DYNATTR(ClassObj, PropName, cls, *args, **kwargs):
    v = cls(*args, **kwargs)
    setattr(ClassObj, PropName, v)


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
    AT_Persistent = 'persistent'
    AT_Serializable = 'serializable'
    AT_ReadOnly = 'readOnly'
    AT_WriteOnly = 'writeOnly'
    AT_ReadWrite = 'readWrite'
    AT_MulticastDelegate = 'MCDelegate'
    AT_SingleCastDelegate = 'SCDelegate'
    AT_Getter = 'getter'
    AT_kSlot = 'kSlot'
    AT_Blacklisted = 'blacklist'


class EPropType:
    PT_Input = 'input'
    PT_Output = 'ouput'
    PT_FuncDelegateIn = 'delegateIn'
    PT_FuncDelegateOut = 'delegateOut'
    PT_Readable = 'readable'
    PT_Internal = 'internal'


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
    DT_Iterable = 0x4974657261626c65
    DT_Bool = 0x426f6f6c
    DT_AttrRef = 0x41747472526566
    DT_Enum = 0x456e756d


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
        if kwargs.get('pos', False) is False:
            kwargs['pos'] = 100

        func.extra_data = kwargs
        func.propertyDelegate = None  # Can be used when dynamically connected, by spawning a dynamic delegate and referencing it here.
        return func

    return register_wrapper


def ExposedMethod(funcType, **kwargs):
    """
    Decorator for methods that do not use logic from a complex node. Use this if you wish to expose Methods or Functions to the Visual Scripting.
    """

    def register_wrapper(func):
        func.__VisibleFunc__ = kwargs.get('visible', True)
        func.__returnValues__ = kwargs
        func.__mode__ = funcType
        return func

    return register_wrapper


#  ========================================== Logic Macros ==========================================


def IsDynamicMethod(func):
    return hasattr(func, '__VisibleFunc__') and hasattr(func, '__mode__') and hasattr(func, '__returnValues__')