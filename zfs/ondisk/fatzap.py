import enum
import logging
import struct

from typing import Any
from typing import Dict
from typing import List
from typing import Union

from collections import OrderedDict
from io import BytesIO
from pyndata import *

from .. import constants

logger = logging.getLogger(__name__)


class PointerTable(Struct):
    __ENDIAN__ = 'little'
    block = uint64()
    num_blocks = uint64()
    shift = uint64()
    next_block = uint64()
    blocks_copied = uint64()


class LeafHeader(Struct):
    __ENDIAN__ = 'little'
    header = uint64(enum=constants.ZapType)
    next = uint64()
    prefix = uint64()
    magic = uint64()
    num_free = uint16()
    n_entries = uint64()
    prefix_len = uint16()
    freelist = uint16()
    _padding = padding(length=2)


class FatZAPHeader(Struct):

    class MAGIC(enum.Enum):
        ZAP = 0x2F52AB2AB

    __ENDIAN__ = 'little'
    block_type = uint64(enum=constants.ZapType)
    magic = uint64(enum=MAGIC)
    ptr_info = PointerTable()
    first_free = uint64()
    num_leafs = uint64()
    num_entries = uint64()
    salt = uint64()


class LeafChunk(Struct):
    __ENDIAN__ = 'little'
    chunk_type = uint8()
    data = bytestring(length=23)


class LeafType(Struct):
    pass


class LeafEntry(LeafType):
    size = uint8()
    next = uint16()
    name_chunk = uint16()
    name_length = uint16()
    value_chunk = uint16()
    value_length = uint16()
    collision = uint16()
    padding = padding(length=2)
    hash = uint64()


class LeafArray(LeafType):
    data = bytestring(length=21)
    next = uint16()


class LeafFree(LeafType):
    _padding = bytestring(length=21)
    next = uint16()


CHUNK_TYPES = {
    251: LeafArray,
    252: LeafEntry,
    253: LeafFree,
}


def parse_chunk(chunk: Union[LeafChunk, BytesIO]) -> LeafType:
    if isinstance(chunk, BytesIO):
        ch = LeafChunk(chunk)
    else:
        ch = chunk
    return CHUNK_TYPES[ch.chunk_type](ch.data)


def parse_fatzap(data: bytes) -> Dict[str, Any]:
    reader = BytesIO(data)
    header = FatZAPHeader(reader)
    ret = OrderedDict()
    for i in range(header.num_leafs):
        i += 1
        reader.seek(8*2048*i)
        # created only to advance the reader
        _leaf_hdr = LeafHeader(reader)
        hashes = reader.read(1 << header.ptr_info.shift)

        chunks = []
        for x in range(638):
            try:
                c = parse_chunk(reader)
                chunks.append(c)
            except Exception:
                raise
        ret.update(reconstruct_data(chunks))
    return ret


def read_linked(chunks: List[LeafType], first: int) -> bytes:
    index = first
    out = []
    while index < 65535:
        try:
            c = chunks[index]
            out.append(c.data)
            index = c.next
        except Exception:
            raise
    return b''.join(out)


formats = {
    1: 'B',
    2: 'H',
    4: 'I',
    8: 'Q',
}


def reconstruct_data(chunks: List[LeafType]) -> Dict[str, Any]:
    items = OrderedDict()
    for entry in chunks:
        if isinstance(entry, LeafEntry):
            # we drop 1 extra byte because the length includes the NUL terminator
            key = read_linked(chunks, entry.name_chunk)[:entry.name_length-1]
            raw_value = read_linked(chunks, entry.value_chunk)[:entry.size * entry.value_length]
            if entry.size in formats:
                format_code = '>' + formats[entry.size] * entry.value_length
                value = struct.unpack(format_code, raw_value)
                if len(value) == 1:
                    value = value[0]
                items[key.decode('utf-8')] = value
    return items
