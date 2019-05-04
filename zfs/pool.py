import os.path

from typing import List
from typing import Union
from typing import overload

from . import constants
from . import objectset
from . import readcontext
from . import datasets
from . import vdevs
from . import posix


def vdev_list_to_dict(vdevs):
    d = {}
    for v in vdevs:
        d[v.id] = v
    return d


class Pool(object):
    def __init__(self, vdevs: List[vdevs.VDev], try_config=None) -> None:
        self.vdevs = vdev_list_to_dict(vdevs)
        self.default_compression = constants.Compression.LZJB
        self.default_checksum = constants.Checksum.FLETCHER_4
        self.ashift = self.first_vdev().best_label[b'vdev_tree'][b'ashift']
        self.version = self.first_vdev().best_label[b'version']
        self.try_config = try_config or set()

        self._meta_object_sets = {}

    def first_vdev(self) -> vdevs.VDev:
        return list(self.vdevs.values())[0]

    def context(self) -> readcontext.ReadContext:
        return readcontext.ReadContext(
            self.vdevs,
            self.default_compression,
            self.default_checksum,
            self.ashift,
            self.try_config
        )

    def read_block(self, blkptr) -> bytes:
        return self.context().read_block(blkptr)

    def read_indirect(self, blkptr) -> bytes:
        return self.context().read_indirect(blkptr)

    def read_dnode(self, dnode) -> bytes:
        return self.context().read_dnode(dnode)

    def read_file(self, path: str) -> bytes:
        pathes = os.path.split(path)
        if len(pathes) != 2:
            raise NotImplementedError
        filename = pathes[-1]
        dir_ents = self.open(pathes[0])
        if filename not in dir_ents:
            raise OSError("file not found: {}".format(filename))
        return dir_ents[filename].read()

    @overload
    def objset_for_vdev(self, vdev: int) -> objectset.ObjectSet:
        ...

    @overload
    def objset_for_vdev(self, vdev: vdevs.VDev) -> objectset.ObjectSet:
        ...

    def objset_for_vdev(self, vdev) -> objectset.ObjectSet:
        if isinstance(vdev, int):
            vdev = self.vdevs[vdev]
        root = self.read_indirect(vdev.active_uberblock.root)
        vdev_id = vdev.id
        if vdev_id not in self._meta_object_sets:
            self._meta_object_sets[vdev_id] = objectset.ObjectSet.from_block(self, root)
        return self._meta_object_sets[vdev_id]

    @property
    def root_dataset(self) -> datasets.Dataset:
        objset = self.objset_for_vdev(self.first_vdev())
        dir_index = objset[1]['root_dataset']
        dataset = objset[dir_index]
        return dataset

    def metaslab_array(self):
        location = self.first_vdev().best_label[b'metaslab_array']
        return self.objset_for_vdev(self.first_vdev())[location]

    def dataset_for(self, dataset_expr: str) -> datasets.Dataset:
        if '@' not in dataset_expr:
            dataset_expr += '@'
        dataset_name, snapshot_name = dataset_expr.split('@', 1)
        ds = self.open(dataset_name)
        if isinstance(ds, datasets.Dataset):
            return ds.snapshots.get(snapshot_name, ds)
        else:
            raise KeyError

    def open(self, path: str) -> Union[datasets.Dataset, posix.Directory]:
        paths = path.lstrip('/').split('/')
        current = self.root_dataset
        if paths == ['']:
            return current
        for next_dir in paths:
            current = current[next_dir]
        return current
