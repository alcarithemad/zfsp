from __future__ import absolute_import

from .field import Field
from .structure import Struct
from .structfield import StructField

class ConditionalField(Field):
    def __init__(self, func, real_field):
        super(ConditionalField, self).__init__()

        if issubclass(type(real_field), Struct):
            real_field = StructField(real_field)

        self.func = func
        self.real_field = real_field
        self.default = real_field.default

    def pack(self, value, struct):
        if self.func(struct):
            return self.real_field.pack(value, struct)
        else:
            return b''

    def unpack(self, reader, struct):
        if self.func(struct):
            return self.real_field.unpack(reader, struct)
        else:
            return self.default

def conditional(field):
    def wrapper(f):
        cf = ConditionalField(f, field)
        return cf
    return wrapper
