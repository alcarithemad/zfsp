from __future__ import absolute_import

import struct
import sys

if sys.version_info[0] == 3:
    xrange = range

from .field import Field
from .error import error
from .integer import integer
from .structure import Struct
from .structure import StructField
from .variablelength import VariableLength

class array(VariableLength, Field):
    '''An array of ``kind`` elements of fixed or variable length.
    
    Parameters:
        kind (Field): a :class:`Field` or :class:`Struct` to be repeated.
        length: see :class:`VariableLength` for ways to specify the length of the array.

    ::

        class S(pyndata.Struct):
            l1 = pyndata.uint8()
            # an array of 0-255 uint32 values.
            a1 = pyndata.array(pyndata.uint32(), l1)

    '''
    def __init__(self, kind, length):
        super(array, self).__init__()
        
        if issubclass(type(kind), Struct):
            kind = StructField(kind)
        self.kind = kind

        self.length = length

        self.default = []

    def pack(self, values, _struct):
        return b''.join(self.kind.pack(item, _struct) for item in values)

    def unpack(self, reader, _struct):
        out = []
        for x in xrange(self.get_length(_struct)):
            out.append(self.kind.unpack(reader, _struct))
        return out
