# Test Connection Habits <> Repositories, TaskManager, RecordAnalyzer <> Database

# Import datetime for datetime calculations
from datetime import datetime, timedelta

# Import necessary modules from source
from source.helpers.enums import Period
from source.app_logic.habit import Habit
from source.helpers.utils_datetime_helper import dt_to_string, string_to_dt

# Detailed habit behavior is covered by unit tests with mocked repositories.
# Repository persistence is covered by repository integration tests.
# TaskManager behavior is covered by task_manager_integration_test.py
# RecordAnalyzer behavior is covered by record_analyzer_integration_test.py
# This file should only contain selected smoke tests that verify habit works with real repositories

def test_habit_creation_new_integration(habit_repo_with_reg_path, task_repo_with_reg_path):
    """Test that a new habit is created correctly in the database."""

    # Expected habit record and task record
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

    # Check whether habit is created and task is created correctly in database
    new_habit = Habit("Other Habit", Period.DAILY)

    assert habit_repo_with_reg_path.find_by_habit_id(new_habit.habit_id) == expected_habit_record
    assert task_repo_with_reg_path.find_by_habit_id(new_habit.habit_id) == expected_task_record

    # Ensure deletion of new habit to remain clean testing database
    new_habit.delete()

    # Force flush + slight delay
    import time
    time.sleep(0.1)

def test_habit_creation_from_db_integration(all_habits_from_db, task_repo_with_reg_path):
    """Test that a habit is created correctly from the database."""

    for habit_id, habit_name, period, start_date, status in all_habits_from_db:
        habit = Habit.from_db(habit_id)

        assert habit.habit_id == habit_id
        assert habit.habit_name == habit_name
        assert dt_to_string(habit.start_date) == start_date
        assert habit.period.value == period
        assert habit.status.value == status

        # Check that task is only created if habit is active
        task_entry = task_repo_with_reg_path.find_by_habit_id(habit.habit_id)

        if habit.status.value == "Active":
            assert len(task_entry) == 1
        else:
            assert len(task_entry) == 0

def test_habit_task_completion_integration(task_repo_with_reg_path, record_repo_with_reg_path):
    """Test that a habit's task is completed correctly."""

    # Expected new task record after check-off of old task
    expected_new_task_record = [{"habit_name": "Other Habit",
                             "habit_id": 9877,
                             "due_date": dt_to_string(datetime.today()+timedelta(days=1)),
                             "is_overdue": 0,
                             "completion_status": "Pending"}]

    # Create habit that has corresponding task
    habit = Habit("Other Habit", Period.DAILY)

    # Get old number of records
    old_amt_records = len(record_repo_with_reg_path.find_by_habit_id(habit.habit_id))

    # Complete corresponding task
    habit.complete()

    # Force flush + slight delay
    import time
    time.sleep(0.1)

    # Check that new task is created and record is created
    assert len(task_repo_with_reg_path.find_by_habit_id(habit.habit_id)) == 1
    assert task_repo_with_reg_path.find_by_habit_id(habit.habit_id) == expected_new_task_record
    assert len(record_repo_with_reg_path.find_by_habit_id(habit.habit_id)) == old_amt_records + 1

    # Ensure deletion of new habit to remain clean testing database
    record_repo_with_reg_path.delete((habit.habit_name, habit.habit_id))
    habit.delete()

    # Force flush + slight delay
    time.sleep(0.1)

def test_change_naming_integration(habit_repo_with_reg_path, task_repo_with_reg_path):
    """Test that a habit's name is changed correctly."""

    # Expected habit record and task record
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

    # Create habit that has corresponding task
    new_habit = Habit("Other Habit", Period.DAILY)

    # Change habit name
    new_habit.habit_name = "Changed Habit"

    # Check whether habit is created and task is changed accordingly in database
    assert habit_repo_with_reg_path.find_by_habit_id(new_habit.habit_id) == expected_changed_habit_record
    assert task_repo_with_reg_path.find_by_habit_id(new_habit.habit_id) == expected_changed_task_record

    # Ensure deletion of new habit to remain clean testing database
    new_habit.delete()

    # Force flush + slight delay
    import time
    time.sleep(0.1)
