import io
import sys
import itertools
from typing import Iterator, Dict, Union, Sequence

from collections.abc import Iterable


class NodePath:
    __slots__ = ('path',)

    def __init__(self, path=None):
        self.path = path or []

    def __truediv__(self, other):
        self.path.append(other)
        return self

    def __getitem__(self, index):
        self.path.append(index)
        return self


class NodeMeta(type):
    def __truediv__(self, other):
        return NodePath([self, other])

    def __getitem__(self, index):
        return NodePath([self, index])


class Node(metaclass=NodeMeta):
    """The base class for all types of nodes in the AST.

    .. admonition:: Internals
        :class: note

        Internally, Node's are a doubly-linked list. This isn't terribly
        efficient in Python, but makes complex structure manipulation trivial.
        Since we're human-focused, this trade-off in favour of usability is
        well worth it.
    """
    __slots__ = ('parent', 'first', 'last', 'line_no', 'next', 'prev')

    def __init__(self, *, line_no=0, children=None):
        #: The first child in the node.
        self.first: 'Node' = None
        #: The last child in the node.
        self.last: 'Node' = None

        #: The parent of this node.
        self.parent: 'Node' = None
        #: The next sibling node.
        self.next: 'Node' = None
        #: The previous sibling node.
        self.prev: 'Node' = None

        #: The source line number, if known.
        self.line_no = line_no

        if children:
            self.extend(children)

    def pprint(self, *, indent='', file=sys.stdout, is_last=False,
               show_line_no=True):
        """Pretty-print this node and all of its children to a file-like
        object.

        :param indent: The indent to apply at the start of each line.
                       [default: '']
        :param file: IO object for output. [default: sys.stdout]
        :param is_last: True if this is the last child in a sequence.
                        [default: False]
        :param show_line_no: True if source line numbers should be shown.
                             [default: True]
        """
        fork = '\u251C'
        dash = '\u2500'
        end = '\u2514'
        pipe = '\u2502'

        if show_line_no:
            file.write(f'[{self.line_no or 0:04}]')
        file.write(f'{indent}{end if is_last else fork}{dash}')

        file.write(repr(self))
        file.write('\n')
        file.flush()

        child_count = len(self) - 1
        for i, child in enumerate(self):
            child.pprint(
                indent=f'{indent}{" " if is_last else pipe} ',
                file=file,
                is_last=child_count == i,
                show_line_no=show_line_no
            )

    def pretty(self, *, indent='', show_line_no=True):
        """Pretty-print this node and all of its children, returning the
        result as a string.

        :param indent: The indent to apply at the start of each line.
                       [default: '']
        :param show_line_no: True if source line numbers should be shown.
                             [default: True]
        """
        with io.StringIO() as out:
            self.pprint(indent=indent, show_line_no=show_line_no, file=out)
            return out.getvalue()

    def find(self, of_type=None, *, f=None, depth=None):
        """Find and yield child nodes that match all given filters.

        >>> fragment = Fragment(children=[Text('Hello World!')])
        >>> for text in fragment.find(Text):
        ...     print(text.content)

        :func:`find()` supports simple paths. For example, to get all the text
        under headers:

        >>> for text in fragment.find(Header / Text):
        ...     print(text.content)

        :func:`find()` supports slicing on paths, to skip items, get a range
        of items, or to get a specific index.

        >>> for list_item in fragment.find(List / ListItem[::2]):
        ...     print(list_item)

        :param of_type: A Node subclass to match to.
        :param f: Any callable object which will be given the node.
        :param depth: The maximum depth to search for matching children.
                      By default only immediate children are checked. Passing
                      a negative value will search with no limit.
        """
        if of_type is not None and isinstance(of_type, NodePath):
            results = [self]

            for path_component in of_type.path:
                results = list(itertools.chain.from_iterable(
                    result.find(
                        of_type=path_component,
                        f=f,
                        depth=depth
                    )
                    for result in results
                ))

            yield from results
            return

        for child in self:
            if depth is not None and depth != 0:
                yield from child.find(
                    of_type=of_type,
                    f=f,
                    depth=depth - 1
                )

            if of_type is not None and not isinstance(child, of_type):
                continue

            if f is not None and not f(child):
                continue

            yield child

    def find_one(self, *args, default=None, **kwargs):
        """Same as :func:`~Node.find()`, but returns only the first match,
        or `None` if no result was found.

        >>> fragment = Fragment(children=[Text('Hello World!')])
        >>> print(fragment.find_one(Text))

        :param of_type: A Node subclass to match to.
        :param f: Any callable object which will be given the node.
        :param depth: The maximum depth to search for matching children.
                      By default only immediate children are checked. Passing
                      a negative value will search with no limit.
        :param default: The value to return when no result is found.
                        [default: None]
        """
        try:
            return next(self.find(*args, **kwargs))
        except StopIteration:
            return default

    def extend(self, value) -> 'Node':
        """Append one or more nodes to this Node's list of children.

        :param value: An iterable of nodes. May also contain sub-iterables,
                      which will be recursively flattended.
        """
        for child in value:
            if isinstance(child, Node):
                if not self.is_allowed_child(child):
                    raise ValueError(
                        f'Nodes of type {self.of_type!r} do not allow '
                        f'children of type {child.of_type!r}.'
                    )

                if self.first is None:
                    self.first = child
                    self.last = child
                    child.parent = self
                else:
                    self.last >> child
            elif isinstance(child, Iterable):
                self.extend(child)
            else:
                raise ValueError(
                    f'Do not know how to handle a child ({child!r}).'
                )

        # Chainable
        return self

    def fix_missing_locations(self) -> 'Node':
        """Recursively populates line_no values on child nodes using the parent
        value."""
        for child in self:
            if not child.line_no:
                child.line_no = self.line_no
            child.fix_missing_locations()

        # Chainable
        return self

    def _re_eq(self, other) -> bool:
        # Recursive equality check. Used by the individual node's
        # implementations of __eq__ when they have children.
        if len(other) != len(self):
            return False

        other_children = iter(other)
        for i, own_child in enumerate(self):
            other_child = next(other_children)
            if other_child != own_child:
                return False

            if not other_child._re_eq(own_child):
                return False

        return True

    def is_allowed_child(self, child: 'Node') -> bool:
        """
        Returns `True` if `child` is allowed to be directly under this node.

        It may still be possible for the child to be indirectly under this
        node, such as wrapping an inline in a paragraph.

        Called by methods like `append()` and `extend()` to ensure the children
        being added are valid.

        :param child: The node to be checked.
        """
        return True

    def tidy(self) -> 'Node':
        """Removes some redundant markup.

        This:
            - Removes stray Fragment's under a container.
            - Removes empty Text nodes.
            - Merges adjacent Text nodes.
        """
        child = self.first
        while child is not None:
            child.tidy()
            next_child = child.next

            if (isinstance(child, Fragment) and self.is_container and
                    len(self) == 1):
                # If this child is a fragment and the only type under a
                # container, there's no point in it existing.
                self.first = child.first
                self.last = child.last
                for new_child in self:
                    new_child.parent = self

                break
            elif isinstance(child, Text) and not child.content:
                # Blank text nodes are often produced by markdown_it
                # around emphasis.
                child.unlink()
            elif isinstance(child, Text) and isinstance(child.prev, Text):
                # Adjacent text nodes should be merged.
                child.prev.content += child.content
                child.unlink()

            child = next_child

        # Chainable
        return self

    def remove(self, of_type=None, *, f=None, depth: int = None) -> 'Node':
        """Removes all nodes that match the given conditions.

        For example, to remove all the text nodes that contain the word
        'Mars':

        >>> fragment = Fragment(children=[
        ...     Text('Hello Earth!'),
        ...     Text('Hello Mars!'),
        ... ])
        >>> fragment.remove(Text, f=lambda n: 'Mars' in n.content)

        or to erase all inline HTML:

        >>> fragment.remove(HTMLInline)

        :param of_type: A Node subclass to match to.
        :param f: Any callable object which will be given the node.
                  If the callable returns `True`, the node will be deleted.
        :param depth: The maximum depth to search for matching children.
                      By default only immediate children are checked. Passing
                      a negative value will search with no limit.
        """
        matches = self.find(of_type=of_type, f=f, depth=depth)

        for match in matches:
            match.unlink()

        # Chainable
        return self

    def unlink(self) -> 'Node':
        """Remove this node from its parent.

        A node that has been unlinked is free to be moved to a new position in
        the tree or an entirely new tree.
        """
        if self.prev is not None:
            self.prev.next = self.next

        if self.next is not None:
            self.next.prev = self.prev

        if self.parent is not None:
            if self.parent.last is self:
                self.parent.last = self.prev

            if self.parent.first is self:
                self.parent.first = self.next

        self.parent = None
        self.next = None
        self.prev = None

        # Chainable
        return self

    def replace(self, replacement: 'Node') -> 'Node':
        """Replaces this node with ``replacement`` and unlinks it from its
        parent.
        """
        replacement.parent = self.parent

        if self.prev is not None:
            self.prev.next = replacement
            replacement.prev = self.prev

        if self.next is not None:
            self.next.prev = replacement
            replacement.next = self.next

        if self.parent is not None:
            if self.parent.last is self:
                self.parent.last = replacement

            if self.parent.first is self:
                self.parent.first = replacement

        self.parent = None
        self.next = None
        self.prev = None

        # Chainable
        return self

    def contained_by(self, of_type: Union['Node', Sequence['Node']]) -> bool:
        """
        Returns ``True`` if this node is contained by a node ``of_type``, not
        just as a direct parent but anywhere in the hierarchy.

        `of_type` may also be a list of types, in which case this method
        with return `True` if this node is contained by *any* of the given
        types.
        """
        node = self.parent
        while node:
            if isinstance(node, of_type):
                return True
            node = node.parent

        return False

    def prepend_sibling(self, other: 'Node') -> 'Node':
        """Inserts the node `other` before this node.

        As a shortcut, the `<<` operator can be used instead. For example,
        to insert a header before an existing paragraph:

        .. code:: python

            Paragraph(children=Text('Hello!') << Header(1)
        """
        if self.parent is None:
            raise ValueError(
                'Cannot prepend a node when this node does not have a parent.'
            )

        if self.prev is not None:
            self.prev.next = other
            other.prev = self.prev

        self.prev = other
        other.next = self
        other.parent = self.parent

        if self.parent.first is self:
            self.parent.first = other

        return self

    def append_sibling(self, other: 'Node') -> 'Node':
        """Inserts the node `other` after this node.

        As a shortcut, the `>>` operator can be used instead. For example,
        to add a paragraph after an existing header:

        .. code:: python

            Header(1) >> Paragraph(children=Text('Hello!')
        """
        if self.parent is None:
            raise ValueError(
                'Cannot append a node when this node does not have a parent.'
            )

        if self.next is not None:
            self.next.prev = other
            other.next = self.next

        self.next = other
        other.prev = self
        other.parent = self.parent

        if self.parent.last is self:
            self.parent.last = other

        return self

    __lshift__ = prepend_sibling
    __rshift__ = append_sibling

    def __iter__(self) -> Iterator['Node']:
        node = self.first
        while node is not None:
            yield node
            node = node.next

    def __reversed__(self) -> Iterator['Node']:
        node = self.last
        while node is not None:
            yield node
            node = node.prev

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}()>'

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and self._re_eq(other)

    def to_dict(self) -> Dict:
        """Recursively dump this node and all of its children to a dict."""
        return {
            'type': self.of_type,
            'children': [
                child.to_dict() for child in self
            ]
        }

    @property
    def of_type(self) -> str:
        return self.__class__.__name__.lower()

    @property
    def is_block(self) -> bool:
        raise NotImplementedError()

    @property
    def is_leaf(self) -> bool:
        raise NotImplementedError()

    @property
    def is_container(self) -> bool:
        raise NotImplementedError()


