from humanmark.render import available_renderers


def test_renderers():
    """Ensure plugin-registered renderers are present and valid."""
    renderers = available_renderers()

    # Make sure our default render is available at least.
    assert 'markdown' in renderers

    # Ensure required fields are available on every renderer.
    for v in renderers.values():
        assert v.DESCRIPTION is not None
        assert v.OPTIONS_CLASS is not None
