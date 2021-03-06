import pkg_resources

from humanmark import ast


class Renderer:
    #: A dataclass that is used to pass options into the renderer. This
    #: dataclass is used to generate command line options.
    OPTIONS_CLASS = None
    #: A short, one-line description of this renderer. Used for command
    #: line help and error messages.
    DESCRIPTION = None

    def __init__(self, *, options=None):
        self.opts = self.OPTIONS_CLASS(**(options or {}))

    def render(self, node: ast.Node) -> str:
        raise NotImplementedError()


def available_renderers():
    return {
        entry_point.name: entry_point.load()
        for entry_point
        in pkg_resources.iter_entry_points('humanmark.renderers')
    }
