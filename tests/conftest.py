from tests import scorecard


def pytest_sessionfinish(session, exitstatus):
    """Write the reported-not-asserted scorecard (tests/scorecard.py) after every run."""
    scorecard.write()
