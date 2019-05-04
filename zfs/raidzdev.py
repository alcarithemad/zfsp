import itertools
import logging
import operator
import struct
from typing import Union, Tuple

from zfs import ondisk, vdevs
from functools import reduce

logger = logging.getLogger(__name__)


def convert(k, base, disks, parity):
    off = (disks+parity+2)/base
    k -= base
    if k >= 230:
        off -= 3
    return (k + off) % disks


def should_resize(offset, size, disks, parity):
    base = (size % 10)
    if size >= 8 and base in (4, 8):
        return convert(size, base, disks, parity) == offset % disks
    else:
        return False


# thanks aschmitz
def locate_data(disks, parity, offset, size):
    first_col = parity
    ret = [disks, first_col]
    vdevs = []
    bit_12 = (offset >> 11) & 1
    vdev_ids = list(range(disks))
    order = list(range(disks))
    if bit_12:
        order[0:2] = reversed(order[0:2])
    for i in order:
        dva = ondisk.dva()
        dva.vdev = vdev_ids[(offset + i) % disks]
        dva.offset = int((offset + i) / disks)
        vdevs.append(dva)
    vdev_order = [d.vdev for d in vdevs]
    if size > 318:
        logger.debug('*'*30, size)
    if disks == 5 and should_resize(offset, size, disks, parity):
        logger.debug('!!!!!! size decrease {} {:} {:} {} {:} {}'.format(offset % disks, offset, size, list(map(int, vdev_order)), size, bit_12))
        size -= 1
    for _, next_vdev in zip(range(size), itertools.cycle(vdevs)):
        next_vdev.asize += 1
    ret.append(tuple(vdevs))
    return ret


def xor_blocks(*args):
    args = [x for x in args if len(x)]
    if len(args) == 0:
        return ''
    size = min(len(x) for x in args)
    args = [x[:size] for x in args]
    format_str = '>'
    if size >= 8:
        format_str += '{}Q'.format(int(size/8))
    if size % 8:
        format_str += '{}B'.format(size % 8)
    structure = struct.Struct(format_str)
    out = [reduce(operator.xor, t) for t in zip(*(structure.unpack(x) for x in args))]
    return structure.pack(*out)


class RaidZDev(vdevs.VDev):
    def __init__(self, parity, devs):
        self.devs = devs
        self.parity = parity
        self.label = devs[0].label
        self.best_label = devs[0].best_label
        self.id = self.label[b'vdev_tree'][b'id']
        self.active_uberblock = devs[0].active_uberblock

    def _read_resolved(self, dva):
        return self.devs[dva.vdev].read_dva(dva)

    def read_dva(self, dva):
        offset = dva.offset
        num_disks = len(self.devs)
        parity = self.parity
        columns, first, addrs = locate_data(num_disks, parity, offset, dva.asize)
        if columns == num_disks:
            blocks = [self._read_resolved(addr) for addr in addrs]
            data = b''.join(blocks[first:])
        else:
            raise Exception('wtf? {}'.format(addrs))
        computed = xor_blocks(*blocks[first:])
        self.blocks = blocks[:] + [computed]
        self.last_dva = dva, addrs
        return data

    def read(self, offset: Union[int, Tuple[int, int]], size: int) -> bytes:
        raise Exception

