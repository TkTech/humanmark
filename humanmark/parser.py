from typing import Union, Iterator, Iterable

from markdown_it import MarkdownIt
from markdown_it.token import nest_tokens, Token, NestedTokens
from humanmark import ast

TokenStream = Iterable[Union[Token, NestedTokens]]


class TokenVisitor:
    """
    Utility class for visiting all the members of a markdown_it token
    stream.
    """

    def visit(self, tokens: TokenStream) -> Iterator[ast.Node]:
        """Convert a token stream to a AST :class:`~humanmark.ast.Node`,
        including all of its children, yielding each node.
        """
        for token in tokens:
            m = getattr(self, f'visit_{token.type}')
            if not m:
                raise NotImplementedError(
                    f'Tokens of type {token.type!r} are not implemented.'
                )

            yield m(token)

    def visit_heading_open(self, token):
        return ast.Header(
            level=int(token.tag.lstrip('h')),
            children=self.visit(token.children),
            line_no=token.map[0] if token.map else 0
        )

    def visit_paragraph_open(self, token):
        return ast.Paragraph(
            line_no=token.map[0] if token.map else 0,
            children=self.visit(token.children)
        )

    def visit_inline(self, token):
        return ast.Fragment(children=self.visit(token.children))

    def visit_text(self, token):
        return ast.Text(
            token.content,
            line_no=token.map[0] if token.map else 0
        )

    def visit_code_block(self, token):
        return ast.CodeBlock(children=[ast.Text(token.content)])

    def visit_fence(self, token):
        return ast.CodeBlock(
            fenced=True,
            fencechar=token.markup[0],
            infostring=token.info or None,
            children=[
                ast.Text(token.content)
            ]
        )

    def visit_blockquote_open(self, token):
        return ast.BlockQuote(children=self.visit(token.children))

    def visit_softbreak(self, token):
        return ast.SoftBreak()

    def visit_hr(self, token):
        return ast.ThematicBreak(token.markup[0])

    def visit_bullet_list_open(self, token):
        return ast.List(
            start=token.attrGet('start'),
            children=self.visit(token.children)
        )

    def visit_ordered_list_open(self, token):
        return ast.List(
            start=token.attrGet('start'),
            children=self.visit(token.children)
        )

    def visit_list_item_open(self, token):
        return ast.ListItem(
            bullet=token.markup,
            children=self.visit(token.children)
        )

    def visit_html_block(self, token):
        return ast.HTMLBlock(content=token.content)

    def visit_html_inline(self, token):
        return ast.HTMLInline(content=token.content)

    def visit_code_inline(self, token):
        return ast.InlineCode(content=token.content)

    def visit_em_open(self, token):
        return ast.Emphasis(children=self.visit(token.children))

    def visit_strong_open(self, token):
        return ast.Strong(children=self.visit(token.children))

    def visit_s_open(self, token):
        return ast.Strike(children=self.visit(token.children))

    def visit_link_open(self, token):
        return ast.Link(token.attrGet('href'))


def parse(content: str):
    """Parse markdown into an :class:`~humanmark.ast.Fragment`."""
    fragment = ast.Fragment()

    md = MarkdownIt().enable('strikethrough')

    fragment.extend(
        TokenVisitor().visit(
            nest_tokens(md.parse(content))
        )
    )

    fragment.tidy()
    fragment.fix_missing_locations()
    return fragment
