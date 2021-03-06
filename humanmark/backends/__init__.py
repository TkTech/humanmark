import pkg_resources

from humanmark import ast


class Backend:
    """
    Base class for all backends.

    A backend is used to map to and from a markdown parser/generator and
    the HumanMark AST.
    """
    #: A short, one-line description of this backend. Used for command
    #: line help and error messages.
    DESCRIPTION = None

    def parse(self, content: str) -> ast.Fragment:
        raise NotImplementedError()


def available_backends():
    return {
        entry_point.name: entry_point.load()
        for entry_point
        in pkg_resources.iter_entry_points('humanmark.backends')
    }
