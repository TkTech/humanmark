HumanMark
=========

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Contents:

   cli
   reference/index
   contributing

A human-friendly markdown *generator*. Accidentally also really useful for
manipulating existing markdown. HumanMark offers a powerful AST that makes
many annoying markdown operations trivial.

.. admonition:: Work In Progress
    :class: caution

    This library is still in beta and is being actively developed. Looking for
    a feature? Found a bug? Please, make an issue on `GitHub`_.


Installation
------------

HumanMark is available from PyPi for CPython3.7+ and PyPy:

    pip install humanmark


Building an AST
---------------

We can easily load an AST from an existing bit of Markdown:

.. code:: python

    from humanmark import load

    with open('README.md', 'rt') as source:
        fragment = load(source)

Or create a new AST explicitly:

.. code:: python

    from humanmark import Fragment, Header, Paragraph, Text

    fragment = Fragment(children=[
        Header(1, children=[
            Text('Hello World!')
        ]),
        Paragraph(children=[
            Text('This is a sample document.')
        ])
    ])


Navigation
----------

Finding nodes is easy using :func:`~humanmark.ast.Node.find()`. We can find by
type:

.. code:: python

    fragment.find(Header)

Or using a path to get all of the text under a header:

.. code:: python

    fragment.find(Header / Text)

Or using a filter to only get the top-level headers:

.. code:: python

    fragment.find(Header, f=lambda h: h.level == 1)

... but maybe we just want the first one:

.. code:: python

    fragment.find_one(Header, f=lambda h: h.level == 1)

Of course, we can also just loop over all the children in a node:

.. code:: python

    for child in fragment:
        if isinstance(child, Header):
            print('Found a header!')

Editing
-------

You can append and prepend siblings. Lets add a new paragraph below every
header:

.. code:: python

    for header in fragment.find(Header):
        header.append_sibling(
            Paragraph(children=[
                Text('This will appear below every header!'),
                SoftBreak(),
                Text('We could have used this to add "back to top" links.')
            ])
        )

License
-------

HumanMark is made available under the MIT License. For more details, see
`LICENSE`_.

.. _LICENSE: https://github.com/tktech/humanmark/blob/main/LICENSE
.. _GitHub: https://github.com/tktech/humanmark
