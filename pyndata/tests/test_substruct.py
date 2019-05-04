import pyndata

class SubStruct(pyndata.Struct):
    x = pyndata.uint8()

class StructWithSubStruct(pyndata.Struct):
    s1 = SubStruct()
    s2 = SubStruct()
    _s3 = SubStruct()

def test_sub_struct_unpack():
    t = StructWithSubStruct(b'\x01\x23\x45')
    assert t.s1.x == 0x01
    assert t.s2.x == 0x23
    assert t._s3.x == 0x45

def test_sub_struct_pack():
    t = StructWithSubStruct()
    t.s1.x = 0x20
    t.s2.x = 0x44
    t._s3.x = 0x59
    packed = t.pack()
    assert packed == b'\x20\x44\x59'
