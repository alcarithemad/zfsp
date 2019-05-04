from __future__ import absolute_import

import sys

from .array import array
from .bitfield import BitField
from .bytestring import bytestring
from .error import error
from .field import __nextfield__
from .field import Field
from .integer import *
from .nullstring import nullstring
from .padding import padding
from .structfield import StructField
if sys.version_info[0] == 3:
    from .structure3 import Struct
else:
    from .structure import Struct
from .variablelength import VariableLength

__all__ = [
    '__nextfield__',
    'array',
    'BitField',
    'bytestring',
    'error',
    'Field',
    'integer',
    'nullstring',
    'padding',
    'Struct',
    'StructField',
    'VariableLength'
] + [
    'int8',
    'int16',
    'int32',
    'int64',
    'uint8',
    'uint16',
    'uint32',
    'uint64'
]

for name in __all__:
    o = globals()[name]
    if isinstance(o, type):
        o.__module__ = 'pyndata'

