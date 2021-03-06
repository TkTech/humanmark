import json
from pathlib import Path

from click.testing import CliRunner

from humanmark import ast
from humanmark.cli import cli


def test_tree_command(request):
    """Ensure the `humanmark tree <source>` command works as expected."""
    runner = CliRunner()
    result = runner.invoke(cli, [
        'tree',
        str(Path(request.fspath.dirname) / 'data' / 'hello_world.md')
    ])
    assert result.exit_code == 0
    assert len(result.output.split('\n')) == 7


def test_render_command(request):
    """Ensure the `humanmark render <source>` command works as expected."""
    runner = CliRunner()
    result = runner.invoke(cli, [
        '--renderer=json',
        'render',
        str(Path(request.fspath.dirname) / 'data' / 'hello_world.md')
    ])
    assert result.exit_code == 0
    assert json.loads(result.output) == ast.Fragment(
        children=[
            ast.Header(1, children=[
                ast.Text('Hello World!')
            ]),
            ast.Paragraph(children=[
                ast.Text('This is a minimal test document.')
            ])
        ]
    ).to_dict()
