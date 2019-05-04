import pytest

import pyndata

class BytestringTests(pyndata.Struct):
    str1 = pyndata.bytestring(4)

def test_bytestring():
    t = BytestringTests()
    t.str1 = b'asdf'
    assert t.str1 == b'asdf'
    assert t.pack() == b'asdf'

class VariableBytestring(pyndata.Struct):
	l = pyndata.uint8()
	s = pyndata.bytestring(length=l)

def test_variable_unpack():
	v = VariableBytestring()
	v.unpack(b'\x04asdf')
	assert v.l == 4
	assert v.s == b'asdf'

def test_variable_pack():
    v = VariableBytestring()
    v.s = b'asdf'
    assert v.l == 4
    assert v.pack() == b'\x04asdf'

def test_bad_unpack_length():
    v = VariableBytestring()
    with pytest.raises(pyndata.error):
        v.unpack(b'\x05a')
