# HumanMark

A human-friendly markdown *generator*. Accidentally also really useful for
manipulating existing markdown.

## 📝 Parse & Modify Markdown

Editing existing markdown is trivial. Maybe we want to uppercase every
header:

```python
from humanmark import loads, Header, Text

fragment = loads('''# Hello World!

This is a sample document.
''')

for text in fragment.find(Header / Text):
    text.content = text.content.upper()

fragment.pprint()
```

Maybe we wanted to make sure we'd only edit top-level headers. We would just
add a filter to our `find()`:

```python
headers = fragment.find(Header, f=lambda header: header.level == 1)
```

## 🙈 Why?

Manually updating a [Awesome-style][] project's README.md sucks. Dead links,
unsorted, royal pain to add and update star and fork counts, etc. So I
created a meta-project, Awesome^2, to generate these README.md files
automatically from an index.yaml. Originally, this just used a [Jinja2][]
template to output the markdown, which sucked. Getting line wrapping and
whitespace correct was non-trivial. So, made a generator.

Then I realized I'd need to parse markdown anyways, both to support having
extra markdown in the header and footers of an index.yaml, and to ease
conversion of existing README.md files to an index.yaml. So, made the
generator bi-directional.

## ⚗ Testing

HumanMark has good test coverage via pytest. Install the extras with:

    pip install -e ".[test]"
    pip install -e ".[cli]"

... and run the tests with:

    pytest

[markdown-it-py]: https://github.com/executablebooks/markdown-it-py
[awesome-style]: https://github.com/sindresorhus/awesome
[Jinja2]: https://jinja.palletsprojects.com/en/2.11.x/
