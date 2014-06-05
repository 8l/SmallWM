"""
A place where the common data is defined.
"""
def Struct(name, bases, attrs):
    """
    Creates a structure, which is read-write.
    """
    slots = attrs['__slots__']

    if '__defaults__' in attrs:
        defaults = attrs['__defaults__']
        def class_init(self, **kwargs):
            for key in slots:
                if key in kwargs:
                    setattr(self, key, kwargs[key])
                else:
                    try:
                        setattr(self, key, defaults[key])
                    except KeyError:
                        raise TypeError(
                            'Argument not given for {}, but no default provided'.format(key))
    else:
        def class_init(self, *args):
            if len(args) != len(slots):
                raise TypeError('{} arguments required'.format(len(args)))
            for name, arg in zip(slots, args):
                setattr(self, name, arg)

    attrs['__init__'] = class_init
    return type(name, bases, attrs)

class Icon(metaclass=Struct):
    """
    The data used to draw icons for hidden windows.
    """
    __slots__ = 'win', 'gc', 'pixmap', 'width', 'height'

class ClientData(metaclass=Struct):
    """
    The data which is managed for each individual client.
    """
    __slots__ = 'is_sticky', 'desktop', 'layer', 'icon', 'move_resize'
    __defaults__ = {'is_sticky': False, 'icon': None, 'move_resize': None}

class WMState(metaclass=Struct):
    """
    The state of the window manager related to X.
    """
    __slots__ = 'display', 'screen', 'root', 'current_desktop', 'screen_width', 'screen_height'

class WMConfig(metaclass=Struct):
    """
    Configuration options given by the configuration file.
    """
    __slots__ = ('shell', 'key_commands', 'command_keys', 'max_desktops', 
        'icon_width', 'icon_height', 'border_width', 'class_actions', 'show_pixmaps'

class WM(metaclass=Struct):
    """
    The top-level state object which stores most of the other Struct-style types.
    """
    __slots__ = 'wm_state', 'wm_config', 'client_data'
    __defaults__ = {'client_data': {}}