class Block(Node):
    """Mixin for block nodes."""
    @property
    def is_block(self):
        return True

    @property
    def is_leaf(self):
        raise NotImplementedError()

    @property
    def is_container(self):
        raise NotImplementedError()


class Container(Block):
    """Mixin for container block nodes."""
    @property
    def is_leaf(self):
        return False

    @property
    def is_container(self):
        return True


class Leaf(Block):
    """Mixin for leaf block nodes."""
    @property
    def is_leaf(self):
        return True

    @property
    def is_container(self):
        return False

    def is_allowed_child(self, child: Node) -> bool:
        return not child.is_block


class Inline(Node):
    """Mixin for inline nodes."""
    @property
    def is_block(self):
        return False

    @property
    def is_container(self):
        return False


class Fragment(Container):
    """A fragment of Markdown that serves no purpose in rendering. It simply
    acts as a container.
    """


class ThematicBreak(Leaf):
    def __init__(self, char: str, *, line_no=0, children=None):
        super().__init__(line_no=line_no, children=children)
        if char not in ('-', '_', '*'):
            raise ValueError('Thematic breaks must be one of -, _, or *.')

        self.char = char

    def __repr__(self):
        return f'<ThematicBreak({self.char!r})>'

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                other.char == self.char and
                self._re_eq(other))


