from typing import ByteString


def decompress(bs: ByteString, size: int) -> ByteString:
    bs = bytearray(bs)
    out = bytearray()
    blen = len(bs)
    pos = 0
    while pos < blen and len(out) < size:
        control = bs[pos]
        pos += 1
        for i in range(8):
            b = control & (1 << i) > 0
            if not pos < blen:
                break
            if not b:
                out.append(bs[pos])
                pos += 1
            else:
                length = (bs[pos] >> 2) + 3
                distance = (bs[pos] & 0b11) << 8 | bs[pos+1]
                pos += 2
                backref = out[-distance:]
                lookup = backref * int(length / distance) + backref[:(length % distance)]
                out += lookup
    return out[:size]
