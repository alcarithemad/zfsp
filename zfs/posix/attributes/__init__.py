import logging

import enum
import pyndata

logger = logging.getLogger(__name__)


class PosixType(enum.Enum):
    FIFO = 1
    CHARACTER = 2
    DIRECTORY = 4
    BLOCK = 6
    REGULAR_FILE = 8
    SYMLINK = 10
    SOCKET = 12
    DOOR = 13
    PORT = 14


class Mode(pyndata.Struct):
    __ENDIAN__ = 'little'
    mode = pyndata.uint64()
    perms = pyndata.BitField(mode, 10)
    unknown = pyndata.BitField(mode, 2)
    file_type = pyndata.BitField(mode, 4, enum=PosixType)


class Timestamp(pyndata.Struct):
    __ENDIAN__ = 'little'
    seconds = pyndata.uint64()
    nanoseconds = pyndata.uint64()


class ZNodeACE(pyndata.Struct):
    who = pyndata.uint32()
    access_mask = pyndata.uint32()
    flags = pyndata.uint16()
    type = pyndata.uint16()


class ZNodeACL(pyndata.Struct):
    external_object = pyndata.uint64()
    count = pyndata.uint32()
    version = pyndata.uint16()
    _padding = pyndata.padding(length=2)
    aces = pyndata.array(ZNodeACE, length=count)


class DefaultAttrsV1(pyndata.Struct):
    __ENDIAN__ = 'little'
    ZPL_ATIME = Timestamp()
    ZPL_MTIME = Timestamp()
    ZPL_CTIME = Timestamp()
    ZPL_CRTIME = Timestamp()
    ZPL_GEN = pyndata.uint64()
    ZPL_MODE = Mode()
    ZPL_SIZE = pyndata.uint64()
    ZPL_PARENT = pyndata.uint64()
    ZPL_LINKS = pyndata.uint64()
    ZPL_XATTR = pyndata.uint64()
    ZPL_RDEV = pyndata.uint64()
    ZPL_FLAGS = pyndata.uint64()
    ZPL_UID = pyndata.uint64()
    ZPL_GID = pyndata.uint64()
    padding = pyndata.array(pyndata.uint64(), length=4)
    acl = ZNodeACL()


def FixedAttributes(data):
    attrs = DefaultAttrsV1(data)
    return attrs.field_items


def POSIXAttrs_for(dataset):
    if dataset.pool.version >= 24:
        return SystemAttributes(dataset)
    else:
        return FixedAttributes


from .systemattributes import SystemAttributes
