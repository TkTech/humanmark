from humanmark.backends import available_backends


def test_backends():
    """Ensure plugin-registered backends are present and valid."""
    backends = available_backends()

    # Make sure our default backend is available at least.
    assert 'markdown_it' in backends

    # Ensure required fields are available on every backend.
    for v in backends.values():
        assert v.DESCRIPTION is not None
