import logging
import struct

from io import BytesIO

from typing import Union

from nvlist import NVTypes

logger = logging.getLogger(__name__)


def next_break_offset(x):
    # this is the next multiple of 8
    return (x + 7) & ~7


class HistoryParser(object):
    def __init__(self, buffer: Union[BytesIO, bytes]) -> None:
        if isinstance(buffer, bytes):
            self.buf = BytesIO(buffer)
        else:
            self.buf = buffer

    def unpack_int(self):
        return struct.unpack('<i', self.buf.read(4))[0]

    def unpack_uint(self):
        return struct.unpack('<I', self.buf.read(4))[0]

    def unpack_hyper(self):
        return struct.unpack('<q', self.buf.read(8))[0]

    def unpack_uhyper(self):
        return struct.unpack('<Q', self.buf.read(8))[0]

    def unpack_fstring(self, length):
        total_length = next_break_offset(length)
        return self.buf.read(total_length)[:length]

    def unpack_string(self):
        length = self.unpack_uint()
        return self.unpack_fstring(length)

    def unpack_value(self):
        pos = self.buf.tell()
        total_length = self.unpack_uint()
        if total_length == 0:
            return '', ''
        length = self.unpack_uint()
        value_count = self.unpack_uint()
        value_type = NVTypes(self.unpack_uint())
        key = self.unpack_fstring(length)
        key = key.rstrip('\x00')

        remaining = total_length - (self.buf.tell() - pos)

        values = []
        for v in range(value_count):
            if value_type == NVTypes.UINT64:
                value = self.unpack_uhyper()
            elif value_type == NVTypes.INT32:
                value = self.unpack_uhyper()
            elif value_type == NVTypes.STRING:
                value = self.buf.read(remaining)
                value = value.rstrip('\x00')
            elif value_type == NVTypes.NVLIST:
                # print 'nvlist', total_length, remaining
                value = self.unpack_nvlist(extra=True)
            elif value_type == NVTypes.BOOLEAN:
                value = self.unpack_uhyper()
            else:
                logger.debug('saw type', value_type, value_count, remaining)
                value = self.buf.read(remaining)
            values.append(value)
        remaining = total_length - (self.buf.tell() - pos)
        if remaining > 0:
            logger.debug('remains', remaining, value_count, value_type)
            values.append(self.buf.read(remaining))
        if len(values) == 1:
            values = values[0]
        return key, values

    def unpack_nvlist(self, extra=False):
        values = {}
        this_length = self.unpack_uhyper()
        unknown2 = self.unpack_uhyper()
        unknown3 = self.unpack_uint()
        start = self.buf.tell()
        if extra:
            self.unpack_uint()
        end_offset = start + this_length
        while self.buf.tell() <= end_offset:
            name, v = self.unpack_value()
            if name:
                values[name] = v
            else:
                break
        return values

    def unpack_history(self):
        total_length = len(self.buf.getvalue()) - 24
        history = [True]
        while self.buf.tell() < total_length and history[-1]:
            history.append(self.unpack_nvlist())
        return history[1:-1]
