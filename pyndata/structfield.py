from __future__ import absolute_import

from .field import Field

class StructField(Field):
    '''Wrapper to make Struct act like a Field. Shouldn't be called directly,
    unless you're building a custom Field type that needs to embed another
    Field.
    '''

    def __init__(self, struct):
        self.__DEFAULT__ = struct
        super(StructField, self).__init__()
        self.__index__ = struct.__index__
        self.struct = type(struct)

    def pack(self, value, struct):
        return value.pack()

    def unpack(self, reader, struct):
        return self.struct(reader)