class HTMLBlock(Leaf):
    def __init__(self, content: str, *, line_no=0, children=None):
        super().__init__(line_no=line_no, children=children)
        self.content = content

    def __repr__(self):
        return f'<HTMLBlock({len(self.content)} characters)>'

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                other.content == self.content and
                self._re_eq(other))

    def to_dict(self):
        return {
            **super().to_dict(),
            'content': self.content
        }


class HTMLInline(Inline):
    def __init__(self, content: str, *, line_no=0, children=None):
        super().__init__(line_no=line_no, children=children)
        self.content = content

    def __repr__(self):
        return f'<HTMLInline({len(self.content)} characters)>'

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                other.content == self.content and
                self._re_eq(other))

    def to_dict(self):
        return {
            **super().to_dict(),
            'content': self.content
        }


class Header(Container):
    def __init__(self, level: int, *, line_no=0, children=None):
        super().__init__(line_no=line_no, children=children)
        if level < 1 or level > 6:
            raise ValueError('Headers must be between levels 1 to 6.')

        self.level = level

    def __repr__(self):
        return f'<Header({self.level})>'

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                other.level == self.level and
                self._re_eq(other))

    def to_dict(self):
        return {
            **super().to_dict(),
            'level': self.level
        }


class Paragraph(Container):
    pass


