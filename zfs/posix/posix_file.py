import logging

from . import PosixObject

logger = logging.getLogger(__name__)


class File(PosixObject):

    def read(self) -> bytes:
        data = self.dataset.pool.read_dnode(self.dnode)
        return data[:self.attrs['ZPL_SIZE']]
