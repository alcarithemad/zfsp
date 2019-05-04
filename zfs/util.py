import hashlib
import logging
import struct
import zlib

from typing import Tuple


from .constants import Checksum
from .constants import Compression

logger = logging.getLogger(__name__)

try:
    from . import rlzjb as lzjb
except ImportError:
    from . import lzjb

try:
    import lz4
    import lz4.block
except ImportError:
    lz4 = None
    logger.warn("import lz4 failed, lz4 decompression will not be available.")


counter = __import__('itertools').count()


def decompress(data: bytes, mode: Compression, size: int, inherit=None) -> bytes:
    if mode == Compression.INHERIT:
        mode = inherit
    if mode in (Compression.ON, Compression.LZJB):
        return bytes(lzjb.decompress(data, size))
    elif mode == Compression.LZ4 and lz4:
        length = struct.unpack('>I', data[:4])[0]
        data = data[4:length + 4]
        return lz4.block.decompress(struct.pack('<i', size) + data)
    elif mode.name.startswith('GZIP_'):
        data = zlib.decompress(data)
        return data[:size]
    elif mode == Compression.OFF:
        return data
    else:
        if mode == Compression.LZ4 and not lz4:
            logging.error("Got a block with lz4 compression, but don't have `lz4` available")
        raise ValueError(mode)


ChecksumType = Tuple[int, int, int, int]


def checksum(data: bytes,
            valid: ChecksumType,
            mode: Checksum,
            inherit: Checksum=None,
            chk: ChecksumType=None
    ) -> bool:
    valid = tuple(valid)
    if mode == Checksum.INHERIT:
        mode = inherit
    if mode == Checksum.FLETCHER_4:
        chk = fletcher4(data)
    elif mode == Checksum.FLETCHER_2:
        chk = fletcher2(data)
    elif mode == Checksum.SHA256:
        chk = sha256(data)
    elif mode == Checksum.OFF:
        return True
    else:
        raise ValueError(mode)
    return all(c == v for c, v in zip(chk, valid))


def sha256(data: bytes) -> ChecksumType:
    return struct.unpack('>QQQQ', hashlib.sha256(data).digest())


def unpack(data: bytes, code: str):
    s = struct.calcsize(code)
    return struct.unpack(code*int(len(data)/s), data)


def fletcher2(data: bytes) -> ChecksumType:
    mod = 1 << 64
    un_data = list(unpack(data, 'Q'))
    a = 0
    b = 0
    c = 0
    d = 0
    for first, second in zip(un_data[0::2], un_data[1::2]):
        a = (a + first) % mod
        b = (b + second) % mod
        c = (c + a) % mod
        d = (d + b) % mod
    return a, b, c, d


def fletcher4(data: bytes) -> ChecksumType:
    mod = 1 << 64
    a = 0
    b = 0
    c = 0
    d = 0
    for w in unpack(data, 'I'):
        a = (a + w) % mod
        b = (b + a) % mod
        c = (c + b) % mod
        d = (d + c) % mod

    return a, b, c, d
