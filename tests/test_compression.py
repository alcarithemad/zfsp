import pytest
from fixtures import complex_zpool, lz4_zpool, fixture, static_fixture

from zfs.constants import Compression

compresion_modes = {
    'gzip-1': Compression.GZIP_1,
    'gzip-2': Compression.GZIP_2,
    'gzip-3': Compression.GZIP_3,
    'gzip-4': Compression.GZIP_4,
    'gzip-5': Compression.GZIP_5,
    'gzip-6': Compression.GZIP_6,
    'gzip-7': Compression.GZIP_7,
    'gzip-8': Compression.GZIP_8,
    'gzip-9': Compression.GZIP_9,
    'lzjb': Compression.LZJB,
    'zle': Compression.ZLE,
}


@pytest.fixture(scope="module")
def file_contents():
    return open(static_fixture('words'), 'rb').read()


@pytest.mark.parametrize("mode", compresion_modes)
def test_zfs_compression(mode, complex_zpool, file_contents):
    root_dataset = complex_zpool.root_dataset
    zfile = root_dataset[mode][mode]
    assert zfile.dnode.blkptr[0].compression == compresion_modes[mode]
    result = zfile.read() == file_contents
    assert result


def test_lz4_compression(lz4_zpool, file_contents):
    root_dataset = lz4_zpool.root_dataset
    mode = 'lz4'
    zfile = root_dataset[mode][mode]
    assert zfile.dnode.blkptr[0].compression == Compression.LZ4
    result = zfile.read() == file_contents
    assert result
