import pytest

from humanmark import ast


def test_list_items_only():
    """Ensure a List's direct children can only be ListItems."""
    ast.List(children=[
        ast.ListItem(children=[
            ast.Text('valid child')
        ])
    ])

    with pytest.raises(ValueError):
        ast.List(children=[
            ast.Text('invalid child')
        ])
