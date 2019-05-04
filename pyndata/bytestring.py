from __future__ import absolute_import

import sys

from .error import error
from .field import Field
from .variablelength import VariableLength

class bytestring(VariableLength, Field):
    '''Like :class:`array`, but unpacked as a python string of arbitrary data.

    Parameters:
        length: see :class:`VariableLength` for ways to specify the length of
            the array.

    '''
    def __init__(self, length):
        super(bytestring, self).__init__()
        self.length = length
        self.default = b''

    if sys.version_info[0] == 3:
        def pack(self, value, struct):
            return bytes(value)
    else:
        def pack(self, value, struct):
            return value

    def unpack(self, reader, struct):
        l = self.get_length(struct)
        data = reader.read(l)
        if len(data) != l:
            raise error("Not enough bytes, field {} expected {}, got {} (struct was: {})".format(
                    self.name, l, repr(data), struct
                )
            )
        else:
            return data
