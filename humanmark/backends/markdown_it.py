from collections import deque

from markdown_it import MarkdownIt
from markdown_it.token import Token

from humanmark import ast
from humanmark.backends import Backend


class MarkdownItBackend(Backend):
    """A markdown-it-py powered backend, parsing markdown documents
    and returning HumanMark AST nodes.

    This backend implements a visitor model. To customize how markdown-it
    tokens are converted to the AST, or to implement new types of tokens,
    make a subclass and implement a `visit_<token name>()` method. For example,
    to change all text tokens to uppercase:

    .. code:: python

        class UppercaseText(MarkdownItBackend):
            def visit_text(self, token):
                return ast.Text(token.content.upper())

    A node's children and line mappings are populated for you.
    """
    def parse(self, content: str) -> ast.Fragment:
        md = MarkdownIt().enable('strikethrough')

        # This option is undocumented. This stores the reference label for a
        # link in token.meta.label, instead of just discarding it. It is
        # mentioned in the changelog, so hopefully it won't disappear on us.
        md.options['store_labels'] = True

        # This was using nest_tokens(), but that was deprecated quite literally
        # a day after parse() was written. This new approach avoids recursion.
        top = ast.Fragment()
        token_it = [deque(md.parse(content))]

        while token_it:
            tokens = token_it[-1]
            try:
                token = tokens.popleft()
            except IndexError:
                if top.parent is None:
                    return top

                top = top.parent
                token_it.pop()

                continue

            m = getattr(self, f'visit_{token.type}')
            if not m:
                raise NotImplementedError(
                    f'Tokens of type {token.type!r} are not implemented.'
                )

            node = m(token)
            node.line_no = token.map[0] if token.map else None

            top.extend([node])

            if token.nesting == 0:
                if token.children:
                    token_it.append(deque(token.children))
                    top = node
                continue

            children = []
            nesting = token.nesting
            while nesting != 0:
                token = tokens.popleft()
                nesting += token.nesting
                if nesting != 0:
                    children.append(token)

            token_it.append(deque(children))
            top = node

    def visit_heading_open(self, token: Token) -> ast.Header:
        return ast.Header(level=int(token.tag.lstrip('h')))

    def visit_paragraph_open(self, token: Token) -> ast.Paragraph:
        return ast.Paragraph()

    def visit_inline(self, token: Token) -> ast.Fragment:
        # We don't have a concept of an "inline" container. Instead we
        # stick them into Fragments which will be optimized out later by
        # a call to `Node.tidy()`.
        return ast.Fragment()

    def visit_text(self, token: Token) -> ast.Text:
        return ast.Text(token.content)

    def visit_code_block(self, token: Token) -> ast.CodeBlock:
        return ast.CodeBlock(children=[ast.Text(token.content)])

    def visit_fence(self, token: Token) -> ast.CodeBlock:
        return ast.CodeBlock(
            fenced=True,
            fencechar=token.markup[0],
            infostring=token.info or None,
            children=[
                ast.Text(token.content)
            ]
        )

    def visit_blockquote_open(self, token: Token) -> ast.BlockQuote:
        return ast.BlockQuote()

    def visit_softbreak(self, token: Token) -> ast.SoftBreak:
        return ast.SoftBreak()

    def visit_hr(self, token: Token) -> ast.ThematicBreak:
        return ast.ThematicBreak(token.markup[0])

    def visit_bullet_list_open(self, token: Token) -> ast.List:
        return ast.List(start=token.attrGet('start'))

    def visit_ordered_list_open(self, token: Token) -> ast.List:
        return ast.List(start=token.attrGet('start'))

    def visit_list_item_open(self, token: Token) -> ast.ListItem:
        return ast.ListItem(bullet=token.markup)

    def visit_html_block(self, token: Token) -> ast.HTMLBlock:
        return ast.HTMLBlock(content=token.content)

    def visit_html_inline(self, token: Token) -> ast.HTMLInline:
        return ast.HTMLInline(content=token.content)

    def visit_code_inline(self, token: Token) -> ast.InlineCode:
        return ast.InlineCode(children=[ast.Text(token.content)])

    def visit_em_open(self, token: Token) -> ast.Emphasis:
        return ast.Emphasis()

    def visit_strong_open(self, token: Token) -> ast.Strong:
        return ast.Strong()

    def visit_s_open(self, token: Token) -> ast.Strike:
        return ast.Strike()

    def visit_link_open(self, token: Token) -> ast.Link:
        return ast.Link(
            token.attrGet('href'),
            title=token.attrGet('title'),
            reference=token.meta.get('label')
        )

    def visit_image(self, token: Token) -> ast.Image:
        return ast.Image(
            token.attrGet('src'),
            title=token.attrGet('title'),
            reference=token.meta.get('label')
        )