class List(Container):
    def __init__(self, *, line_no=0, children=None, start=None):
        super().__init__(line_no=line_no, children=children)
        self.start = start

        if start is not None and not isinstance(start, int):
            raise ValueError('The starting index of a list must be a number.')

    def __repr__(self):
        return f'<List(start={self.start!r})>'

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                other.start == self.start and
                self._re_eq(other))

    def is_allowed_child(self, child: Node) -> bool:
        return isinstance(child, ListItem)

    def to_dict(self):
        return {
            **super().to_dict(),
            'start': self.start
        }


class ListItem(Container):
    def __init__(self, *, line_no=0, children=None, bullet: str = '-'):
        super().__init__(line_no=line_no, children=children)
        self.bullet = bullet

    def __repr__(self):
        return f'<ListItem({self.bullet!r})>'

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                other.bullet == self.bullet and
                self._re_eq(other))

    @property
    def is_bullet(self):
        return self.bullet != '.'

    @property
    def is_numbered(self):
        return self.bullet == '.'

    @property
    def bullet(self):
        return self._bullet

    @bullet.setter
    def bullet(self, value):
        # '.' is non-standard, and represents a numbered item.
        if value not in ('-', '+', '*', '.'):
            raise ValueError(
                'Bullet must be one of \'-\', \'+\', \'*\', or \'.\''
            )

        self._bullet = value

    def to_dict(self):
        return {
            **super().to_dict(),
            'bullet': self.bullet
        }


class BlockQuote(Container):
    pass


