from typing import TextIO

from humanmark.backends.markdown_it import MarkdownItBackend
from humanmark.render.markdown import MarkdownRenderer
from humanmark.ast import (
    Node,
    Fragment,
    ThematicBreak,
    HTMLBlock,
    HTMLInline,
    Header,
    Paragraph,
    List,
    ListItem,
    BlockQuote,
    CodeBlock,
    Text,
    Strong,
    Emphasis,
    Strike,
    Link,
    InlineCode,
    Image,
    SoftBreak
)

# Shaddup *all* the linters complaining about unused imports.
_ALL_IMPORTS = [
    Node,
    Fragment,
    ThematicBreak,
    HTMLBlock,
    HTMLInline,
    Header,
    Paragraph,
    List,
    ListItem,
    BlockQuote,
    CodeBlock,
    Text,
    Strong,
    Emphasis,
    Strike,
    Link,
    InlineCode,
    Image,
    SoftBreak
]


def load(f: TextIO, *, backend=None) -> Fragment:
    """Parse a markdown file into a :class:`~humanmark.ast.Fragment`.

    >>> from humanmark import parse
    >>> with open('README.md', 'rt') as source:
    ...     fragment = load(source)

    :param f: Any file-like object providing `read()`.
    :param backend: The Markdown backend to use to parse this document.
                    [default: markdown-it-py]
    """
    return loads(f.read(), backend=backend)


def loads(content: str, *, backend=None) -> Fragment:
    """Parse a markdown string into a :class:`~humanmark.ast.Fragment`.

    >>> from humanmark import parse
    >>> loads('# This is a header!').pprint()
    [0000]├─<Fragment()>
    [0000]│ └─<Header(1)>
    [0000]│   └─<Text('This is a header!')>

    :param content: A valid markdown document to be parsed.
    :param backend: The Markdown backend to use to parse this document.
                    [default: markdown-it-py]
    """
    if backend is None:
        backend = MarkdownItBackend()

    fragment = backend.parse(content)
    fragment.tidy()
    fragment.fix_missing_locations()
    return fragment


def dump(node: Node, f: TextIO, *, renderer=None):
    """Renders a HumanMark AST `node` to the file-like object `f`.

    :param renderer: An optional renderer to use instead of the default
                     MarkdownRender.
    """
    mk = renderer or MarkdownRenderer()
    f.write(mk.render(node))


def dumps(node: Node, *, renderer=None) -> str:
    """Renders a HumanMark AST `node` to a string and returns it.

    :param renderer: An optional renderer to use instead of the default
                     MarkdownRender.
    """
    mk = renderer or MarkdownRenderer()
    return mk.render(node)
