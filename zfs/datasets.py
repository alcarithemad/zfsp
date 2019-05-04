import logging
import os

from typing import Any
from typing import Dict
from typing import Iterator

from . import objectset
from zfs import posix

logger = logging.getLogger(__name__)


class Dataset(object):
    def __init__(self, pool, dsl_dir, objset, dnode, path=None):
        self.pool = pool
        self.parent_objectset = objset
        self.dsl_dir = dsl_dir
        self.dnode = dnode
        self.dsl_dataset = objset[dsl_dir.head_dataset]
        self.path = path or '/'
        self.properties = objset[dsl_dir.props_zap]
        self._snapshots = None
        self._snapshot_names = None

        objset_block = self.pool.read_block(self.dsl_dataset.bp)
        self.objectset = objectset.ObjectSet.from_block(self.pool, objset_block, dataset=self)

    @property
    def child_datasets(self) -> 'ChildDatasets':
        children = self.parent_objectset[self.dsl_dir.child_dir_zap]
        return ChildDatasets(children, self, self.parent_objectset, path=self.path)

    @property
    def snapshot_names(self) -> Dict:
        if not self._snapshot_names:
            self._snapshot_names = self.parent_objectset[self.dsl_dataset.snapnames_zap]
        return self._snapshot_names

    @property
    def snapshots(self) -> Dict[str, 'Dataset']:
        if not self._snapshots:
            snapshots = {}
            for name, index in self.snapshot_names.items():
                dsl_dataset = self.parent_objectset[index]
                dataset = Dataset(
                    self.pool,
                    self.dsl_dir,
                    self.parent_objectset,
                    self.parent_objectset.objset[index],
                    path=self.path+'@'+name
                )
            self._snapshots = snapshots
        return self._snapshots

    @property
    def entries(self) -> Dict[str, Any]:
        d = dict(self.child_datasets.entries)
        d.update(self.root_directory.entries)
        return d

    def __contains__(self, item) -> bool:
        return (item in self.child_datasets) or (item in self.root_directory)

    def __getitem__(self, item):
        if item in self.child_datasets:
            return self.child_datasets[item]
        else:
            return self.root_directory[item]

    def keys(self):
        return self.root_directory.keys()

    def items(self):
        return self.root_directory.items()

    def attributes(self, key):
        sa_attrs = self.objectset[self.objectset[1]['SA_ATTRS']]
        registry = self.objectset[sa_attrs['REGISTRY']]
        layout = self.objectset[sa_attrs['LAYOUTS']][key]
        attrs = {}
        for k, attr in registry.items():
            attrs[attr['attr_num']] = {
                'name': k,
                'byteswap': attr['byteswap'],
                'length': attr['length']
            }
        return [attrs[x] for x in layout]

    @property
    def root_directory(self) -> 'posix.Directory':
        root_dir_index = self.objectset[1]['ROOT']
        root_dir = self.objectset[root_dir_index]
        root_dir.path = self.path
        return root_dir

    def __repr__(self):
        return 'Dataset {path} children {children} root {root}'.format(
            path=self.path,
            children=list(self.child_datasets.keys()),
            root=list(self.root_directory.keys())
        )


class ChildDatasets:
    def __init__(self, entries: Dict[str, Any], dataset: Dataset, objectset: 'objectset.ObjectSet', path: str=None) -> None:
        self.entries = entries
        self.path = path
        self.dataset = dataset
        self.objectset = objectset

        self.resolved_entries = {}

    def __contains__(self, name: str) -> bool:
        return name in self.entries

    def __getitem__(self, name: str) -> Any:
        joined_path = os.path.join(self.path, name)
        if name not in self.resolved_entries:
            try:
                index = self.entries[name]
                obj = self.objectset[index]
                obj.path = joined_path
                self.resolved_entries[name] = obj
            except Exception:
                logger.exception(f'directory lookup failed for {joined_path}')
                raise FileNotFoundError(joined_path)
        return self.resolved_entries[name]

    def keys(self):
        return self.entries.keys()

    def items(self) -> Iterator:
        return ((k, self[k]) for k in self.keys())
