from humanmark import loads, ast


def test_block_tokens_to_ast():
    """Ensures every block can be converted to our AST."""
    fragment = loads(
        # ATX header.
        '# Hello World!\n'
        # Block-level code.
        '\n    this is a block of code\n'
        # Fenced code block.
        '\n```python\n'
        'print("Hello World!")\n'
        '```\n'
        # Blockquote + softbreak
        '> This is a blockquote that spans multiple\n'
        '  lines.\n'
        # continuedd Blockquote.
        '> # continuation with a header\n'
        # Thematic break
        '----\n'
        # ListItems
        '- One\n'
        '- Two\n'
        '2. Three\n'
        '5. Four\n\n'
        # Setex Header
        'Header\n'
        '======\n'
        # HTML (block)
        '<p>testing</p>\n'
    )

    assert ast.Fragment(children=[
        ast.Header(1, children=[
            ast.Text('Hello World!')
        ]),
        ast.CodeBlock(children=[
            ast.Text('this is a block of code\n')
        ]),
        ast.CodeBlock(
            fenced=True,
            infostring='python',
            fencechar='`',
            children=[
                ast.Text('print("Hello World!")\n')
            ]
        ),
        ast.BlockQuote(children=[
            ast.Paragraph(children=[
                ast.Text('This is a blockquote that spans multiple'),
                ast.SoftBreak(),
                ast.Text('lines.')
            ]),
            ast.Header(1, children=[
                ast.Text('continuation with a header')
            ])
        ]),
        ast.ThematicBreak('-'),
        ast.List(children=[
            ast.ListItem(bullet='-', children=[
                ast.Paragraph(children=[
                    ast.Text('One')
                ])
            ]),
            ast.ListItem(bullet='-', children=[
                ast.Paragraph(children=[
                    ast.Text('Two')
                ])
            ])
        ]),
        ast.List(start=2, children=[
            ast.ListItem(bullet='.', children=[
                ast.Paragraph(children=[
                    ast.Text('Three')
                ])
            ]),
            ast.ListItem(bullet='.', children=[
                ast.Paragraph(children=[
                    ast.Text('Four')
                ])
            ])
        ]),
        ast.Header(1, children=[
            ast.Text('Header')
        ]),
        ast.HTMLBlock(content='<p>testing</p>\n')
    ]) == fragment


def test_inline_tokens_to_ast():
    """Ensures every inline can be converted to our AST."""

    pairs = (
        ('simple text', ast.Text('simple text')),
        ('`inline code`', ast.InlineCode(children=[
            ast.Text('inline code')
        ])),
        ('~~strike~~', ast.Strike(children=[ast.Text('strike')])),
        ('*emphasis*', ast.Emphasis(children=[ast.Text('emphasis')])),
        ('**strong**', ast.Strong(children=[ast.Text('strong')])),
        ('<http://tkte.ch>', ast.Link('http://tkte.ch', children=[
            ast.Text('http://tkte.ch')
        ])),
        ('[tkte.ch](https://tkte.ch)', ast.Link(
            'https://tkte.ch',
            children=[
                ast.Text('tkte.ch')
            ]
        )),
        ('[tkte.ch](https://tkte.ch "title")', ast.Link(
            'https://tkte.ch',
            title='title',
            children=[
                ast.Text('tkte.ch')
            ]
        )),
        ('![tkte.ch](/image.png)', ast.Image(
            '/image.png',
            children=[
                ast.Text('tkte.ch')
            ]
        )),
        ('![tkte.ch](/image.png "alt")', ast.Image(
            '/image.png',
            title='alt',
            children=[
                ast.Text('tkte.ch')
            ]
        ))
    )

    for markdown, node in pairs:
        assert loads(markdown) == ast.Fragment(children=[
            ast.Paragraph(children=[
                node
            ])
        ])
