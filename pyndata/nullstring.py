from __future__ import absolute_import

import sys

from .error import error
from .field import Field

class nullstring(Field):
    '''A null-terminated string.

    Parameters:
        max_length (int): the maximum number this string may contain.

    Keyword Arguments:
        padded (bool): always read ``max_length`` bytes, discarding everything
            after the first null byte.
        allow_max (bool): allows the field to read exactly ``max_length``
            bytes with no null terminator.
        encoding (str): converts the string to this encoding before packing or
            unpacking. If set to ``None``, only packs and unpacks
            :class:`bytes`. Defaults to ``'utf-8'``.
    '''
    def __init__(self, max_length, padded=False, allow_max=False, encoding='utf-8'):
        super(nullstring, self).__init__()
        self.max_length = max_length
        self.padded = padded
        self.default = b''
        self.allow_max = allow_max
        self.encoding = encoding

    def pack(self, value, struct):
        if isinstance(value, str):
            print(self.encoding, type(value), value)
            if self.encoding:
                value = value.encode(self.encoding)
            elif sys.version_info[0] == 2:
                pass
            else:
                raise error
        if self.allow_max:
            if len(value) > self.max_length:
                raise ValueError("String length {} exceeds this field's maximum length {}".format(len(value), self.max_length))
        else:
            if len(value) >= self.max_length:
                raise ValueError("String length {} exceeds this field's maximum length {}".format(len(value), self.max_length))
        value = (value+b'\0')[:self.max_length]
        if self.padded:
            pad = self.max_length - len(value)
            value += b'\0'*pad
        return value

    def unpack(self, reader, struct):
        if self.padded:
            value = reader.read(self.max_length)
        else:
            value = [b'']
            i = 0
            m = self.max_length + (1 if self.allow_max else 0)
            while value[-1] != '\0' and i < m:
                value.append(reader.read(1))
                i += 1
            value = b''.join(value)
            print(value)
        value = value.rstrip(b'\0')
        if self.encoding:
            value = value.decode(self.encoding)
        return value
