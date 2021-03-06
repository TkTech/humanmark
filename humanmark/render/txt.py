import re
from dataclasses import dataclass

from humanmark import ast
from humanmark.render import Renderer


@dataclass
class Options:
    #: Don't output the contents of code blocks.
    ignore_code_blocks: bool = True
    #: Don't output the contents of inline code.
    ignore_inline_code: bool = True
    #: Strip punctuation from the result.
    strip_punctation: bool = True


class TXTRenderer(Renderer):
    """
    Renders just the text nodes of a HumanMark AST. This is useful to use
    markdown documents for machine learning training.
    """
    OPTIONS_CLASS = Options
    DESCRIPTION = 'Renders just the text of a document.'

    def render(self, node: ast.Node) -> str:
        output = []
        types_to_skip = []

        if self.opts.ignore_code_blocks:
            types_to_skip.append(ast.CodeBlock)

        if self.opts.ignore_inline_code:
            types_to_skip.append(ast.InlineCode)

        types_to_skip = tuple(types_to_skip)

        for text in node.find(ast.Text, depth=-1):
            if types_to_skip and text.contained_by(types_to_skip):
                continue

            text = text.content
            if self.opts.strip_punctation:
                text = re.sub(r'[^\w\s]', ' ', text, re.UNICODE)

            text = text.strip()
            if text:
                output.append(text)

        return ' '.join(output)
