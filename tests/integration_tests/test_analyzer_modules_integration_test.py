# Test Connection Analyzer <> Repositories <> Database

# Import pytest for test fixtures
import pytest
pytestmark = pytest.mark.integration

# Import necessary modules from source
from source.app_logic.analyzer_modules import RecordAnalyzer
from source.app_logic.habit import Habit

# Detailed RecordAnalyzer calculations are covered by unit tests with mocked records.
# CompletionRecordRepository persistence is covered by repository integration tests.
# This file only contains a thin smoke test to verify that RecordAnalyzer works
# with records returned from the real repository/database layer.

# Create record analyzer with connection to real database
@pytest.fixture
def record_analyzer(record_repo_with_reg_path):
    return RecordAnalyzer(record_repo_with_reg_path)

@pytest.mark.parametrize("expected_habit_name, expected_streak", [
    ("Drink Water", 7),
    ("Write Blog", 0),
    ("Change Bed Laundry", 0),
    ("Stretching Routine", 2),
], ids=["Drink Water", "Write Blog", "Change Bed Laundry", "Stretching Routine"])
def test_current_streak_integration(expected_habit_name, expected_streak, record_analyzer, all_habits_from_db):
    """Test that the current streak is calculated correctly."""

    # Get habit ID from habit name that equals the habit name of the fixture
    habit_id = next(habit[0] for habit in all_habits_from_db if habit[1] == expected_habit_name)
    habit = Habit.from_db(habit_id)

    # Calculate streak
    streak = record_analyzer.calculate_streak(habit)

    # Compare to expected streak
    assert streak == expected_streak


@pytest.mark.parametrize("expected_habit_name, expected_rate", [
    ("Drink Water", 1.0),
    ("Write Blog", 1.0),
    ("Change Bed Laundry", 1.0),
    ("Stretching Routine", 0.55),
], ids=["Drink Water", "Write Blog", "Change Bed Laundry", "Stretching Routine"])
def test_completion_rate_integration(expected_habit_name, expected_rate, record_analyzer, all_habits_from_db):
    """Test that the completion rate is calculated correctly."""

    # Get habit ID from habit name that equals the habit name of the fixture
    habit_id = next(habit[0] for habit in all_habits_from_db if habit[1] == expected_habit_name)
    habit = Habit.from_db(habit_id)

    # Calculate completion rate
    rate = record_analyzer.calculate_completion_rate(habit)

    # Compare to expected rate with 0.5% tolerance
    assert pytest.approx(rate, 0.005) == expected_rate


@pytest.mark.parametrize("expected_habit_name, expected_len", [
    ("Drink Water", 7.0),
    ("Write Blog", 3.0),
    ("Change Bed Laundry", 1.0),
    ("Stretching Routine", 11.0),
], ids=["Drink Water", "Write Blog", "Change Bed Laundry", "Stretching Routine"])
def test_habit_history_integration(expected_habit_name, expected_len, record_analyzer, all_habits_from_db):
    """Test that the habit history is returned correctly."""

    expected_keys = ["habit_name", "completion_date", "completion_status", "was_overdue"]

    # Get habit ID from habit name that equals the habit name of the fixture
    habit_id = next(habit[0] for habit in all_habits_from_db if habit[1] == expected_habit_name)
    habit = Habit.from_db(habit_id)

    # Get habit history
    history = record_analyzer.habit_history(habit)

    # Verify structure and content
    assert len(history) == expected_len
    assert isinstance(history, list)
    assert all(isinstance(record, dict) for record in history)
    assert all(key in record for record in history for key in expected_keys)
    assert all(record["habit_name"] == expected_habit_name for record in history)