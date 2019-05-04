import pytest

import pyndata

class S(pyndata.Struct):
	a = pyndata.uint8()
	b = pyndata.uint8()
	c = pyndata.uint8()

def test_keyword_fields():
	x = S(a=1, b=2, c=3)
	assert x.a == 1
	assert x.b == 2
	assert x.c == 3

def test_keyword_failure():
	with pytest.raises(AttributeError):
		x = S(z=1)

