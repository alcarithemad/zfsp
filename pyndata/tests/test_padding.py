import pyndata

class padded(pyndata.Struct):
    f = pyndata.uint8(default=0xff)
    pad = pyndata.padding(3)

def test_padding_unpack():
    x = padded()
    x.pad = b'\x01\x02\x03'
    assert x.pack() == b'\xff\x01\x02\x03'

def test_padding_pack():
    x = padded()
    x.unpack(b'\x20\x01\x02\x03')
    assert x.pad == b'\x01\x02\x03'
