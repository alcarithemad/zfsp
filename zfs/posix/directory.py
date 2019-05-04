import logging
import os

from typing import Iterator
from typing import Tuple
from typing import Any
from typing import Sequence


import pyndata

import zfs.posix
from . import PosixObject
from .attributes import PosixType

logger = logging.getLogger(__name__)


class DirectoryEntry(pyndata.Struct):
    # this is not a real on-disk struct
    __ENDIAN__ = 'little'

    name = pyndata.nullstring(max_length=256)
    value = pyndata.uint64()
    value.__SHOW__ = False
    object_type = pyndata.BitField(value, 4, 60, enum=PosixType)
    number = pyndata.BitField(value, 48)


class Directory(PosixObject):
    def __init__(self, dnode, entries, dataset, objectset, path=None):
        super().__init__(dnode, dataset)
        self.entries = entries
        self.path = path
        self.objectset = objectset

        self.resolved_entries = {}

    def __contains__(self, name: str) -> bool:
        return name in self.entries

    def __getitem__(self, name: str) -> Any:
        joined_path = os.path.join(self.path, name)
        if name not in self.resolved_entries:
            try:
                entry_value = self.entries[name]
                entry = DirectoryEntry(name=name, value=entry_value)
                obj = self.objectset[entry.number]
                if isinstance(obj, (Directory, zfs.posix.File)):
                    obj.path = joined_path
                self.resolved_entries[name] = obj
            except Exception:
                logger.warning('directory lookup failed for {}'.format(joined_path))
                raise FileNotFoundError(joined_path)
        return self.resolved_entries[name]

    def keys(self) -> Sequence[str]:
        return self.entries.keys()

    def items(self) -> Iterator[Tuple[str, Any]]:
        return ((k, self[k]) for k in self.keys())

    def __repr__(self) -> str:
        return 'Directory {path} {entries}'.format(path=self.path, entries=list(self.keys()))
