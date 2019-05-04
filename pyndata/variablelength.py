from __future__ import absolute_import

from .field import Field
from .bitfield import BitField

class VariableLength(object):
    '''Mixin class for fields with dynamic length.
    Length can be an :class:`int`, an instance of a :class:`Field` or
    :class:`BitField`, or a function
    with the signature f(struct, length=None)
    '''
    def get_length(self, struct):
        if isinstance(self.length, (Field, BitField)):
            return self.length.__get__(struct)
        elif callable(self.length):
            return self.length(struct)
        else:
            return self.length

    def __set__(self, obj, value):
        super(VariableLength, self).__set__(obj, value)
        if isinstance(self.length, (Field, BitField)):
            return self.length.__set__(obj, len(value))
        elif callable(self.length):
            return self.length(obj, len(value))