class CodeBlock(Container):
    """
    A block of code.

    If ``fenced`` is ``False``, the codeblock will be indented instead.

    :param infostring: Optional text that will follow the start of the fence.
                       Typically used to specify a syntax highlighting
                       language. [default: None]
    :param fenced: Should this code block be fenced or indented.
                   Defaults to True only if an infostring is provided.
                   [default: False]
    :param fencechar: The character to use for a fenced code block. Must be
                      one of '`' or '~'. [default: \\`]
    """
    def __init__(self, *, line_no=0, children=None, infostring=None,
                 fenced=None, fencechar='`'):
        super().__init__(line_no=line_no, children=children)
        self.infostring = infostring
        self.fenced = fenced if fenced is not None else bool(infostring)
        self.fencechar = fencechar

        if fencechar not in ('`', '~'):
            raise ValueError(
                'Only \'`\' or \'~\' are valid characters for fencing.'
            )

    def __repr__(self):
        return (
            f'<CodeBlock(fenced={self.fenced}, infostring={self.infostring!r},'
            f' fencechar={self.fencechar!r})>'
        )

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                other.infostring == self.infostring and
                other.fenced == self.fenced and
                other.fencechar == self.fencechar and
                self._re_eq(other))

    def to_dict(self):
        return {
            **super().to_dict(),
            'infostring': self.infostring,
            'fenced': self.fenced,
            'fencechar': self.fencechar
        }

    def is_allowed_child(self, child: Node) -> bool:
        return isinstance(child, Text)


class Text(Inline):
    def __init__(self, content: str, *, line_no=0, children=None):
        super().__init__(line_no=line_no, children=children)

        if children:
            raise ValueError('A text node must not have children.')

        self.content = content

    def __repr__(self):
        return f'<Text({self.content!r})>'

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                other.content == self.content)

    def to_dict(self):
        return {
            'type': self.of_type,
            'content': self.content
        }

    def is_allowed_child(self, child: Node) -> bool:
        return False


class Strong(Inline):
    pass


class Emphasis(Inline):
    pass


class Strike(Inline):
    pass


class Link(Inline):
    """
    A container for a hyperlink.

    If a reference is provided, it will be used when emitting a link instead of
    the full URL, with the actual URL being emitted elsewhere. In a markdown
    document, these references would typically end up at the bottom of the
    document.

    If the url and the text are identical, the link is assumed to be an
    autolink.

    :param url: The relative or absolute URL to target.
    :param reference: A reference label to emit instead of the full URL.

    .. _autolink: https://github.github.com/gfm/#autolinks
    """
    def __init__(self, url: str, reference=None, title=None, *, line_no=0,
                 children=None):
        super().__init__(line_no=line_no, children=children)
        self.url = url
        self.reference = reference
        self.title = title

    def __repr__(self):
        return (
            f'<Link({self.url!r}, reference={self.reference!r},'
            f' title={self.title!r})>'
        )

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                other.url == self.url and
                other.title == self.title and
                other.reference == self.reference and
                self._re_eq(other))

    def to_dict(self):
        return {
            **super().to_dict(),
            'url': self.url,
            'title': self.title,
            'reference': self.reference
        }

    @property
    def is_autolink(self):
        """`True` if this link should be rendered as an autolink."""
        text = self.find_one(Text)
        return text is not None and self.url == text.content


class Image(Inline):
    """
    A container for an image.

    If a reference is provided, it will be used when emitting a link instead of
    the full URL, with the actual URL being emitted elsewhere. In a markdown
    document, these references would typically end up at the bottom of the
    document.

    :param url: The relative or absolute URL to target.
    :param title: A title for the image.
    :param reference: A reference label to emit instead of the full URL.
    """
    def __init__(self, url: str, title=None, reference=None, *, line_no=0,
                 children=None):
        super().__init__(line_no=line_no, children=children)
        self.url = url
        self.title = title
        self.reference = reference

    def __repr__(self):
        return (
            f'<Image({self.url!r}, reference={self.reference!r},'
            f' title={self.title!r})>'
        )

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                other.url == self.url and
                other.title == self.title and
                other.reference == self.reference and
                self._re_eq(other))

    def to_dict(self):
        return {
            **super().to_dict(),
            'url': self.url,
            'title': self.title,
            'reference': self.reference
        }


class InlineCode(Inline):
    pass


class SoftBreak(Inline):
    """In markdown, a softbreak represents a literal newline (``\\n``).

    Various rendering formats may discard a SoftBreak if it will have no
    impact on the final result, such as in HTML.
    """
