"""
Defines the common data structures.
"""

def Struct(name, bases, attrs):
    """
    This class allows data to be defined purely declaratively, since classes 
    which this class as their metaclass will have initializers generated for 
    them.

    For example, the following creates a class where the only required argument
    is ``first_name``.::

        >>> class Person(metaclass=Struct):
        ...     __slots__ = 'first_name', 'last_name', 'age', 'gender'
        ...     __defaults__ = { 'last_name': None, 'age': None, 
        ...                     'gender': None }

    Now, the Person class can be instantiated in a variety of ways.::

        >>> tim = Person(first_name='Tim', last_name='the Enchanger', gender='male')
        >>> artuhr = Person(first_name='Arthur', age=35, gender='male')
        
    Take, for example, the Person ``tim`` - is has the following attributes:

    - ``first_name = "Tim"``
    - ``last_name = "The Enchanter"``
    - ``age = None``
    - ``gender = "male"``
    """
    slots = attrs['__slots__']

    if '__defaults__' in attrs:
        defaults = attrs['__defaults__']
        def class_init(self, **kwargs):
            """
            Initializer which takes defaults into account.

            Attributes not in __defaults__ but which are in __slots__ must
            be passed in as a keyword argument. Arguments that are in
            __defaults__ can be overridden.
            """
            # First, find any extra keys which aren't declared
            slot_set = set(slots)
            key_set = set(kwargs.keys())
            if not key_set.issubset(slot_set):
                raise TypeError('Extra keyword parameters given which are not '
                        'declared in __slots__')

            for key in slots:
                if key in kwargs:
                    setattr(self, key, kwargs[key])
                else:
                    try:
                        setattr(self, key, defaults[key])
                    except KeyError:
                        raise TypeError(
                            'Argument not given for {}, '
                            'but no default provided'.format(key))
    else:
        def class_init(self, *args):
            """
            Initializer which doesn't have any __defaults__.

            All arguments provided in __slots__ must be provided in the
            arguments.
            """
            if len(args) != len(slots):
                raise TypeError('{} arguments required'.format(len(args)))
            for name, arg in zip(slots, args):
                setattr(self, name, arg)

    attrs['__init__'] = class_init
    return type(name, bases, attrs)

class Icon(metaclass=Struct):
    """
    The data used to draw icons for hidden windows.

    .. py:attribute win

        The window which the icon is drawn on.

    .. py:attribute gc

        The graphics context which belongs to the icon.

    .. py:attribute pixmap

        The application icon which can be shown on the icon window.

    .. py:attribute pix_width

        The width of :attr:`pix_width`.

    .. py:attribute pix_height

        The height of :attr:`pix_height`.
    """
    __slots__ = 'win', 'gc', 'pixmap', 'pix_width', 'pix_height'
