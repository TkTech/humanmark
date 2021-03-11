import dataclasses

try:
    import click
except ImportError:
    raise RuntimeError(
        'To use the humanmark CLI you need to install the optional'
        ' dependencies.\n'
        ' If you are using pip, do `pip install "humanmark[cli]"`.'
    )

from humanmark import loads, dumps
from humanmark.render import Renderer, available_renderers
from humanmark.backends import available_backends


def dynamic_command(expand_renderer=False, expand_backend=False):
    class DynamicCommand(click.Command):
        """A special ``click.Command`` subclass that generates
        ``click.Options`` for the selected renderer and backend."""
        def get_params(self, ctx):
            # get_params is undocumented, but I can't see a better way of
            # doing this. A decorator doesn't have access to the context, so
            # we don't know what renderer/backend to use. `make_parser` is
            # documented, but isn't even used by the --help command!
            params = super().get_params(ctx)
            # sphinx-click, which generates our CLI documentation, somehow
            # gets here without ever generating the context in the parent
            # group.
            ctx.ensure_object(dict)

            renderer: Renderer = ctx.obj.get('renderer')
            if expand_renderer and renderer:
                # A renderer was specified, so we want to parse out its options
                # dataclass and turn them into options.
                options = renderer.OPTIONS_CLASS
                fields = dataclasses.fields(options)
                for field in fields:
                    safe_field_name = field.name.replace('_', '-')
                    param_name = f'--r-{safe_field_name}'
                    if field.type is bool:
                        param_name = f'{param_name}/--no-r-{safe_field_name}'

                    params.append(
                        click.Option(
                            [param_name],
                            is_flag=field.type is bool,
                            type=field.type,
                            default=field.default,
                            help=f'Default is [{field.default!r}]'
                        )
                    )

            return params
    return DynamicCommand


@click.group()
@click.option(
    '--backend',
    type=click.Choice(list(available_backends().keys())),
    help='Specify the backend used to parse documents.',
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


@cli.command('render', cls=dynamic_command(expand_renderer=True))
@click.argument('source', type=click.File('rt'))
@click.pass_context
def render_command(ctx, source, **kwargs):
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
