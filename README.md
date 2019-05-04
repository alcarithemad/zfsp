# ZFSp

## What?

ZFS, in Python, without reading the original C.

## What?!

That's right.

## How?

Many hours spent staring at hexdumps, and asking friends to search the
internet for explanations of various features.

## Why?

Why not?

It seemed like it might be a fun project.

## Installation

The Pipfile lists the dependencies; there aren't many.

Python 3.5+ is required, but 3.6 is _not_, as PyPy runs this code
much, much faster (around 4x on the test suite) and didn't support 3.6 until recently.

    pipenv install -e .

N.B.: `-e` gets you an "editable" install; changes to the source tree will
affect the installed package's behavior.

## Test Suite.

Running the test suite requires one-time access to a system with ZFS, to generate the test pools.

Run `tests/fixtures.sh` on such a system and make the resulting directory `tests/fixtures`
(this is where it will end up if you run `fixtures.sh` directly from the `tests` directory).

The tests themselves can be run with `py.test`.
Most of the tests pass, but there are some known failures.
Feel free to try fixing them.

The tests are heavily parameterized and attempt to run all tests against
all relevant pool variations.

## Usage

`zexplore` is the main command line interface. It's reasonably well documented (I hope).

There's a subcommand for some limited FUSE support, which depends on `fusepy`
(developed with `2.0.4`). This is not installed by default in the Pipfile.

Example commands:

    $ zexplore label -p tests/fixtures/feature_large_blocks
    {b'errata': 0,
     b'features_for_read': {},
     b'guid': 6168868809305637343,
     b'hostid': 8323329,
     b'hostname': b'ubuntu-zesty',
     b'name': b'feature_large_blocks',
     b'pool_guid': 16637796155898928459,
     b'state': 1,
     b'top_guid': 6168868809305637343,
     b'txg': 16,
     b'vdev_children': 1,
     b'vdev_tree': {b'ashift': 9,
                    b'asize': 62390272,
                    b'create_txg': 4,
                    b'guid': 6168868809305637343,
                    b'id': 0,
                    b'is_log': 0,
                    b'metaslab_array': 33,
                    b'metaslab_shift': 24,
                    b'path': b'/vagrant/fixtures/feature_large_blocks',
                    b'type': b'file'},
     b'version': 5000}

    $ zexplore objset -p tests/fixtures/nested_datasets -P 1
    {'config': 27,
     'creation_version': 5000,
     'deflate': 1,
     'feature_descriptions': 30,
     'features_for_read': 28,
     'features_for_write': 29,
     'free_bpobj': 11,
     'history': 32,
     'root_dataset': 2,
     'sync_bplist': 31}

    $ zexplore ls -p tests/fixtures/nested_datasets /n1/n2/n3
    x
    y

    $ zexplore cat -p tests/fixtures/nested_datasets /gzip-9/gzip-9 | head -n 5
    A
    a
    aa
    aal
    aalii

## Caveats

Lots of things won't work, including:

* raidz with more than 4 disks will probably fail with an inscrutable error.
  ZFS uses a magic allocation function that's a non-linear black box. I haven't figured it out.
  raidz where the disks are larger than a few GB will probably also fail,
  but I haven't tested that at all.
* Some new feature flags have come out since I last worked on this seriously,
  and those features are (obviously) not supported. That's things like (incomplete list):
  * SHA-512/256
  * Skein
  * spacemap_v2
* Some feature flags that did exist when I was actively working on this are not implemented,
  either because I failed to figure out how they work, or because I didn't get around to trying.
* pyndata is the struct description library used to read all the on-disk structures.
  I wrote it first, and it's bad. If I was doing this again today,
  I'd probably build something with dataclasses.
* There's a [Rust implementation of LZJB](https://github.com/alcarithemad/rlzjb) which is not
  currently included, but decompression is not the bottleneck.
