try:
    import click
except ImportError:
    raise RuntimeError(
        'To use the humanmark CLI you need to install the optional'
        ' dependencies.\n'
        ' If you are using pip, do `pip install "humanmark[cli]"`.'
    )

from humanmark import loads, dumps
from humanmark.render import available_renderers
from humanmark.backends import available_backends


@click.group()
@click.option(
    '--backend',
    type=click.Choice(list(available_backends().keys())),
    help='Specify the backend used to parse markdown.',
    default='markdown_it'
)
@click.option(
    '--renderer',
    type=click.Choice(list(available_renderers().keys())),
    help='Specify the renderer used to render the AST.',
    default='markdown'
)
@click.pass_context
def cli(ctx, backend, renderer):
    """Utilities for working with markdown."""
    ctx.ensure_object(dict)
    ctx.obj['backend'] = available_backends()[backend]
    ctx.obj['renderer'] = available_renderers()[renderer]


@cli.command('render')
@click.argument('source', type=click.File('rt'))
@click.pass_context
def render_command(ctx, source):
    """Parse and render `source`."""
    backend = ctx.obj['backend']()
    renderer = ctx.obj['renderer']()

    fragment = loads(source.read(), backend=backend)
    click.echo(dumps(fragment, renderer=renderer))


@cli.command('tree')
@click.argument('source', type=click.File('rt'))
@click.pass_context
def tree(ctx, source):
    """Pretty-print a visual representation of a parsed markdown file's
    AST (abstract syntax tree)."""
    backend = ctx.obj['backend']()
    fragment = loads(source.read(), backend=backend)
    click.echo(fragment.pretty())


if __name__ == '__main__':
    cli()
