import logging

from .. import ondisk
from .. import datasets
from zfs.posix.attributes import POSIXAttrs_for

logger = logging.getLogger(__name__)


class PosixObject(object):
    def __init__(self, dnode: ondisk.DNode, dataset: datasets.Dataset) -> None:
        self.attrs = POSIXAttrs_for(dataset)(dnode.bonus)
        self.dataset = dataset
        self.dnode = dnode


from .posix_file import File
from .directory import Directory
