#!/usr/bin/env python

import argparse
import logging
import sys

from pprint import pprint

import zfs.posix
from nvlist import NVList
from zfs import filedev
from zfs.posix import posix_file
from zfs.constants import ObjectType, TryConfig
from zfs.pool import Pool

try:
    from zfs import zfuse
except:
    zfuse = None

VERBOSE_LEVELS = [
    logging.CRITICAL,
    logging.ERROR,
    logging.WARNING,
    logging.INFO,
    logging.DEBUG,
]

TRY_LEVELS = [
    {}, # don't try anything extra
    {TryConfig.read_all_dvas: True}
]

logger = logging.getLogger(__name__)


class PoolExplorer(object):

    def __init__(self):
        self.parser = parser = argparse.ArgumentParser(prog='explore')
        subcommands = parser.add_subparsers(
            title='subcommands',
            description='explore a zpool',
            metavar='command'
        )

        parser.set_defaults(func=lambda a: parser.print_help(), pool=None)

        pool_parser = argparse.ArgumentParser(add_help=False)
        pool_parser.add_argument('--pool', '-p', action='append', required=True)
        pool_parser.add_argument('--vdev-id', type=int, default=None)
        pool_parser.add_argument('--label', '-L', type=int, default=None)
        pool_parser.add_argument('--txg', '-T', type=int, default=None)


        log_opts = parser.add_argument_group('logging options',
            'Options for controlling output. --verbose sets the log level globally.'
            ' The other options allow controlling the log level on a per-log basis.')

        log_opts.add_argument('--verbose', '-v', action='count', default=0,
            help='Increase verbosity. Add more instances (e.g., -vvv) to be even more verbose.'
            ' The default log level is CRITICAL.'
            f' At most {len(VERBOSE_LEVELS)-1} are useful.'
        )

        for level in map(logging.getLevelName, VERBOSE_LEVELS):
            level = level.lower()
            log_opts.add_argument(f'--{level}', metavar='MODULE', action='append', default=[],
                help=f"Set the log level for MODULE to {level}."
            )


        parser.add_argument('--try', '-t', dest='try_level', action='count',
            help="Try harder. More instances of this argument try even harder."
            " It's not useful to use more than 3. This is equivalent to an unspecified"
            " set of the --try-* arguments.",
            default=0
        )

        try_opts = parser.add_argument_group('Try harder', 'extra options for reading data.')
        parser.set_defaults(try_config=[])

        for name, value in TryConfig.__members__.items():
            arg_name = '--try-'+name.replace('_', '-')
            try_opts.add_argument(arg_name, dest='try_config', action='append_const', const=value)


        parser_ls = subcommands.add_parser('ls', parents=[pool_parser], help='list files')
        parser_ls.set_defaults(func=self.list_cmd)
        parser_ls.add_argument('path', default='/', nargs='?', help='List the items in PATH.')


        parser_cat = subcommands.add_parser('cat', parents=[pool_parser], help='cat file')
        parser_cat.set_defaults(func=self.cat)
        parser_cat.add_argument('path', help='Output the contents of PATH.')


        parser_objset = subcommands.add_parser('objectset', parents=[pool_parser], aliases=['objset'],
            help='inspect object sets')
        parser_objset.set_defaults(func=self.objset)
        parser_objset.add_argument('--dataset', '-d',
            help='Show the object set for DATASET. If not specified, show the meta object set.')
        parser_objset.add_argument('--self', action='store_true',
            help='Show extra info about the object set itself.')
        parser_objset.add_argument('--dump', metavar='FILE',
            help="follow the object's block pointers and dump their contents to FILE.")
        parser_objset.add_argument('--execute', '-e', metavar='CODE',
            help='Execute some Python CODE with the object in scope as `o`.')

        objset_selector_group = parser_objset.add_mutually_exclusive_group(required=True)
        objset_selector_group.add_argument('--all', '-a', action='store_true',
            help='Show all non-NONE objects.')
        objset_selector_group.add_argument('--everything', action='store_true',
            help='Show all objects, even empty ones.')
        objset_selector_group.add_argument('object', type=int, nargs='?', help='Object to display.')

        objset_exclusive_display = parser_objset.add_mutually_exclusive_group()
        objset_exclusive_display.add_argument('--parse', '-P', action='store_true',
            help='Show the parsed data, instead of the DNode.')
        objset_exclusive_display.add_argument('--dnode', '-D', action='store_true',
            help='Show raw DNodes.')


        parser_nvparse = subcommands.add_parser('nvparse', help='Parse an NVList from a file. WIP')
        parser_nvparse.set_defaults(func=self.nvparse)
        parser_nvparse.add_argument('file', help='The file to parse.')

        parser_label = subcommands.add_parser('label', parents=[pool_parser], help='View disk labels.')
        parser_label.set_defaults(func=self.label)
        parser_label.add_argument('label', type=int, default=0, nargs='?', choices=(0, 1, 2, 3),
            metavar='LABEL', help='Show information from LABEL, which must be 0, 1, 2, or 3.')
        parser_label.add_argument('--uberblocks', '-u', action='store_true')
        parser_label.add_argument('--all', action='store_true')


        parser_dva = subcommands.add_parser('dva', parents=[pool_parser], help='Read arbitrary blocks.')
        parser_dva.set_defaults(func=self.read_dva)
        parser_dva.add_argument('dva', help='The DVA (data virtual address) to read.')
        parser_dva.add_argument('--dump', metavar='FILE', help='Write the data to FILE.')

        parser_fuse = subcommands.add_parser('fuse', parents=[pool_parser],
            help='Mount a pool with the FUSE wrapper.')
        if zfuse:
            parser_fuse.set_defaults(func=self.mount_fuse)
        parser_fuse.add_argument('mountpoint', help='Set the mountpoint')
        parser_fuse.epilog = '''This requires the `fusepy` module, which in turn depends on libfuse.
            See https://pypi.python.org/pypi/fusepy for information. On macOS, you will also need
            https://osxfuse.github.io/
        '''

    def setup_module_logs(self, args):
        for level in VERBOSE_LEVELS:
            levelname = logging.getLevelName(level).lower()
            modules = getattr(args, levelname)
            for mod in modules:
                logging.getLogger(mod).setLevel(level)

    def cli(self, *a, **kw):
        args = self.parser.parse_args(*a, **kw)
        level = VERBOSE_LEVELS[args.verbose]
        logging.basicConfig(level=level, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        if level != logging.CRITICAL:
            logger.log(level, 'this is the most verbose log level for this run')
        self.setup_module_logs(args)
        if args.pool:
            self.pool = self.load_pool(args)
        if args.pool and args.vdev_id == None:
            args.vdev_id = int(self.pool.first_vdev().id)
        args.func(args)


    def load_pool(self, args):
        # TODO: parse disk label to find other vdevs
        devices = [filedev.FileDev(path, args.label, args.txg) for path in args.pool]
        try_config = set(args.try_config).union(*TRY_LEVELS[:args.try_level+1])
        logger.info('extra options: {}'.format(try_config))
        pool = Pool(devices, try_config=try_config)
        return pool

    def list_cmd(self, args):
        target = self.pool.open(args.path)
        # logger.info(target.attrs)
        if isinstance(target, zfs.posix.File):
            print(args.path)
        else:
            for file in sorted(target.keys()):
                print(file)
                # print(file.decode('utf8'))

    def cat(self, args):
        sys.stdout.buffer.write(self.pool.read_file(args.path))

    def show_object(self, args, os, obj):
        if args.parse:
            try:
                pprint(os.parse_dnode(obj))
            except:
                logging.exception('parse error')
                print(obj)
        elif args.dnode:
            print(obj)
        elif args.dump:
            f = open(args.dump, 'wb')
            f.write(self.pool.read_dnode(obj))
            f.close()
        else:
            print(obj.node_type)
        if args.execute:
            try:
                parsed = os.parse_dnode(obj)
            except:
                parsed = None
            try:
                exec(args.execute, globals(), {'o':obj, 'os':os, 'p':parsed})
            except:
                logger.exception('execution failed on object {}'.format(obj.node_type))

    def objset(self, args):
        if args.dataset:
            ds = self.pool.dataset_for(args.dataset)
            os = ds.objectset
        else:
            os = self.pool.objset_for_vdev(args.vdev_id)

        if args.self:
            print(os.raw_objectset)
            if args.dump:
                f = open(args.dump, 'wb')
                print(len(os.objset))
                f.write(os.objset)
                f.close()
                return

        if not args.object:
            args.all = True
        if args.all:
            for i, obj in enumerate(os):
                if obj.node_type != ObjectType.NONE or args.everything:
                    if args.parse:
                        print('-'*30)
                    print(i, end=' ')
                    self.show_object(args, os, obj)
        elif args.object:
            obj = os.get_dnode(args.object)
            self.show_object(args, os, obj)

    def nvparse(self, args):
        source = open(args.file, 'rb')
        data = source.read()
        nv = NVList(data)
        pprint(nv.unpack_nvlist())

    def label(self, args):
        vdev = self.pool.vdevs[args.vdev_id]
        label = vdev.best_label
        if args.label is not None:
            label = vdev.labels[args.label]
            pprint(label[0])
        if args.uberblocks:
            for i, uber in enumerate(label[1]):
                if args.all or uber.valid():
                    print(i, uber)

    def mount_fuse(self, args):
        # TODO: allow per-dataset mounting, to match the semantics of the real implementation
        zfuse.mount(self.pool, args.mountpoint)

    def read_dva(self, args):
        dva = args.dva
        return NotImplemented

def cli(*args, **kwargs):
    px = PoolExplorer()
    return px.cli()

if __name__ == '__main__':
    cli()

