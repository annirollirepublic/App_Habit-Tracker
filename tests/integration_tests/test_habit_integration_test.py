# Test Connection Habits <> Repositories, TaskManager, RecordAnalyzer <> Database
import pytest
from datetime import datetime, timedelta

from source.enums import Period
from source.habit import Habit
from source.utils_datetime_helper import dt_to_string

pytestmark = pytest.mark.integration

# Detailed habit behavior is covered by unit tests with mocked repositories.
# Repository persistence is covered by repository integration tests.
# TaskManager behavior is covered by task_manager_integration_test.py
# RecordAnalyzer behavior is covered by record_analyzer_integration_test.py
# This file should only contain selected smoke tests that verify habit works with real repositories

def test_habit_creation_new_integration(habit_repo_with_reg_path, task_repo_with_reg_path):
    expected_habit_record = [{"habit_name": "Other Habit",
                             "habit_id": 9877,
                             "period": 1,
                             "start_date": dt_to_string(datetime.today()),
                             "status": "Active"}]

    expected_task_record = [{"habit_name": "Other Habit",
                             "habit_id": 9877,
                             "due_date": dt_to_string(datetime.today()),
                             "is_overdue": 0,
                             "completion_status": "Pending"}]

    # checks whether habit is created and task is created correctly in database
    new_habit = Habit("Other Habit", Period.DAILY, _from_db=False)

    assert habit_repo_with_reg_path.find_by_habit_id(new_habit.habit_id) == expected_habit_record
    assert task_repo_with_reg_path.find_by_habit_id(new_habit.habit_id) == expected_task_record

    # Ensure deletion of new habit to remain clean testing database
    new_habit.delete()

    # Force flush + slight delay
    import time
    time.sleep(0.1)

def test_habit_creation_from_db_integration(all_habits_from_db, task_repo_with_reg_path):
    # checks whether habit is created and task is created correctly in database
    for habit_id, habit_name, period, start_date, status in all_habits_from_db:
        habit = Habit(habit_name, period, start_date, habit_id, status,True)

        assert habit.habit_id == habit_id
        assert habit.habit_name == habit_name
        assert habit.start_date == start_date
        assert habit.period == period
        assert habit.status == status

        task_entry = task_repo_with_reg_path.find_by_habit_id(habit.habit_id)

        if habit.status == "Active":
            assert len(task_entry) == 1
        else:
            assert len(task_entry) == 0

def test_habit_task_completion_integration(task_repo_with_reg_path, record_repo_with_reg_path):
    expected_new_task_record = [{"habit_name": "Other Habit",
                             "habit_id": 9877,
                             "due_date": dt_to_string(datetime.today()+timedelta(days=1)),
                             "is_overdue": 0,
                             "completion_status": "Pending"}]

    new_habit = Habit("Other Habit", Period.DAILY, _from_db=False)

    new_habit.complete()
    # Force flush + slight delay
    import time
    time.sleep(0.1)

    assert len(task_repo_with_reg_path.find_by_habit_id(new_habit.habit_id)) == 1
    assert task_repo_with_reg_path.find_by_habit_id(new_habit.habit_id) == expected_new_task_record

    # Ensure deletion of new habit to remain clean testing database
    record_repo_with_reg_path.delete((new_habit.habit_name, new_habit.habit_id))
    new_habit.delete()

    # Force flush + slight delay
    time.sleep(0.1)

def test_change_naming_integration(habit_repo_with_reg_path, task_repo_with_reg_path):
    expected_changed_habit_record = [{"habit_name": "Changed Habit",
                                      "habit_id": 9877,
                                      "period": 1,
                                      "start_date": dt_to_string(datetime.today()),
                                      "status": "Active"}]

    expected_changed_task_record = [{"habit_name": "Changed Habit",
                                     "habit_id": 9877,
                                     "due_date": dt_to_string(datetime.today()),
                                     "is_overdue": 0,
                                     "completion_status": "Pending"}]

    new_habit = Habit("Other Habit", Period.DAILY, _from_db=False)
    new_habit.habit_name = "Changed Habit"

    assert habit_repo_with_reg_path.find_by_habit_id(new_habit.habit_id) == expected_changed_habit_record
    assert task_repo_with_reg_path.find_by_habit_id(new_habit.habit_id) == expected_changed_task_record

    # Ensure deletion of new habit to remain clean testing database
    new_habit.delete()

    # Force flush + slight delay
    import time
    time.sleep(0.1)
