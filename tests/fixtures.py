import os.path
import sys

import pytest

from zfs import pool, filedev, raidzdev

module_path = os.path.dirname(sys.modules[__name__].__dict__.get('__file__', ''))
fixture_path = os.path.join(module_path, 'fixtures')
static_fixture_path = os.path.join(module_path, 'static')

def fixture(path):
    return os.path.join(fixture_path, path)

def static_fixture(path):
    return os.path.join(static_fixture_path, path)


def generate_test_name(param):
    if isinstance(param[0], filedev.FileDev):
        return param[0].f.name.split('/')[-1]
    elif isinstance(param[0], raidzdev.RaidZDev):
        return generate_test_name(param[0].devs)

feature_pools = {
    b'com.delphix:extensible_dataset':[filedev.FileDev(fixture('feature_extensible_dataset'))],
    b'com.delphix:hole_birth':[filedev.FileDev(fixture('feature_hole_birth'))],
    b'com.delphix:embedded_data':[filedev.FileDev(fixture('feature_embedded_data'))],
    b'org.open-zfs:large_block':[filedev.FileDev(fixture('feature_large_blocks'))],
}

old_version_pools = []
for version in range(1, 29):
    old_version_pools.append([filedev.FileDev(fixture('versioned/zversion_{}'.format(version)))])

@pytest.fixture(params=[
    [filedev.FileDev(fixture('simple'))],
    [filedev.FileDev(fixture('nested_datasets'))],
    [filedev.FileDev(fixture('ashift_12'))],
    [
        filedev.FileDev(fixture('two_vdevs_1')),
        filedev.FileDev(fixture('two_vdevs_2')),
    ],
    [
        filedev.FileDev(fixture('three_vdevs_1')),
        filedev.FileDev(fixture('three_vdevs_2')),
        filedev.FileDev(fixture('three_vdevs_3')),
    ],
    [
        filedev.FileDev(fixture('five_vdevs_1')),
        filedev.FileDev(fixture('five_vdevs_2')),
        filedev.FileDev(fixture('five_vdevs_3')),
        filedev.FileDev(fixture('five_vdevs_4')),
        filedev.FileDev(fixture('five_vdevs_5')),
    ],
    [
        filedev.FileDev(fixture('zmirror1')),
        filedev.FileDev(fixture('zmirror2')),
    ],
    [
        raidzdev.RaidZDev(1, [
            filedev.FileDev(fixture('zraid1-1')),
            filedev.FileDev(fixture('zraid1-2')),
            filedev.FileDev(fixture('zraid1-3')),
        ])
    ],
] + list(feature_pools.values()) + old_version_pools, ids=generate_test_name)
def zpool(request):
    zp = pool.Pool(request.param)
    return zp

@pytest.fixture
def complex_zpool():
    return pool.Pool([filedev.FileDev(fixture('nested_datasets'))])


@pytest.fixture
def lz4_zpool():
    return pool.Pool([filedev.FileDev(fixture('lz4'))])
