import xdrlib

import enum

NVAREA = 112 << 10


class NVTypes(enum.IntEnum):
    UNKNOWN = 0
    BOOLEAN = 1
    BYTE = 2
    INT16 = 3
    UINT16 = 4
    INT32 = 5
    UINT32 = 6
    INT64 = 7
    UINT64 = 8
    STRING = 9
    BYTE_ARRAY = 10
    INT16_ARRAY = 11
    UINT16_ARRAY = 12
    INT32_ARRAY = 13
    UINT32_ARRAY = 14
    INT64_ARRAY = 15
    UINT64_ARRAY = 16
    STRING_ARRAY = 17
    HRTIME = 18
    NVLIST = 19
    NVLIST_ARRAY = 20
    BOOLEAN_VALUE = 21
    INT8 = 22
    UINT8 = 23
    BOOLEAN_ARRAY = 24
    INT8_ARRAY = 25


class NVList(xdrlib.Unpacker):
    def unpack_nvlist(self):
        if self.unpack_uint() != 16842752:
            self.set_position(self.get_position() - 4)
        if self.unpack_uhyper() != 1:
            raise Exception('asdf')
        values = {}
        while len(self.get_buffer()) - self.get_position() >= 8:
            name, v = self.unpack_value()
            if name:
                values[name] = v
            else:
                return values

    def unpack_value(self):
        name, v = None, None
        decoded_length = self.unpack_uint()
        l = self.unpack_uint()

        if decoded_length > 0:
            name = self.unpack_string()
            value_type = self.unpack_uint()
            value_count = self.unpack_uint()
            if value_type == NVTypes.UINT64:
                v = self.unpack_uhyper()
            elif value_type == NVTypes.STRING:
                v = self.unpack_string()
            elif value_type == NVTypes.BOOLEAN:
                v = True
            elif value_type == NVTypes.NVLIST:
                v = self.unpack_nvlist()
            elif value_type == NVTypes.NVLIST_ARRAY:
                v = []
                for x in range(value_count):
                    sub = self.unpack_nvlist()
                    v.append(sub)
            else:
                raise Exception('Unknown nvlist value type {} for key {}'.format(value_type, name))
        return name, v
