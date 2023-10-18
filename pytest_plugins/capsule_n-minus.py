# Collection of Capsule Factory fixture tests
# No destructive tests
# Adjust capsule host and capsule_configured host behavior for n_minus testing
# Calculate capsule hostname from inventory just as we do in xDist.py

def pytest_addoption(parser):
    """Add options for pytest to collect tests based on fixtures its using"""
    help_text = '''
        Collects tests based on capsule fixtures used by tests and uncollect destructive tests

        Usage: --n-minus

        example: pytest --n-minus tests/foreman
    '''
    parser.addoption(
        "--n-minus", action='store_true', default=False,
        help=help_text)


def pytest_collection_modifyitems(items, config):

    if not config.getoption('n_minus', False):
        return

    selected = []
    deselected = []

    for item in items:
        is_destructive = item.get_closest_marker('destructive')
        # Deselect Destructive tests and tests without capsule_factory fixture
        if 'capsule_factory' not in item.fixturenames or is_destructive:
            deselected.append(item)
            continue
        if 'session_puppet_enabled_sat' in item.fixturenames:
            deselected.append(item)
            continue
        if 'sat_maintain' in item.fixturenames and 'satellite' in item.callspec.params.values():
            deselected.append(item)
            continue
        selected.append(item)

    config.hook.pytest_deselected(items=deselected)
    items[:] = selected
