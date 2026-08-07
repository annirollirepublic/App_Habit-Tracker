# Test Connection Analyzer <> Repositories <> Database
import pytest
pytestmark = pytest.mark.integration

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

def test_current_streak_integration(habit_repo_with_reg_path, record_analyzer, all_habits_from_db):
    expected_streak = {"Drink Water":7,
                       "Write Blog": 0,
                       "Change Bed Laundry": 0,
                       "Stretching Routine": 2}

    for habit_id, habit_name, period, start_date, status in all_habits_from_db:
        habit = Habit.from_db(habit_id)

        streak = record_analyzer.calculate_streak(habit)

        # if record for habit was created, not for "Read 50 Pages"
        if habit.habit_name in expected_streak.keys():
            assert expected_streak[habit.habit_name] == streak

def test_completion_rate_integration(habit_repo_with_reg_path, record_analyzer, all_habits_from_db):
    expected_rate = {"Drink Water": 1.,
                     "Write Blog": 1.,
                     "Change Bed Laundry": 1.,
                     "Stretching Routine": 0.55}

    for habit_id, habit_name, period, start_date, status in all_habits_from_db:
        habit = Habit.from_db(habit_id)

        rate = record_analyzer.calculate_completion_rate(habit)

        # if record for habit was created, not for "Read 50 Pages"
        if habit.habit_name in expected_rate.keys():
            assert pytest.approx(expected_rate[habit.habit_name], rel=0.1) == rate
