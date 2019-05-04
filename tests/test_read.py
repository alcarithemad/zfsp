import pytest

from fixtures import zpool


def test_read_file(zpool):
    file_data = zpool.read_file('zeros')
    expected = b'\0' * 4097
    assert file_data == expected
    file2 = zpool.read_file('/d1/d2/d3/c')
    assert file2 == b'c\n'


def test_read_in_directory(zpool):
    path = '/'
    dir_ents = zpool.open(path)
    assert all(name in dir_ents for name in ['a', 'b', 'd1', 'fat', 'n1', 'zeros'])


def test_read_in_subdirectory(zpool):
    path = '/d1/d2/d3'
    dir_ents = zpool.open(path)
    assert set(dir_ents.keys()) == {'c', 'd'}


def test_read_in_nested_datasets(zpool):
    path = '/n1/n2/n3'
    dir_ents = zpool.open(path)
    assert set(dir_ents.keys()) == {'x', 'y'}


def test_read_fatzap_directory(zpool):
    dir_ents = zpool.open('/fat')
    assert 'greater_than_50_character_name_to_force_use_of_a_fatzap' in dir_ents
    assert 'second_long_nameAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' in dir_ents
    assert 'third_long_nameAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' in dir_ents
    assert 'fourth_long_nameAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' in dir_ents
