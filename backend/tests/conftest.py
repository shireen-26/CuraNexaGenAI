import logging
import pytest

@pytest.fixture(autouse=True)
def restore_logging_after_test():
    """
    Ensures pytest's logging capture works even after the app's logging 
    configuration replaces handlers. This fixture runs automatically 
    for every test.
    """
    # Save current logging state
    root = logging.getLogger()
    old_handlers = root.handlers[:]
    old_level = root.level

    yield

    # Restore original handler state
    root.handlers = old_handlers
    root.setLevel(old_level)


@pytest.fixture(autouse=True)
def ensure_caplog_works(caplog):
    """
    Makes sure the caplog handler is added *after* the app configures logging.
    """
    root = logging.getLogger()

    # If caplog handler is missing due to configure_logging(), re-add it
    for handler in caplog.handler.records:
        if handler not in root.handlers:
            root.addHandler(caplog.handler)

    yield
