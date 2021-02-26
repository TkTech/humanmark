"""
.. _autolink: https://github.github.com/gfm/#autolinks
"""
import io
import sys
from typing import (
    List as ListType,
    Iterable as IterableType
)
from collections.abc import Iterable
from collections import namedtuple


Event = namedtuple('Event', [
    'entering',
    'node',
    'depth'
])


class Node:
    __slots__ = ('parent', 'children', 'line_no', 'next', 'prev')

    def __init__(self, *, line_no=0, children=None):
        #: List of children for this Node.
        self.children: ListType[Node] = []
        #: The parent node.
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

        child_count = len(self.children) - 1
        for i, child in enumerate(self.children):
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

        :param of_type: A Node subclass to match to.
        :param f: Any callable object which will be given the node.
        :param depth: The maximum depth to search for matching children.
                      By default only immediate children are checked. Passing
                      a negative value will search with no limit.
        """
        for child in self.children:
            if depth is not None and depth != 0:
                yield from child.find(
                    of_type=of_type,
                    f=f,
                    depth=depth - 1
                )

            if of_type is not None:
                if not isinstance(child, of_type):
                    continue

            if f is not None:
                if not f(child):
                    continue

            yield child

    def find_one(self, *args, default=None, **kwargs):
        """Same as :method:`~Node.find()`, but returns only the first match,
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

    def append(self, value):
        self.extend([value])

    def extend(self, value, *, starting_pos=None) -> int:
        for child in value:
            if isinstance(child, Node):
                if not self.is_allowed_child(child):
                    raise ValueError(
                        f'Nodes of type {self.of_type!r} do not allow '
                        f'children of type {child.of_type!r}.'
                    )

                if self.children:
                    last_child = self.children[-1]
                    last_child.next = child
                    child.prev = last_child

                child.parent = self
                self.children.append(child)
            elif isinstance(child, Iterable):
                self.extend(child, starting_pos=starting_pos)
            else:
                raise ValueError(
                    f'Do not know how to handle a child ({child!r}).'
                )

    def __iter__(self):
        yield from self.children

    def __repr__(self):
        return f'<{self.__class__.__name__}()>'

    def __iadd__(self, value: 'Node'):
        self.extend([value])
        return self

    def __getitem__(self, value) -> 'Node':
        if isinstance(value, str):
            return self.find_one(f=lambda n: n.of_type == value)
        else:
            return self.find_one(value)

    def __len__(self) -> int:
        return len(self.children)

    def fix_missing_locations(self):
        """Recursively populates line_no values on child nodes using the parent
        value."""
        for child in self.children:
            if not child.line_no:
                child.line_no = self.line_no
            child.fix_missing_locations()

    def _re_eq(self, other) -> bool:
        # Recursive equality check. Used by the individual node's
        # implementations of __eq__ when they have children.
        if len(other.children) != len(self.children):
            return False

        for i, own_child in enumerate(self.children):
            if other.children[i] != own_child:
                return False

            if not other.children[i]._re_eq(own_child):
                return False

        return True

    def walk(self, *, depth=0) -> IterableType[Event]:
        for child in self.children:
            if child.children:
                yield Event(True, child, depth)
                if child.is_container:
                    depth += 1
                yield from child.walk(depth=depth)
                if child.is_container:
                    depth -= 1
            yield Event(False, child, depth)

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

    def tidy(self):
        """Remove redundant markup.

        This cleans up:
            - solitary Fragment's under a container.
            - Empty text nodes.
            - Adjacent text nodes.
        """
        new_children = []

        while self.children:
            child = self.children.pop(0)
            child.tidy()

            if (child.of_type == 'fragment' and self.is_container and
                    not new_children and not self.children):
                # If this child is a fragment and the only type under a
                # container, there's no point in it existing.
                new_children = child.children
                break
            elif child.of_type == 'text':
                if not child.content:
                    # Blank text nodes are often produced by markdown_it
                    # around emphasis.
                    continue
                elif new_children and new_children[-1].of_type == 'text':
                    # Adjacent text nodes should be merged.
                    new_children[-1].content += child.content
                    continue

            new_children.append(child)

        del self.children[:]
        # Extend will fix the next/prev pointers.
        self.extend(new_children)
        return self


class Block(Node):
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
    @property
    def is_leaf(self):
        return False

    @property
    def is_container(self):
        return True


class Leaf(Block):
    @property
    def is_leaf(self):
        return True

    @property
    def is_container(self):
        return False

    def is_allowed_child(self, child: Node) -> bool:
        return not child.is_block


class Inline(Node):
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
    def __eq__(self, other):
        return other.of_type == self.of_type and self._re_eq(other)


class ThematicBreak(Leaf):
    def __init__(self, char: str, *, line_no=0, children=None):
        super().__init__(line_no=line_no, children=children)
        if char not in ('-', '_', '*'):
            raise ValueError('Thematic breaks must be one of -, _, or *.')

        self.char = char

    def __repr__(self):
        return f'<ThematicBreak({self.char!r})>'

    def __eq__(self, other):
        return (other.of_type == self.of_type and
                other.char == self.char and
                self._re_eq(other))


