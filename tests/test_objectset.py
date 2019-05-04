from zfs import objectset

from fixtures import zpool


def test_objset(zpool):
    assert zpool.objset_for_vdev(0)
