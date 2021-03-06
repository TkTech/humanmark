from dataclasses import dataclass
from typing import Iterator

from humanmark import ast
from humanmark.render import Renderer


@dataclass
class Options:
    """
    The configuration that can be passed into a MarkdownRenderer.
    """
    #: `0` to disable wrapping, otherwise the number of characters to allow
    #: per line.
    wrap: int = 0
    #: `True` if words should be broken when wrapping.
    wrap_break: bool = True


class MarkdownRenderer(Renderer):
    """
    Renders a HumanMark AST as Markdown.
    """
    OPTIONS_CLASS = Options
    DESCRIPTION = 'Renders to a Markdown document.'

    def render(self, node: ast.Node) -> str:
        return self.render_ex(node, joined_by='\n\n')

    def render_ex(self, node: ast.Node, *, joined_by='') -> str:
        content = []

        for child in node:
            m = getattr(self, f'visit_{child.of_type}')

            for chunk in m(child):
                content.append(chunk)

        return joined_by.join(content)

    def visit_fragment(self, node: ast.Fragment) -> Iterator[str]:
        yield from (self.render_ex(child) for child in node)

    def visit_text(self, node: ast.Text) -> Iterator[str]:
        yield node.content

    def visit_paragraph(self, node: ast.Paragraph) -> Iterator[str]:
        yield f'{self.render_ex(node)}'

    def visit_header(self, node: ast.Header) -> Iterator[str]:
        yield f'{"#" * node.level} {self.render_ex(node)}'

    def visit_blockquote(self, node: ast.BlockQuote) -> Iterator[str]:
        lines = self.render_ex(node, joined_by='\n').splitlines()
        if not lines:
            yield '>'
        else:
            yield '\n'.join(f'> {line}' for line in lines)

    def visit_emphasis(self, node: ast.Emphasis) -> Iterator[str]:
        yield f'*{self.render_ex(node)}*'

    def visit_strong(self, node: ast.Strong) -> Iterator[str]:
        yield f'**{self.render_ex(node)}**'

    def visit_strike(self, node: ast.Strike) -> Iterator[str]:
        yield f'~~{self.render_ex(node)}~~'

    def visit_softbreak(self, node: ast.SoftBreak) -> Iterator[str]:
        yield '\n'

    def visit_thematicbreak(self, node: ast.ThematicBreak) -> Iterator[str]:
        yield '---'

    def visit_link(self, node: ast.Link) -> Iterator[str]:
        if node.is_autolink:
            yield f'<{node.url}>'
        elif node.reference is not None:
            yield f'[{self.render_ex(node)}][{node.reference}]'
        else:
            title = f' {node.title!r}' if node.title else ''
            yield f'[{self.render_ex(node)}]({node.url}{title})'

    def visit_list(self, node: ast.List) -> Iterator[str]:
        out = []
        for i, item in enumerate(node, node.start or 1):
            bullet = item.bullet
            if not item.is_bullet:
                bullet = f'{i}.'

            prefix = ' ' * (len(bullet) + 1)

            lines = iter(self.render_ex(item, joined_by='\n').splitlines())
            try:
                out.append(f'{bullet} {next(lines)}')
            except StopIteration:
                continue

            for line in lines:
                out.append(f'{prefix}{line}')

        yield '\n'.join(out)

    def visit_inlinecode(self, node: ast.InlineCode) -> Iterator[str]:
        yield f'`{self.render_ex(node)}`'

    def visit_codeblock(self, node: ast.CodeBlock) -> Iterator[str]:
        content = node.find_one(ast.Text).content
        # Some backends (like markdown-it-py) include a final newline before
        # the end of a fenced block. Others don't.
        newline_on_content = '' if content.endswith('\n') else '\n'

        if node.fenced is True or node.infostring:
            yield (
                f'{node.fencechar * 3}{node.infostring or ""}\n'
                f'{content}{newline_on_content}'
                f'{node.fencechar * 3}'
            )
        else:
            yield '\n'.join(f'    {line}' for line in content.splitlines())

    def visit_image(self, node: ast.Image) -> Iterator[str]:
        if node.reference is not None:
            yield f'![{self.render_ex(node)}][{node.reference}]'
        else:
            title = f' {node.title!r}' if node.title else ''
            yield f'![{self.render_ex(node)}]({node.url}{title})'
