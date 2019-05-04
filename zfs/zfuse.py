#!/usr/bin/env python

import functools
import logging

from errno import ENOENT, EINVAL
from stat import S_IFDIR, S_IFLNK, S_IFREG
import _thread

from fuse import FUSE, FuseOSError, Operations

from zfs import datasets
from zfs import posix
from zfs.posix.attributes import PosixType

logger = logging.getLogger(__name__)


def locked(f):
    @functools.wraps(f)
    def inner(self, *a, **kw):
        with self.pool_lock:
            return f(self, *a, **kw)

    return inner


class ZFSFuse(Operations):

    def __init__(self, pool=None):
        self.pool = pool
        self.fd = 0
        self.pool_lock = _thread.allocate_lock()
        logger.critical('...')

    @locked
    def getattr(self, path, fh=None):
        try:
            obj = self.pool.open(path)
            if path.endswith('etc/resolv.conf'):
                logger.debug(f'asdf asdf {obj} {obj.attrs} {obj.dnode.index}')
            if isinstance(obj, datasets.Dataset):
                obj = obj.root_directory
            if isinstance(obj, posix.PosixObject):
                attrs = obj.attrs
                mode = attrs['ZPL_MODE'].perms
                logger.debug(f'{path}, {attrs.keys()}')
                logger.debug(mode)
                if isinstance(obj, posix.Directory):
                    mode |= S_IFDIR
                elif 'ZPL_SYMLINK' in attrs or attrs['ZPL_MODE'].file_type == PosixType.SYMLINK:
                    mode |= S_IFLNK
                elif isinstance(obj, posix.File):
                    mode |= S_IFREG
                return {
                    'st_mode': mode,
                    'st_uid': attrs['ZPL_UID'],
                    'st_gid': attrs['ZPL_GID'],
                    'st_size': attrs['ZPL_SIZE'],
                    'st_mtime': attrs['ZPL_MTIME'].seconds,
                    'st_atime': attrs['ZPL_ATIME'].seconds,
                    'st_ctime': attrs['ZPL_CTIME'].seconds,
                }
            else:
                return {}
        except Exception as e:
            logger.exception('error in getattr')
            raise FuseOSError(ENOENT)

    def getxattr(self, path, name, position=0):
        return b''

    def listxattr(self, path):
        return []

    def open(self, path, flags):
        self.fd += 1
        return self.fd

    @locked
    def readlink(self, path):
        try:
            logger.debug(f'attempted to readlink {path}')
            obj = self.pool.open(path)
            return obj.attrs['ZPL_SYMLINK']
        except Exception as e:
            logger.exception(f'readlink failed for {path}')
            raise FuseOSError(ENOENT)

    @locked
    def read(self, path, size, offset, fh):
        try:
            return self.pool.read_file(path)[offset:offset+size]
        except Exception as e:
            logger.exception("error in read")
            raise FuseOSError(EINVAL)

    @locked
    def readdir(self, path, fh):
        try:
            names = ['.', '..']
            for name in self.pool.open(path).keys():
                if isinstance(name, bytes):
                    name = name.decode('utf8')
                names.append(name)
            logger.info(' '.join(names))
            return names
        except Exception as e:
            logger.exception("error in readdir")
            raise FuseOSError(EINVAL)

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)


def mount(pool, mountpoint):
    zf = ZFSFuse(pool)
    fuse = FUSE(zf, mountpoint,
                foreground=True,
                rdonly=True,
                nobrowse=True,
                jail_symlinks=True,
                nolocalcaches=True,
                # debug=True,
                )
