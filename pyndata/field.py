from __future__ import absolute_import

import itertools
import sys

# The basic premise of this whole pile of magic is right here.
# When we __init__ a field we grab a unique index value for it
# we use __nextfield__ for that: it's a little odd, but it's just
# a reference to an otherwise anonymous itertools.count(). This
# would probably be more idiomatic as a class with a __call__, though.

if sys.version_info[0] == 3:
    __nextfield__ = itertools.count().__next__
else:
    __nextfield__ = itertools.count().next

class Field(object):
    '''Parent class of all fields used in :class:`Struct` .
    Subclass this and implement :meth:`pack` and :meth:`unpack` with your
    desired field behaviour.
    If you override :meth:`__init__`, be sure to call Field's version.

    Keyword Arguments:
        default: The default value for this field.
    
    '''
    __DEFAULT__ = None
    __SHOW__ = True

    def __init__(self, default=None):
        self.default = default or self.__DEFAULT__
        self.__index__ = __nextfield__()
        self.name = None

    def __get__(self, obj, kind=None):
        return obj.field_items[self.name]

    def __set__(self, obj, value):
        obj.field_items[self.name] = value

    def pack(self, value, struct):
        '''Pack a value into a string.

        Parameters:
            value: The value to be packed.
            struct (Struct): The Struct this value is being packed for.
        
        Returns:
            str: The packed value.
        '''
        raise NotImplementedError

    def unpack(self, reader, struct):
        '''Unpack a value from a string.

        Parameters:
            reader: A file-like object to read the data from.
            struct (Struct): The Struct this value is being packed for.
        
        Returns:
            The unpacked value.
        
        '''
        raise NotImplementedError
