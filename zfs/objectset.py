import logging
import struct

from typing import Any
from typing import Dict
from typing import List
from typing import Iterator
from typing import Union

from io import BytesIO

import zfs.ondisk.zap

from . import posix
from . import history
import nvlist
from . import ondisk
from . import datasets

from .constants import ObjectType

logger = logging.getLogger(__name__)

MicroZAPType = Union[zfs.ondisk.zap.SARegistrationMicroZAP, zfs.ondisk.zap.MicroZAP]


class ObjectSet(object):
    @classmethod
    def from_struct(cls, pool, strct: ondisk.Objectsets, dataset: 'datasets.Dataset' = None) -> 'ObjectSet':
        blocks = []
        for blkptr in strct.meta_dnode.blkptr:
            block = pool.read_indirect(blkptr)
            blocks.append(block)
        return ObjectSet(pool, strct, b''.join(blocks), dataset=dataset)

    @classmethod
    def from_block(cls, pool, block: bytes, dataset: 'datasets.Dataset' = None) -> 'ObjectSet':
        objset_struct = ondisk.Objset_for(pool.version)(block)
        objset = ObjectSet.from_struct(pool, objset_struct, dataset=dataset)
        return objset

    def __init__(self, pool, raw_objectset: ondisk.Objectsets, objset: bytes, dataset=None) -> None:
        self.raw_objectset = raw_objectset
        self.pool = pool
        self.dataset = dataset
        self.objset = objset
        self.dnodes = {}
        self.parsed_objset = {}

    def __getitem__(self, index: Union[int, slice]) -> Any:
        if isinstance(index, slice):
            return [self[i] for i in range(index.start or 0, index.stop or len(self.objset)//512, index.step or 1)]
        else:
            if index not in self.parsed_objset:
                self.parsed_objset[index] = self.parse_dnode(self.get_dnode(index), index=index)
            return self.parsed_objset[index]

    def __iter__(self) -> Iterator:
        length = len(self.objset)//512
        for i in range(length):
            yield self.get_dnode(i)

    def get_dnode(self, index: int) -> ondisk.DNode:
        if index not in self.dnodes:
            offset = index * 512
            dn = ondisk.DNode(self.objset[offset:offset+512])
            dn.index = index
            self.dnodes[index] = dn
        return self.dnodes[index]

    def parse_dnode(self, dnode: ondisk.DNode, index: int = None) -> Any:
        nt = dnode.node_type
        try:
            if nt == ObjectType.NONE:
                return self.read_none(dnode)
            elif nt == ObjectType.OBJECT_DIRECTORY:
                return self.read_zap(dnode)
            elif nt == ObjectType.DSL_DIR_CHILD_MAP:
                return self.read_zap(dnode)
            elif nt == ObjectType.DSL_DS_SNAP_MAP:
                return self.read_zap(dnode)
            elif nt == ObjectType.NEXT_CLONES:
                return self.read_zap(dnode)
            elif nt == ObjectType.DEADLIST:
                return self.read_zap(dnode)
            elif nt == ObjectType.DSL_CLONES:
                return self.read_zap(dnode)
            elif nt == ObjectType.MASTER_NODE:
                return self.read_zap(dnode)
            elif nt == ObjectType.PLAIN_FILE_CONTENTS:
                return self.read_file(dnode)
            elif nt == ObjectType.DIRECTORY_CONTENTS:
                return self.read_directory(dnode)
            elif nt == ObjectType.SA_MASTER_NODE:
                return self.read_zap(dnode)
            elif nt == ObjectType.UNLINKED_SET:
                return self.read_zap(dnode)
            elif nt == ObjectType.SA_ATTR_REGISTRATION:
                return self.read_attr_registration(dnode)
            elif nt == ObjectType.SA_ATTR_LAYOUTS:
                return self.read_zap(dnode)
            elif nt == ObjectType.DSL_PROPS:
                return self.read_zap(dnode)
            elif nt == ObjectType.FEATURE_DESCRIPTION:
                return self.read_zap(dnode)
            elif nt == ObjectType.ZVOL_PROP:
                return self.read_zap(dnode)
            elif nt == ObjectType.SPA_HISTORY:
                return self.read_history(dnode)
            elif nt == ObjectType.OBJECT_ARRAY:
                return self.read_object_array(dnode)
            elif nt == ObjectType.PACKED_NVLIST:
                return self.read_nvlist(dnode)
            elif nt == ObjectType.DSL_DATASET:
                return self.read_dataset(dnode)
            elif nt == ObjectType.DSL_DIR:
                return self.read_dsldir(dnode)
            elif nt == ObjectType.BPOBJ:
                return self.read_bpobj(dnode)
            else:
                return self.read_default(dnode)
        except Exception:
            if self.dataset:
                ds = self.dataset.path.replace('/', '-')
                with open('failed/{}_{}_{}'.format(ds, nt.name, index or '-'), 'wb') as f:
                    f.write(self.pool.read_dnode(dnode))
            raise

    def read_default(self, dnode: ondisk.DNode) -> ondisk.DNode:
        return dnode

    def read_none(self, dnode: ondisk.DNode) -> None:
        assert dnode.node_type == ObjectType.NONE
        return None

    def read_directory(self, dnode: ondisk.DNode) -> 'posix.Directory':
        entries = self.read_zap(dnode)
        newdir = posix.Directory(dnode, entries, self.dataset, self)
        return newdir

    def read_file(self, dnode: ondisk.DNode) -> 'posix.File':
        return posix.File(dnode, self.dataset)

    def read_zap(self, dnode: ondisk.DNode) -> Dict[str, Any]:
        raw_zap = self.pool.read_dnode(dnode)
        zap = BytesIO(raw_zap)
        hdr = zfs.ondisk.zap.MicroZAPHeader(zap)
        if hdr.block_type == zfs.ondisk.zap.ZapType.ZAPHeader:
            return self._read_fatzap(raw_zap)
        else:
            return self._read_microzap(dnode, hdr, zap)

    def _read_microzap(self, dnode: ondisk.DNode, hdr: zfs.ondisk.zap.MicroZAPHeader, zap: BytesIO) -> Dict[str, Any]:
        node_type = dnode.node_type
        max_entries = int((len(zap.getvalue()) - 128) / 64)
        mzaps = []
        if node_type == ObjectType.SA_ATTR_REGISTRATION:
            mzap_type = zfs.ondisk.zap.SARegistrationMicroZAP
        else:
            mzap_type = zfs.ondisk.zap.MicroZAP
        if hdr.block_type == zfs.ondisk.zap.ZapType.MicroZAP:
            while len(mzaps) <= max_entries:
                mzaps.append(mzap_type(zap))
        if node_type == ObjectType.SA_ATTR_REGISTRATION:
            r = {z.hdr.name: z for z in mzaps if z.hdr.name != ''}
            return r
        else:
            r = {z.hdr.name: z.value for z in mzaps if z.hdr.name != ''}
            return r

    def read_attr_registration(self, dnode: ondisk.DNode) -> Dict:
        data = self.read_zap(dnode)
        ret = {}
        for k, v in data.items():
            ret[k] = {
                'attr_num': v.attr_num,
                'byteswap': v.byteswap,
                'length': v.length,
            }
        return ret

    def _read_fatzap(self, raw_fz: bytes) -> Dict[str, Any]:
        logger.debug('reading a fatzap')
        data = ondisk.fatzap.parse_fatzap(raw_fz)
        return data

    def read_bpobj(self, dnode: ondisk.DNode) -> List[ondisk.Blockptr]:
        hdr = ondisk.BPObjHeader(dnode.bonus)
        logger.info(hdr)
        data = self.pool.read_dnode(dnode)
        data = BytesIO(data)
        return [ondisk.Blockptr(data) for _ in range(hdr.length)]

    def read_object_array(self, dnode: ondisk.DNode) -> Dict:
        data = self.pool.read_dnode(dnode)
        length = int(len(data) / 8)
        format_code = '<' + (length * 'Q')
        return {i+1: x for i, x in enumerate(struct.unpack(format_code, data)) if x != 0}

    def read_nvlist(self, dnode: ondisk.DNode) -> Dict:
        nv = self.pool.read_block(dnode.blkptr[0])
        nv = nv[:dnode.used]
        nvl = nvlist.NVList(nv)
        nvdata = nvl.unpack_nvlist()
        return nvdata

    def read_dataset(self, dnode: ondisk.DNode) -> ondisk.DSLDataset:
        return ondisk.DSLDataset(dnode.bonus)

    def read_dsldir(self, dnode: ondisk.DNode) -> 'datasets.Dataset':
        from . import datasets
        dsl_dir = ondisk.DSLDir(dnode.bonus)
        return datasets.Dataset(self.pool, dsl_dir, self, dnode)

    def read_history(self, dnode: ondisk.DNode) -> Dict:
        data = self.pool.read_dnode(dnode)
        history_parser = history.HistoryParser(data)
        return history_parser.unpack_history()
