import pytest

import pyndata

class s(pyndata.Struct):
    first = pyndata.uint8()
    second = pyndata.uint8(default=5)

def test_field_get():
    x = s()
    assert x.first == 0

def test_default():
    x = s()
    assert x.second == 5

def test_field_set():
    x = s()
    x.first = 123
    assert x.first == 123

def test_unique_field_items():
    x = s()
    y = s()
    assert id(x.field_items) != id(y.field_items)

def test_pack():
    x = s()
    packed = x.pack()
    assert packed == b'\0\x05'

def test_initial_unpack():
    x = s(b'\x20\xff')
    assert x.first == 0x20
    assert x.second == 0xff

def test_unpack():
    x = s()
    x.unpack(b'\x31\xf0')
    assert x.first == 0x31
    assert x.second == 0xf0

class e(pyndata.Struct):
    __ENDIAN__ = 'big'

    normal = pyndata.uint16()
    little = pyndata.uint16(endian='little')
    big = pyndata.uint16(endian='big')

def test_endian():
    x = e()
    x.normal = 0xf010
    x.little = 0x1311
    x.big = 0xf3f2
    packed = x.pack()
    assert packed == b'\xf0\x10\x11\x13\xf3\xf2'

def test_field_raises():
    f = pyndata.Field()
    with pytest.raises(NotImplementedError):
        f.pack(None, None)

    with pytest.raises(NotImplementedError):
        f.unpack(None, None)
