import json
from dataclasses import dataclass

from humanmark import ast
from humanmark.render import Renderer


@dataclass
class Options:
    #: ``True`` to render the document with indentation.
    pretty_print: bool = True


class JSONRenderer(Renderer):
    """
    Renders a HumanMark AST as JSON.
    """
    OPTIONS_CLASS = Options
    DESCRIPTION = 'Renders to a JSON document.'

    def render(self, node: ast.Node) -> str:
        return json.dumps(
            node.to_dict(),
            indent=4 if self.opts.pretty_print else 0
        )
