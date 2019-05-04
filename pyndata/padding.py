from __future__ import absolute_import

from .field import Field

class padding(Field):
    '''Arbitrary data. For consistency, a struct which unpacks padding,
    then changes non-padding fields and repacks will use the same byte
    values as it originally read. Defaults to `length` null bytes.
    '''
    def __init__(self, length):
        super(padding, self).__init__()
        self.length = length
        self.default = b'\0'*length

    def pack(self, value, struct):
        return value+b'\0'*(self.length-len(value))

    def unpack(self, reader, struct):
        return reader.read(self.length)
