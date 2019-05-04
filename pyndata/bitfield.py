from __future__ import absolute_import

from .field import __nextfield__

class BitField(object):
    '''Represents a bitfield on an :class:`integer` field.
    If shift is unspecified, it will be set to the sum of the sizes of the
    previously defined bitfields attached to the same field.

    Parameters:
        field (Field): The Field being masked.
        size (int): The size of the bitfield, in bits.

    Keyword Arguments:
        shift (int): If provided, overrides the default computation of where
            the bitfield starts, forcing it to exactly ``shift`` bits.
            BitFields with explicit shifts will not affect the position of any
            automatically positioned BitFields.
        enum (enum.Enum): If set, attempts to convert values to members of the
            enum before returning them.

    '''
    default = 0
    __SHOW__ = True
    def __init__(self, field, size, shift=None, enum=None):
        if shift == None:
            shift = field.current_offset
            field.current_offset += size
        self.__index__ = __nextfield__()
        self.field = field
        self.mask = ((1 << size)-1) << shift
        self.shift = shift
        self.enum = enum

    def __get__(self, obj, kind=None):
        value = self.field.__get__(obj)
        value = (value & self.mask) >> self.shift
        try:
            return self.enum(value)
        except:
            return value

    def __set__(self, obj, value):
        value = int(value)
        result = self.field.__get__(obj) & ((~self.mask)&((1<<64)-1))
        result |= ((value << self.shift) & self.mask)
        self.field.__set__(obj, result)
