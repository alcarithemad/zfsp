import sys

import pytest

import pyndata

class NullStringTests(pyndata.Struct):
    str1 = pyndata.nullstring(max_length=4)
    str2 = pyndata.nullstring(max_length=4, padded=True)
    str3 = pyndata.nullstring(max_length=4, allow_max=True)

def test_null_string_pack():
    x = NullStringTests()
    packed = x.pack()
    assert packed == b'\0\0\0\0\0\0'

def test_null_string_illegal():
    x = NullStringTests()
    x.str1 = 'asdf'
    with pytest.raises(ValueError):
        x.pack()

def test_null_string_illegal_allow_max():
    x = NullStringTests()
    x.str3 = 'asdfg'
    with pytest.raises(ValueError):
        x.pack()

def test_null_string_unpack():
    x = NullStringTests()
    x.unpack(b'asd\x00as\x00\x001234')
    assert x.str1 == 'asd'
    assert x.str2 == 'as'
    assert x.str3 == '1234'

class NullEncodingTests(pyndata.Struct):
    s1 = pyndata.nullstring(max_length=4, encoding='utf-8')
    b1 = pyndata.nullstring(max_length=4, encoding=None)

def test_null_string_encoding():
    x = NullEncodingTests()
    x.s1 = 'asd'
    x.b1 = b'xyz'
    assert x.pack() == b'asd\0xyz\0'
    x2 = NullEncodingTests(x.pack())
    print(type(x2.s1))
    if sys.version_info[0] == 3:
        strtype = str
        bytestype = bytes
    else:
        strtype = unicode
        bytestype = str
    assert isinstance(x2.s1, strtype)
    assert isinstance(x2.b1, bytestype)

