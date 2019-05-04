import pytest

import pyndata

class S(pyndata.Struct):
    _a = pyndata.uint8()
    b = pyndata.uint8()
    c = pyndata.BitField(b, 1)
    _d = pyndata.BitField(b, 1)

def test_default_hidden():
    x = S()
    a = repr(x)
    assert a == "S(b=0, c=0)"
