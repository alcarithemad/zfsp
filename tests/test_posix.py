from fixtures import zpool


def test_ownership(zpool):
    directory = zpool.open('/d1/d2/d3')
    c = directory['c']
    assert c.attrs['ZPL_UID'] == 123
    assert c.attrs['ZPL_GID'] == 456


def test_permissions(zpool):
    directory = zpool.open('/d1/d2/d3')
    d = directory['d']
    assert d.attrs['ZPL_MODE'].perms == 0o1765
