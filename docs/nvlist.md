Nvlists ("name value list") are an undocumented, typed binary key-value store.
The basic types use XDR encoding, also designed by Sun. XDR is standardized
in RFC 4506.

The main nvlist used by ZFS begins with the magic uint32 16842752.
Next, a uint64 == 1 denotes the start of the list itself. The list ends
when the next element is declared to have length 0, which may immediately
follow the start of the list.

Each element of the list contains the following elements:

* uint32 decoded length: the actual length of this element
* uint32 length: the length of this element as stored on disk (redundant)
* string name: the name of the key
* uint32 value type: the type of this value (see type list, below)
* uint32 value count: the number of elements in an array value
* varies value

The types are:

* UNKNOWN = 0
* BOOLEAN = 1
* * no data; presence of the key appears to indicate True
* BYTE = 2
* INT16 = 3
* UINT16 = 4
* INT32 = 5
* UINT32 = 6
* INT64 = 7
* UINT64 = 8
* * an XDR hyper
* STRING = 9
* * an XDR string (uint32 length + data)
* BYTE_ARRAY = 10
* INT16_ARRAY = 11
* UINT16_ARRAY = 12
* INT32_ARRAY = 13
* UINT32_ARRAY = 14
* INT64_ARRAY = 15
* UINT64_ARRAY = 16
* STRING_ARRAY = 17
* HRTIME = 18
* NVLIST = 19
* * an nvlist
* NVLIST_ARRAY = 20
* * `value_count` nvlists
* BOOLEAN_VALUE = 21
* INT8 = 22
* UINT8 = 23
* BOOLEAN_ARRAY = 24
* INT8_ARRAY = 25
