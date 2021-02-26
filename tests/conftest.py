import difflib

from humanmark.ast import Node


def pytest_assertrepr_compare(config, op, left, right):
    if isinstance(left, Node) and isinstance(right, Node) and op == '==':
        # Just a bit better than nothing. Shows a diff between two pretty
        # printed nodes. We could make this much better with a bit of
        # effort.
        return [
            'Nodes are not equal:',
            *difflib.unified_diff(
                left.pretty(show_line_no=False).split('\n'),
                right.pretty(show_line_no=False).split('\n'),
                fromfile='left',
                tofile='right',
                lineterm=''
            )
        ]
