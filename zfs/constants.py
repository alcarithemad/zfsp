import enum

POOL_VERSION = 5000


class Compression(enum.IntEnum):
    INHERIT = 0
    ON = 1
    OFF = 2
    LZJB = 3
    EMPTY = 4
    GZIP_1 = 5
    GZIP_2 = 6
    GZIP_3 = 7
    GZIP_4 = 8
    GZIP_5 = 9
    GZIP_6 = 10
    GZIP_7 = 11
    GZIP_8 = 12
    GZIP_9 = 13
    ZLE = 14
    LZ4 = 15


class Checksum(enum.IntEnum):
    INHERIT = 0
    ON = 1
    OFF = 2
    LABEL = 3
    GANG_HEADER = 4
    ZILOG = 5
    FLETCHER_2 = 6
    FLETCHER_4 = 7
    SHA256 = 8
    ZILOG2 = 9
    NOPARITY = 10


class ObjectSetType(enum.IntEnum):
    NONE = 0
    META = 1
    ZFS = 2
    ZVOL = 3


class TryConfig(enum.Enum):
    read_all_dvas = True


class ObjectType(enum.IntEnum):
    NONE = 0
    OBJECT_DIRECTORY = 1         # ZAP
    OBJECT_ARRAY = 2             # UINT64
    PACKED_NVLIST = 3            # UINT8 (XDR by nvlist_pack/unpack)
    PACKED_NVLIST_SIZE = 4       # UINT64
    BPOBJ = 5                    # UINT64
    BPOBJ_HDR = 6                # UINT64
    SPACE_MAP_HEADER = 7         # UINT64
    SPACE_MAP = 8                # UINT64
    INTENT_LOG = 9               # UINT64
    DNODE = 10                   # DNODE
    OBJSET = 11                  # OBJSET
    DSL_DIR = 12                 # UINT64
    DSL_DIR_CHILD_MAP = 13       # ZAP
    DSL_DS_SNAP_MAP = 14         # ZAP
    DSL_PROPS = 15               # ZAP
    DSL_DATASET = 16             # UINT64
    ZNODE = 17                   # ZNODE
    OLDACL = 18                  # Old ACL
    PLAIN_FILE_CONTENTS = 19     # UINT8
    DIRECTORY_CONTENTS = 20      # ZAP
    MASTER_NODE = 21             # ZAP
    UNLINKED_SET = 22            # ZAP
    ZVOL = 23                    # UINT8
    ZVOL_PROP = 24               # ZAP
    PLAIN_OTHER = 25             # UINT8
    UINT64_OTHER = 26            # UINT64
    ZAP_OTHER = 27               # ZAP
    ERROR_LOG = 28               # ZAP
    SPA_HISTORY = 29             # UINT8
    SPA_HISTORY_OFFSETS = 30     # spa_his_phys_t
    POOL_PROPS = 31              # ZAP
    DSL_PERMS = 32               # ZAP
    ACL = 33                     # ACL
    SYSACL = 34                  # SYSACL
    FUID = 35                    # FUID table (Packed NVLIST UINT8)
    FUID_SIZE = 36               # FUID table size UINT64
    NEXT_CLONES = 37             # ZAP
    SCAN_QUEUE = 38              # ZAP
    USERGROUP_USED = 39          # ZAP
    USERGROUP_QUOTA = 40         # ZAP
    USERREFS = 41                # ZAP
    DDT_ZAP = 42                 # ZAP
    DDT_STATS = 43               # ZAP
    SA = 44                      # System attr
    SA_MASTER_NODE = 45          # ZAP
    SA_ATTR_REGISTRATION = 46    # ZAP
    SA_ATTR_LAYOUTS = 47         # ZAP
    SCAN_XLATE = 48              # ZAP
    DEDUP = 49                   # fake dedup BP from ddt_bp_create()
    DEADLIST = 50                # ZAP
    DEADLIST_HDR = 51            # UINT64
    DSL_CLONES = 52              # ZAP
    BPOBJ_SUBOBJ = 53            # UINT64
    FEATURE_DESCRIPTION = 196    # ZAP


class ZILTypes(enum.IntEnum):
    CREATE = 1     # Create file
    MKDIR = 2      # Make directory
    MKXATTR = 3    # Make XATTR directory
    SYMLINK = 4    # Create symbolic link to a file
    REMOVE = 5     # Remove file
    RMDIR = 6      # Remove directory
    LINK = 7       # Create hard link to a file
    RENAME = 8     # Rename a file
    WRITE = 9      # File write
    TRUNCATE = 10  # Truncate a file
    SETATTR = 11   # Set file attributes
    ACL = 12       # Set acl


class ZapType(enum.Enum):
    ZAPHeader = (1 << 63) + 1
    ZAPLeaf = 1 << 63
    MicroZAP = (1 << 63) + 3
