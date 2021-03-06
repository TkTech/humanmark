from humanmark import ast


class Backend:
    """
    Base class for all backends.

    A backend is used to map to and from a markdown parser/generator and
    the HumanMark AST.
    """
    def parse(self, content: str) -> ast.Fragment:
        raise NotImplementedError()
