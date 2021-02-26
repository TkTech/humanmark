from pathlib import Path

from click.testing import CliRunner

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
