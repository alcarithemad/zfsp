from pprint import pprint

import click

import zfs.posix
from zfs.posix import posix_file
from zfs import posix_file
from zfs.constants import ObjectType
from zfs.filedev import FileDev
from zfs.pool import Pool

pass_pool = click.make_pass_decorator(Pool)

@click.group()
@click.option('--pool', '-p',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
@click.option('--vdev-id', type=int, default=0)
@click.option('-v', '--verbose', count=True)
@click.pass_context
def cli(ctx, pool, vdev_id, verbose):
    first_dev = FileDev(pool)
    ctx.obj = Pool([first_dev])


@cli.command()
@click.argument('path', default='/')
@pass_pool
def ls(pool, path):
    try:
        target = pool.open(path)
        if isinstance(target, zfs.posix.File):
            click.echo(path)
        else:
            for name, obj in sorted(target.items()):
                if isinstance(obj, zfs.posix.File):
                    click.secho(name)
                else:
                    click.secho(name, fg='blue')
    except KeyError:
        click.echo('file not found')


@cli.command()
@click.argument('file')
@pass_pool
def cat(pool, file):
    click.echo(pool.read_file(file))


def show_object(args, os, obj):
    if args.should_parse == 'parse':
        try:
            pprint(os.parse_dnode(obj))
        except Exception, e:
            click.secho('parse error {}'.format(e), fg='red')
            click.secho('object: {}'.format(obj), fg='red')
    elif args.should_parse == 'raw':
        click.echo(obj)
    elif args.dump:
        args.dump.write(self.pool.read_dnode(obj))
        args.dump.close()
    else:
        click.echo(obj.node_type)
    if args.execute:
        try:
            parsed = os.parse_dnode(obj)
        except:
            parsed = None
        try:
            exec args.execute in globals(), {'o':obj, 'os':os, 'p':parsed}
        except:
            click.secho('execution failed on object {}'.format(obj.node_type), fg='red')

@cli.group()
@click.option('--dataset', '-d', help='Show the object set for DATASET. If not specified, show the meta object set.')
@click.option('--self', is_flag=True, help='Show extra info about the object set itself.')
@click.option('--dump', type=click.File('wb'), help='follow the object\'s block pointers and dump their contents to FILENAME.')
@click.option('--execute', '-e', metavar='EXPR', help='Execute EXPR with the object in scope as `o`.')
@click.option('--parse', '-P', 'should_parse', flag_value='parse', help='Show the parsed data, instead of the DNode.')
@click.option('--raw', '-R', 'should_parse', flag_value='raw', help='Show raw DNodes.')
# @click.argument('object', type=int, required=False)
@click.pass_context
def objset(ctx, **args):
    args = type('Namespace', (), args)
    args.pool = ctx.obj
    ctx.obj = args
    if args.dataset:
        ds = args.pool.dataset_for(args.dataset)
        args.objset = ds.objectset
    else:
        args.objset = args.pool.objset_for_vdev(0)

@objset.command('all')
@click.option('--everything', is_flag=True, help='Show all objects, even empty ones.')
@click.pass_obj
def show_all(args, everything):
    pool = args.pool
    args.everything = everything

    for i, obj in enumerate(args.objset.objset):
        if obj.node_type != ObjectType.NONE or args.everything:
            if args.should_parse == 'parse':
                click.echo('-'*30)
            click.echo('{} '.format(i), nl=False)
            show_object(args, args.objset, obj)

@objset.command('one')
@click.argument('object', type=int)
@click.pass_obj
def show_one(args, object):
    obj = args.objset.objset[object]
    show_object(args, args.objset, obj)

@objset.command('self')
@click.pass_obj
def show_self(args):
    click.echo(args.objset.raw_objectset)
