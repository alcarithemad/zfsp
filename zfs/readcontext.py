import codecs
import logging

from typing import Tuple

from . import ondisk
from . import util

from .constants import Compression, Checksum, TryConfig

logger = logging.getLogger(__name__)


class ReadContext(object):
    def __init__(self, vdevs, compression, checksum, ashift, try_config):
        self.vdevs = vdevs
        self.default_compression = compression
        self.default_checksum = checksum
        self.blocksize = 1 << ashift
        self.try_config = try_config

    def checksum(self, data: bytes, valid, checksum) -> bool:
        return util.checksum(data, valid, checksum, self.default_checksum)

    def decompress(self, data: bytes, compression: Compression, actual_size: int) -> bytes:
        return util.decompress(data, compression, actual_size, self.default_compression)

    def update_inherit(self, compression: Compression, checksum: Checksum) -> None:
        if compression != Compression.INHERIT:
            self.default_compression = compression
        if checksum != Checksum.INHERIT:
            self.default_checksum = checksum

    def read_block(self, blkptr: ondisk.Blockptr, dva_offset=0) -> bytes:
        if TryConfig.read_all_dvas in self.try_config:
            block = self.read_block_thorough(blkptr)
            return block
        elif blkptr.embedded:
            block = self._read_block_embedded(blkptr)
            return block
        else:
            block, valid = self._read_block(blkptr, blkptr.dvas[dva_offset])
            if not valid:
                logger.error('bad checksum in block {}'.format(blkptr))
            return block

    def read_block_thorough(self, blkptr: ondisk.Blockptr) -> bytes:
        # this function tries DVAs in the blkptr until one works
        # DVAs with asize 0 are bullshit
        # we can pretend a blkptr whose DVAs are all size 0 is an empty string
        # but that's probably wrong
        if blkptr.embedded:
            return self._read_block_embedded(blkptr)
        if all(dva.asize == 0 for dva in blkptr.dvas):
            logger.debug('read an empty block pointer: {}'.format(blkptr))
            return b''
        first_log = True
        blocks = []
        bad = []
        for dva in blkptr.dvas:
            if dva.asize != 0:
                try:
                    block, valid = self._read_block(blkptr, dva)
                    if valid:
                        blocks.append(block)
                    else:
                        logger.error('checksum failed')
                        bad.append(block)
                except Exception:
                    if first_log:
                        logger.info('block pointer {}'.format(blkptr))
                        first_log = False
                    logger.exception('failed to read DVA {}'.format(dva))
                    pass
        if len(blocks) == 1:
            return blocks[0]
        elif len(blocks) > 1:
            if not all(x == y for x, y in zip(blocks, blocks[1:])):
                logger.error('block pointer {} had multiple allocated DVAs with different data!'.format(blkptr))
                logger.info('data lengths were {}'.format(list(map(len, blocks))))
                logger.debug('{}'.format([codecs.encode(b, 'hex') for b in blocks]))
            return blocks[0]
        else:  #len(blocks) must be 0
            logger.error('failed to read any DVAs in block pointer {}'.format(blkptr))
            return b''

    def _read_block_embedded(self, blkptr: ondisk.Blockptr) -> bytes:
        embedded_blkptr = blkptr.to_embedded()
        raw_data = embedded_blkptr.data
        data = self.decompress(raw_data, embedded_blkptr.compression, embedded_blkptr.logical_size+1)
        return data

    def _read_block(self, blkptr: ondisk.Blockptr, dva: ondisk.dva) -> Tuple[bytes, bool]:
        vdev = self.vdevs[dva.vdev]
        data = vdev.read_dva(dva)
        physical_size = (blkptr.physical_size + 1) * 512
        data = data[:physical_size]
        valid_chk = self.checksum(data, blkptr.checksum, blkptr.checksum_type)
        logical_size = (blkptr.logical_size + 1) * 512
        if valid_chk:
            logger.debug('decompress: {} {} {}'.format(blkptr, physical_size, logical_size))
            data = self.decompress(data, blkptr.compression, logical_size)
        return data, valid_chk

    def read_indirect(self, blkptr: ondisk.Blockptr) -> bytes:
        resolved = []
        if blkptr.level > 0:
            data = self.read_block(blkptr)
            indirect = ondisk.indirect(size=blkptr.logical_size + 1)
            ind = indirect(data)
            for ptr in ind.blocks:
                resolved.append(self.read_indirect(ptr))
        else:
            return self.read_block(blkptr)
        return b''.join(resolved)

    def read_dnode(self, dnode: ondisk.DNode) -> bytes:
        return b''.join(self.read_indirect(bp) for bp in dnode.blkptr)

    def context(self):
        return ReadContext(self.vdevs, self.default_compression, self.checksum, self.blocksize, self.try_config)
