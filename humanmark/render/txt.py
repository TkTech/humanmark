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
        for text in node.find(ast.Text, depth=-1):
            if self.opts.ignore_code_blocks:
                if text.contained_by(ast.CodeBlock):
                    continue

            if self.opts.ignore_inline_code:
                if text.contained_by(ast.InlineCode):
                    continue

            text = text.content
            if self.opts.strip_punctation:
                text = re.sub(r'[^\w\s]', ' ', text, re.UNICODE)

            text = text.strip()
            if text:
                output.append(text)

        return ' '.join(output)
