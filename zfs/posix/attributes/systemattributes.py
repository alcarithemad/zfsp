import logging

from io import BytesIO

import pyndata
import struct

from . import Mode, Timestamp

logger = logging.getLogger(__name__)


def simple_attribute(data, attrs):
    return struct.unpack('<Q', data)[0]


def debug_simple_attribute(data, attrs):
    attr = simple_attribute(data, attrs)
    logger.info(attr)
    return attr


def eat_remainder(data, attrs):
    d = data.read()
    return d

def symlink(data, attrs):
    return eat_remainder(data, attrs).decode('utf-8')

def dacl_entries(data, attrs):
    if 'ZPL_DACL_COUNT' not in attrs:
        logger.error('found acl entry but no count!')
        raise KeyError('ZPL_DACL_COUNT not found')
    count = attrs['ZPL_DACL_COUNT']
    acls = []
    for x in range(count):
        acls.append(data.read(8))
    logger.debug(f'{data.tell()}/{len(data.getvalue())}')
    return acls


def no_attrs(f):
    def inner(data, attrs):
        return f(data)
    return inner


SYSTEM_ATTRIBUTES = {
    'ZPL_MODE': no_attrs(Mode),
    'ZPL_SIZE': simple_attribute,
    'ZPL_GEN': simple_attribute,
    'ZPL_UID': simple_attribute,
    'ZPL_GID': simple_attribute,
    'ZPL_PARENT': simple_attribute,
    'ZPL_FLAGS': simple_attribute,
    'ZPL_ATIME': no_attrs(Timestamp),
    'ZPL_MTIME': no_attrs(Timestamp),
    'ZPL_CTIME': no_attrs(Timestamp),
    'ZPL_CRTIME': no_attrs(Timestamp),
    'ZPL_LINKS': simple_attribute,
    'ZPL_XATTR': simple_attribute,
    'ZPL_DACL_COUNT': simple_attribute,
    'ZPL_DACL_ACES': dacl_entries,
    'ZPL_SYMLINK': symlink,
}


class SystemAttributeMagic(pyndata.Struct):
    magic = pyndata.bytestring(length=4)
    layout = pyndata.uint8()
    unknown1 = pyndata.uint8()
    unknown2 = pyndata.padding(length=2)
    unknown3 = pyndata.bytestring(length=lambda s, x=None: 8 if s.unknown1 == 8 else 0)


class SystemAttributes(object):
    def __init__(self, dataset):
        self.dataset = dataset

    def __call__(self, data):
        attributes = {}
        logger.debug(repr(data[:4]))
        data = BytesIO(data)
        attributes['header'] = hdr = SystemAttributeMagic(data)
        logger.debug(hdr)
        for attr in self.dataset.attributes(str(hdr.layout)):
            name = attr['name']
            logger.debug(f'processing attr {name}')
            if attr['length'] > 0:
                d = data.read(attr['length'])
            else:
                d = data
            if name not in SYSTEM_ATTRIBUTES:
                logger.debug('unknown attribute {}'.format(attr))
            attributes[name] = SYSTEM_ATTRIBUTES.get(name, eat_remainder)(d, attrs=attributes)
        return attributes
