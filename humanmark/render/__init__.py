from humanmark import ast


class Renderer:
    def __init__(self, *, options=None):
        self.opts = self.options_class(**(options or {}))

    @property
    def options_class(self):
        raise NotImplementedError()

    def render(self, node: ast.Node) -> str:
        raise NotImplementedError()
