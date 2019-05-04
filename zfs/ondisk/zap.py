import enum
from pyndata import Struct, uint64, padding, uint32, uint16, nullstring, BitField


class ZapType(enum.Enum):
    ZAPLeaf = (1 << 63)
    ZAPHeader = (1 << 63) + 1
    MicroZAP = (1 << 63) + 3


class MicroZAPHeader(Struct):
    __ENDIAN__ = 'little'

    block_type = uint64(enum=ZapType)
    salt = uint64()
    flags = uint64()
    _pad = padding(length=5 * 8)


class MicroZAPCommon(Struct):
    __ENDIAN__ = 'little'

    _pad = uint16()
    collision = uint32()
    name = nullstring(padded=True, max_length=50)


class MicroZAP(Struct):
    __ENDIAN__ = 'little'

    value = uint64()
    hdr = MicroZAPCommon()


class SARegistrationMicroZAP(Struct):
    __ENDIAN__ = 'little'

    _value = uint64()
    attr_num = BitField(_value, 8, 0)
    byteswap = BitField(_value, 8, 16)
    length = BitField(_value, 16, 24)
    hdr = MicroZAPCommon()
