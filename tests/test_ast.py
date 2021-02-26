"""Tests the basic functionality common to all AST Nodes."""
import pytest

from humanmark import ast


@pytest.fixture
def fragment():
    return ast.Fragment(children=[
        ast.Text('Hello Earth!'),
        ast.Paragraph(children=[
            ast.Text('Hello Mars!')
        ])
    ])


def test_tidy_fragments():
    """Ensure uncessary fragments are removed by tidy."""
    fragment = ast.Paragraph(children=[
        ast.Fragment(children=[
            ast.Text('test')
        ])
    ]).tidy()

    assert fragment == ast.Paragraph(children=[
        ast.Text('test')
    ])


def test_tidy_text():
    """Ensure uncessary text nodes are removed by tidy."""
    fragment = ast.Fragment(children=[
        ast.Text('ab'),
        ast.Text('c'),
        ast.Text(''),
        ast.Text('d')
    ]).tidy()

    assert fragment == ast.Fragment(children=[
        ast.Text('abcd')
    ])


def test_text_children():
    """Ensure Text nodes cannot have children."""
    with pytest.raises(ValueError):
        ast.Text('parent', children=[
            ast.Text('invalid child')
        ])


def test_find(fragment):
    """Ensure find() and find_one() return expected results."""
    # Find, with a depth of 0 by default.
    result = list(fragment.find(ast.Text))
    assert result == [ast.Text('Hello Earth!')]

    # Find, with unrestricted depth.
    result = list(fragment.find(ast.Text, depth=-1))
    assert result == [ast.Text('Hello Earth!'), ast.Text('Hello Mars!')]

    result = list(fragment.find(
        ast.Text,
        depth=-1,
        f=lambda n: 'Mars' in n.content
    ))
    assert result == [ast.Text('Hello Mars!')]

    result = fragment.find_one(ast.Text, depth=-1)
    assert result == ast.Text('Hello Earth!')

    result = fragment.find_one(ast.Header)
    assert result is None


def test_extend():
    """Ensure we can grow a node's children."""
    fragment = ast.Fragment()

    # Simple iterable.
    fragment.extend([
        ast.Text('Hello!')
    ])
    assert len(fragment) == 1

    # Iterables within iterables.
    fragment.extend([
        (ast.Text(word) for word in ('Hello', 'World!'))
    ])
    assert len(fragment) == 3

    # Unknown children types.
    with pytest.raises(ValueError):
        fragment.extend([1])


def test_iterable(fragment):
    """Ensure we can iterate over a node."""
    assert len(list(fragment)) == 2


def test_iadd(fragment):
    """Ensure += operator works."""
    fragment += ast.Text('Hello Venus!')
    result = fragment.find_one(ast.Text, f=lambda n: 'Venus' in n.content)
    assert result is not None


def test_getitem(fragment):
    """Ensure shortcut for getting children with __getitem__/[] works."""
    p = fragment.find_one(ast.Paragraph)
    assert p[ast.Text] is not None
    assert p['text'] is not None
