import pytest

from zfs import pool

from fixtures import feature_pools

@pytest.mark.parametrize("feature", feature_pools)
def test_feature_active(feature):
    zp = pool.Pool(feature_pools[feature])
    features = zp.vdevs[0].best_label[b'features_for_read']
    assert feature in features
