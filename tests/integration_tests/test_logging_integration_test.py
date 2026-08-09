# Import logging module to test logging
import logging

# Import pytest to mark tests as integration tests
import pytest
pytestmark = pytest.mark.integration

# Import necessary modules from source
from source.helpers.exceptions import DuplicateHabitError
from source.repository.repository_modules import HabitRepository
from source.app_logic.habit import Habit
from source.helpers.enums import Period

# Import sqlite3 for mocking database connection
import sqlite3

@pytest.fixture(autouse=True)
def reset_log_file(tmp_path):
    """Use a temp log file for each test."""
    log_path = tmp_path / "test_habit_tracker.log"
    # Override config to use temp file
    handler = logging.FileHandler(str(log_path))
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logging.basicConfig(level=logging.DEBUG, handlers=[handler], force=True)
    yield log_path
    logging.shutdown()


def test_log_file_created_and_writes(tmp_path, reset_log_file):
    """Verifies that logging writes to the file at the INFO level."""

    # Assign path to log file
    log_path = reset_log_file

    # Create habit and verify log file is created and contains expected content
    habit = None
    try:
        habit = Habit("Test Log Habit", Period.DAILY)

        assert log_path.exists(), "Log file was not created"
        content = log_path.read_text()
        assert "Creating Habit" in content, "No habit creation logs found"
        assert "INFO" in content, "No INFO level logs found"

    # Cleanup
    finally:
        if habit:
            habit.delete()


def test_duplicate_habit_error_is_logged(habit_repo_with_reg_path, caplog):
    """Critical: Duplicate habit creation must be logged at ERROR level."""

    # Create first habit
    habit = Habit("Log Test Habit", Period.DAILY)

    try:
        # Attempt duplicate creation with caplog capturing
        with caplog.at_level(logging.ERROR):
            with pytest.raises(DuplicateHabitError):
                Habit("Log Test Habit", Period.DAILY)

        # Verify error was logged
        assert any(
            "duplicate" in rec.message.lower() and rec.levelno == logging.ERROR
            for rec in caplog.records
        ), f"No duplicate error logged. Records: {[r.message for r in caplog.records]}"

    finally:
        # Cleanup
        if habit:
            habit.delete()


def test_from_db_error_is_logged_when_habit_not_found(caplog):
    """Critical: Loading non-existent habit must be logged at ERROR level."""

    # Force habit search to fail
    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError, match="Habit with ID 99999 not found"):
            Habit.from_db(99999)

    # Verify error was logged correctly
    assert any(
        "no habit data found" in rec.message.lower() and rec.levelno == logging.ERROR
        for rec in caplog.records
    ), f"No 'not found' error logged. Records: {[r.message for r in caplog.records]}"


def test_database_connection_failure_is_logged(monkeypatch, caplog):
    """Critical: Database connection failure must be logged at a CRITICAL level."""

    # Force sqlite3.connect to fail
    def mock_connect_fail(*args, **kwargs):
        raise sqlite3.OperationalError("Simulated connection failure")

    # Monkeypatch sqlite3.connect to simulate connection failure
    monkeypatch.setattr(sqlite3, "connect", mock_connect_fail)

    # Attempt to create repository, which should fail
    with caplog.at_level(logging.CRITICAL):
        repo = HabitRepository()
        with pytest.raises(Exception):
            repo.browse_all()

    # Verify error was logged correctly
    assert any(
        "failed to create database connection" in rec.message.lower()
        and rec.levelno >= logging.CRITICAL
        for rec in caplog.records
    ), f"No connection error logged. Records: {[r.message for r in caplog.records]}"