from typing import Type
from typing import Union

from pyndata import BitField
from pyndata import Struct
from pyndata import array
from pyndata import bytestring
from pyndata import padding
from pyndata import uint16
from pyndata import uint64
from pyndata import uint8

from .. import constants
from . import fatzap


class dva(Struct):
    __ENDIAN__ = 'little'

    _first = uint64()
    vdev = BitField(_first, 32, 32)
    grid = BitField(_first, 8, 23)
    asize = BitField(_first, 24, 0)
    _offset = uint64()
    gang = BitField(_offset, 1, 63)
    offset = BitField(_offset, 63, 0)

    def __repr__(self):
        return '{}:{:X}:{:X}'.format(self.vdev, self.offset << 9, self.asize << 9)


class Blockptr(Struct):
    __ENDIAN__ = 'little'

    dvas = array(dva(), length=3)
    _prop = uint64()
    logical_size = BitField(_prop, 16, 0)
    physical_size = BitField(_prop, 16, 16)
    compression = BitField(_prop, 6, 32, enum=constants.Compression)
    encryption = BitField(_prop, 1, 38)
    embedded = BitField(_prop, 1, 39)
    checksum_type = BitField(_prop, 8, 40, enum=constants.Checksum)
    object_type = BitField(_prop, 8, 48, enum=constants.ObjectType)
    level = BitField(_prop, 5, 56)
    dedup = BitField(_prop, 1, 62)
    endian = BitField(_prop, 1, 63)

    pad = padding(length=16)
    phys_birth = uint64()
    birth = uint64()
    fill = uint64()
    checksum = array(uint64(), 4)

    def to_embedded(self):
        raw_blkptr = self.pack()
        return EmbeddedBlockptr(raw_blkptr)


class EmbeddedBlockptr(Struct):
    __ENDIAN__ = 'little'

    data1 = bytestring(length=6*8)
    _prop = uint64()
    logical_size = BitField(_prop, 25)
    physical_size = BitField(_prop, 7)
    compression = BitField(_prop, 7)
    embedded = BitField(_prop, 1)
    embedded_type = BitField(_prop, 8)
    type_ = BitField(_prop, 8)
    level = BitField(_prop, 5)
    encryption = BitField(_prop, 1)
    dedup = BitField(_prop, 1)
    endian = BitField(_prop, 1)
    data2 = bytestring(length=3*8)
    birth = uint64()
    data3 = bytestring(length=5*8)

    @property
    def data(self):
        data = self.data1 + self.data2 + self.data3
        assert len(data) == 112
        return data


class GangBlock(Struct):
    MAGIC = 0x210da7ab10c7a11
    blocks = array(Blockptr(), length=3)
    _pad = padding(length=88)
    magic = uint64()
    checksum = array(uint64(), 4)


class Uberblock(Struct):
    __ENDIAN__ = 'little'
    MAGIC = 0x00bab10c

    magic = uint64()
    version = uint64()
    txg = uint64()
    guid_sum = uint64()
    timestamp = uint64()
    root = Blockptr()
    software_version = uint64()

    def valid(self):
        if self.magic != self.MAGIC:
            return False
        if self.version > constants.POOL_VERSION:
            return False
        # TODO: validate checksums
        return True


class DNode(Struct):
    __ENDIAN__ = 'little'

    node_type = uint8(enum=constants.ObjectType)
    indirect_blockshift = uint8()
    indirect_levels = uint8()
    num_blockptrs = uint8()
    bonustype = uint8(enum=constants.ObjectType)
    checksum_type = uint8(enum=constants.Checksum)
    compression_type = uint8(enum=constants.Compression)
    _dnode_flags = uint8()  # TODO: dnode flag bitfields
    used_bytes = BitField(_dnode_flags, 1, 0)
    userused = BitField(_dnode_flags, 1, 1)
    spill_blkptr = BitField(_dnode_flags, 1, 3)
    data_sectors = uint16()
    bonuslen = uint16()
    _pad = padding(length=4)
    max_block_id = uint64()
    used = uint64()
    _pad2 = padding(length=4 * 8)
    blkptr = array(Blockptr(), length=num_blockptrs)

    def bonus_length(self, o=None):
        if self.bonuslen != 0 and self.node_type != constants.ObjectType.NONE:
            return self.bonuslen
        elif self.node_type == constants.ObjectType.NONE:
            return 320
        else:
            return self.bonuslen
    bonus = bytestring(length=bonus_length)  # TODO: finish
    _final_pad = padding(length=64)


class ZILHeader(Struct):
    claim_txg = uint64()
    replay_seq = uint64()
    log = Blockptr()
    claim_seq = uint64()
    _pad = padding(length=5 * 8)


class ZILRecord(Struct):
    tx_type = uint64(enum=constants.ZILTypes)
    length = uint64()
    txg = uint64()
    seq = uint64()


class ObjsetV1(Struct):
    __ENDIAN__ = 'little'

    meta_dnode = DNode()
    zil_header = ZILHeader()
    os_type = uint64(enum=constants.ObjectSetType)


Objset = ObjsetV1


class ObjsetV15(Struct):
    __ENDIAN__ = 'little'

    meta_dnode = DNode()
    zil_header = ZILHeader()
    os_type = uint64(enum=constants.ObjectSetType)
    os_flags = uint64()  # TODO: flag values
    _pad = padding(length=112)
    userused = DNode()
    groupused = DNode()


ObjectsetTypes = Union[Type[ObjsetV1], Type[ObjsetV15]]
Objectsets = Union[ObjsetV1, ObjsetV15]


def Objset_for(version) -> ObjectsetTypes:
    if version in range(1, 15):
        return ObjsetV1
    else:
        return ObjsetV15


indirect_cache = {}


def indirect(size=None, shift=None):
    size = (size * 512) or (1 << shift)
    count = int(size / 128)

    if size not in indirect_cache:

        class IndirectBlock(Struct):
            __ENDIAN__ = 'little'
            blocks = array(Blockptr(), length=count)

        IndirectBlock.__name__ = 'Indirect' + str(size)

        indirect_cache[size] = IndirectBlock

    return indirect_cache[size]


class DSLDir(Struct):
    __ENDIAN__ = 'little'

    creation_time = uint64()
    head_dataset = uint64()
    parent = uint64()
    clone_parent = uint64()
    child_dir_zap = uint64()
    used_bytes = uint64()
    compressed_bytes = uint64()
    uncompressed_bytes = uint64()
    quota = uint64()
    props_zap = uint64()
    _pad = padding(length=21 * 8)


class DSLDataset(Struct):
    __ENDIAN__ = 'little'

    dir = uint64()
    prev_snapshot = uint64()
    prev_snapshot_txg = uint64()
    next_snapshot = uint64()
    snapnames_zap = uint64()
    num_children = uint64()
    creation_time = uint64()
    creation_txg = uint64()
    deadlist = uint64()
    used_bytes = uint64()
    compressed_bytes = uint64()
    uncompressed_bytes = uint64()
    unique_bytes = uint64()
    fsid_guid = uint64()
    guid = uint64()
    flags = uint64()
    bp = Blockptr()
    _pad = padding(length=8 * 8)


class BPObjHeader(Struct):
    __ENDIAN__ = 'little'

    length = uint64()
    unknown = array(uint16(), length=20)

