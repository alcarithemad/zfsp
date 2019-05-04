from __future__ import absolute_import

import copy
import sys

if sys.version_info[0] == 3:
    from io import BytesIO as StringIO
else:
    try: from cStringIO import StringIO
    except: from StringIO import StringIO

from .bitfield import BitField
from .field import __nextfield__
from .field import Field
from .structfield import StructField

# This is a little strange, so it deserves an explanation.
# In StructMeta down below, we need to check if the newly created class is
# a Struct, but the real Struct class doesn't exist yet, and won't exist
# when it's being run through the __new__ method.
#
# Instead, we "forward declare" Struct here a la C, then inherit from this
# Struct in the real Struct class below. If it helps, mentally replace every
# "Struct" before "class Struct(object" (and the on in the base classes there)
# with "FirstStruct".
class Struct(object):
    pass

class StructMeta(type):
    '''Makes an ordered list of fields from a class definition.
    '''
    def __new__(cls, cls_name, bases, attrs):
        fields = []
        bitfields = []
        field_defaults = {}
        for name, field in attrs.items():
            if isinstance(field, Struct):
                field = StructField(field)
                attrs[name] = field
            if isinstance(field, Field):
                field.name = name
                if name[0] == '_':
                    field.__SHOW__ = False
                field_defaults[name] = field.default
                fields.append(field)
            elif isinstance(field, BitField):
                field.name = name
                if name[0] == '_':
                    field.__SHOW__ = False
                bitfields.append(field)
        fields.sort(key=lambda x:x.__index__)
        new_cls = type.__new__(cls, cls_name, bases, attrs)
        new_cls.field_defaults = field_defaults
        new_cls.fields = fields
        new_cls.bitfields = bitfields
        return new_cls

class Struct(Struct):
    ''':class:`Struct` is where the magic happens.

    All :class:`Field` and :class:`BitField` objects set as class attributes
    on a class which subclasses :class:`Struct` will automagically be used in
    definition order to :meth:`pack` or :meth:`unpack`.

    '''
    __metaclass__ = StructMeta
    __ENDIAN__ = 'little'

    def __init__(self, initial=None, **kwargs):
        self.__index__ = __nextfield__()
        if initial:
            self.field_items = {}
        else:
            self.field_items = copy.deepcopy(self.field_defaults)
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise AttributeError("struct {} has no attribute {}".format(self.__class__.__name__, k))
        if initial:
            self.unpack(initial)

    def __repr__(self):
        fields = [field.name+'='+repr(getattr(self, field.name)) for field in self.fields if field.__SHOW__]
        fields.extend(field.name+'='+repr(field.__get__(self)) for field in self.bitfields if field.__SHOW__)
        ret = '{0}({1})'.format(type(self).__name__, ', '.join(fields))
        return ret

    def pack(self):
        '''pack packs all Fields in the struct using their :meth:`Field.pack` methods, in
        order, and returns the resulting :class:`str`.
        '''
        out = []
        for field in self.fields:
            out.append(field.pack(field.__get__(self), self))
        return b''.join(out)

    def unpack(self, reader):
        '''unpack takes a :class:`str` or a file-like object and calls the unpack method
        of each Field in the struct in order.
        '''
        if isinstance(reader, (str, bytes)):
            reader = StringIO(reader)
        for field in self.fields:
            setattr(self, field.name, field.unpack(reader, self))
