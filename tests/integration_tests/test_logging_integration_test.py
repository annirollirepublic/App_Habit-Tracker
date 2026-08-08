import logging
#from pathlib import Path
import pytest
#from source.config import logging as logging_config
from source.helpers.exceptions import DuplicateHabitError
from source.app_logic.habit import Habit
from source.helpers.enums import Period
from source.helpers.exceptions import CreationFromDatabaseError


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
    """Verifies that logging writes to file at INFO level."""
    log_path = reset_log_file

    habit = None
    try:
        habit = Habit("Test Log Habit", Period.DAILY)

        assert log_path.exists(), "Log file was not created"
        content = log_path.read_text()
        assert "Creating Habit" in content, "No habit creation logs found"
        assert "INFO" in content, "No INFO level logs found"
    finally:
        habit.delete()

def test_duplicate_habit_error_is_logged(habit_repo_with_reg_path, caplog):
    """Critical: Duplicate habit creation must be logged at ERROR level."""
    # Create first habit
    habit = Habit("Log Test Habit", Period.DAILY)
    habit_id = habit.habit_id

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
        habit.delete()


def test_from_db_error_is_logged_when_habit_not_found(caplog):
    """Critical: Loading non-existent habit must be logged at ERROR level."""
    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError, match="Habit with ID 99999 not found"):
            Habit.from_db(99999)

    assert any(
        "no habit data found" in rec.message.lower() and rec.levelno == logging.ERROR
        for rec in caplog.records
    ), f"No 'not found' error logged. Records: {[r.message for r in caplog.records]}"


def test_database_connection_failure_is_logged(monkeypatch, caplog):
    """Critical: Database connection failure must be logged at a CRITICAL level."""
    import sqlite3
    from source.repository.repository_modules import HabitRepository

    # Force sqlite3.connect to fail
    def mock_connect_fail(*args, **kwargs):
        raise sqlite3.OperationalError("Simulated connection failure")

    monkeypatch.setattr(sqlite3, "connect", mock_connect_fail)

    with caplog.at_level(logging.CRITICAL):
        repo = HabitRepository()
        with pytest.raises(Exception):
            repo.browse_all()

    assert any(
        "failed to create database connection" in rec.message.lower()
        and rec.levelno >= logging.CRITICAL
        for rec in caplog.records
    ), f"No connection error logged. Records: {[r.message for r in caplog.records]}"