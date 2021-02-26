try:
    import click
except ImportError:
    raise RuntimeError(
        'To use the humanmark CLI you need to install the optional'
        ' dependencies.\n'
        ' If you are using pip, do `pip install "humanmark[cli]"`.'
    )

from humanmark import parser


@click.group()
def cli():
    """Utilities for working with markdown."""


@cli.command('tree')
@click.argument('source', type=click.File('rt'))
def tree(source):
    """Pretty-print a visual representation of a parsed markdown file's
    AST (abstract syntax tree)."""
    fragment = parser.parse(source.read())
    click.echo_via_pager(fragment.pretty())


if __name__ == '__main__':
    cli()