class HTMLBlock(Leaf):
    def __init__(self, content: str, *, line_no=0, children=None):
        super().__init__(line_no=line_no, children=children)
        self.content = content

    def __repr__(self):
        return f'<HTMLBlock({len(self.content)} characters)>'

    def __eq__(self, other):
        return (other.of_type == self.of_type and
                other.content == self.content and
                self._re_eq(other))


class HTMLInline(Inline):
    def __init__(self, content: str, *, line_no=0, children=None):
        super().__init__(line_no=line_no, children=children)
        self.content = content

    def __repr__(self):
        return f'<HTMLInline({len(self.content)} characters)>'

    def __eq__(self, other):
        return (other.of_type == self.of_type and
                other.content == self.content and
                self._re_eq(other))


class Header(Container):
    def __init__(self, level: int, *, line_no=0, children=None):
        super().__init__(line_no=line_no, children=children)
        if level < 1 or level > 6:
            raise ValueError('Headers must be between levels 1 to 6.')

        self.level = level

    def __repr__(self):
        return f'<Header({self.level})>'

    def __eq__(self, other):
        return (other.of_type == self.of_type and
                other.level == self.level and
                self._re_eq(other))


class Paragraph(Container):
    def __eq__(self, other):
        return other.of_type == self.of_type and self._re_eq(other)


class List(Container):
    def __init__(self, *, line_no=0, children=None, start=None):
        super().__init__(line_no=line_no, children=children)
        self.start = start

        if start is not None and not isinstance(start, int):
            raise ValueError('The starting index of a list must be a number.')

    def __repr__(self):
        return f'<List(start={self.start!r})>'

    def __eq__(self, other):
        return (other.of_type == self.of_type and
                other.start == self.start and
                self._re_eq(other))

    def is_allowed_child(self, child: Node) -> bool:
        return isinstance(child, ListItem)


class ListItem(Container):
    def __init__(self, *, line_no=0, children=None, bullet: str = '-'):
        super().__init__(line_no=line_no, children=children)
        self.bullet = bullet

    def __repr__(self):
        return f'<ListItem({self.bullet!r})>'

    def __eq__(self, other):
        return (other.of_type == self.of_type and
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


class BlockQuote(Container):
    def __eq__(self, other):
        return other.of_type == self.of_type and self._re_eq(other)


class CodeBlock(Container):
    """
    A block of code.

    If `fenced` is `False`, the codeblock will be indented instead.

    :param infostring: Optional text that will follow the start of the fence.
                       Typically used to specify a syntax highlighting
                       language. [default: None]
    :param fenced: Should this code block be fenced (ex: '```') or indented.
                   Defaults to True only if an infostring is provided.
    :param fencechar: The character to use for a fenced code block. Must be
                      one of '`' or '~'. [default: `]
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
        return (other.of_type == self.of_type and
                other.infostring == self.infostring and
                other.fenced == self.fenced and
                other.fencechar == self.fencechar and
                self._re_eq(other))

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
        return (other.of_type == self.of_type and
                other.content == self.content and
                self._re_eq(other))

    def is_allowed_child(self, child: Node) -> bool:
        return False


class Strong(Inline):
    def __eq__(self, other):
        return other.of_type == self.of_type and self._re_eq(other)


class Emphasis(Inline):
    def __eq__(self, other):
        return other.of_type == self.of_type and self._re_eq(other)


class Strike(Inline):
    def __eq__(self, other):
        return other.of_type == self.of_type and self._re_eq(other)


class Link(Inline):
    """
    A container for a hyperlink.

    If a reference is provided, it will be used when emitting a link instead of
    the full URl, with the actual URL being emitted elsewhere. In a markdown
    document, these references would typically end up at the bottom of the
    document.

    If `reference` is `None` *and* there's no Text node under the link, it's
    assumed to be an `autolink`_.

    :param url: The relative or absolute URL to target.
    :param reference: A reference label to emit instead of the full URL.
    """
    def __init__(self, url: str, reference=None, *, line_no=0, children=None):
        super().__init__(line_no=line_no, children=children)
        self.url = url
        self.reference = reference

    def __repr__(self):
        return f'<Link({self.url!r}, reference={self.reference!r})>'

    def __eq__(self, other):
        return (other.of_type == self.of_type and
                other.url == self.url and
                other.reference == self.reference and
                self._re_eq(other))


class InlineCode(Inline):
    def __init__(self, content: str, *, line_no=0, children=None):
        super().__init__(line_no=line_no, children=children)
        self.content = content

    def __repr__(self):
        return f'<InlineCode({self.content!r})>'

    def __eq__(self, other):
        return (other.of_type == self.of_type and
                other.content == self.content and
                self._re_eq(other))


class Image(Inline):
    pass


class SoftBreak(Inline):
    def __eq__(self, other):
        return other.of_type == self.of_type
