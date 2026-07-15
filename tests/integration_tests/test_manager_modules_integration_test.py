# Test Connection TaskManager <> Repositories <> Database
import pytest
from datetime import datetime, timedelta

from source.manager_modules import TaskManager
from source.utils_datetime_helper import dt_to_string
from tests.conftest import task_repo_with_temp_path

pytestmark = pytest.mark.integration

# Detailed TaskManager behavior is covered by unit tests with mocked repositories.
# Repository persistence is covered by repository integration tests.
# This file should only contain selected smoke tests that verify TaskManager works with real repositories

# Create task manager with connection to real database
@pytest.fixture
def task_manager(task_repo_with_temp_path, record_repo_with_temp_path):
    return TaskManager(task_repo_with_temp_path, record_repo_with_temp_path)

def test_create_task_integration(task_manager, mock_habit, task_repo_with_temp_path):

    created_task = task_manager.create_first_task(mock_habit)

    result = task_repo_with_temp_path.find_by_habit_id(mock_habit.habit_id)

    assert len(result) == 1
    assert result[0]["habit_id"] == mock_habit.habit_id
    assert result[0]["habit_name"] == mock_habit.habit_name
    assert result[0]["due_date"] == dt_to_string(mock_habit.start_date)
    assert result[0]["is_overdue"] == (mock_habit.start_date < datetime.today())
    assert result[0]["completion_status"] == "Pending"

    assert created_task.habit_id == mock_habit.habit_id
    assert created_task.habit_name == mock_habit.habit_name
    assert created_task.due_date == mock_habit.start_date

def test_complete_task_integration(task_manager, mock_habit, task_repo_with_temp_path, record_repo_with_temp_path):

    first_task = task_manager.create_first_task(mock_habit)
    new_task = task_manager.complete_current_task(mock_habit)

    new_task_result = task_repo_with_temp_path.find_by_habit_id(mock_habit.habit_id)
    recording_result = record_repo_with_temp_path.find_by_habit_name(mock_habit.habit_name)

    assert len(new_task_result) == 1
    assert new_task_result[0]["habit_id"] == mock_habit.habit_id #is preserved
    assert new_task_result[0]["habit_name"] == mock_habit.habit_name #is preserved
    assert new_task_result[0]["due_date"] == dt_to_string(first_task.due_date + timedelta(days=mock_habit.period.value))
    assert new_task_result[0]["completion_status"] == "Pending"

    assert len(recording_result) == 1
    assert recording_result[0]["habit_id"] == mock_habit.habit_id #handover successful
    assert recording_result[0]["habit_name"] == mock_habit.habit_name #handover successful
    assert recording_result[0]["period"] == mock_habit.period.value #handover successful
    assert recording_result[0]["due_date"] == dt_to_string(first_task.due_date) #handover successful
    assert recording_result[0]["was_overdue"] == (first_task.due_date < datetime.today())
    assert recording_result[0]["completion_date"] == dt_to_string(datetime.today())
    assert recording_result[0]["completion_status"] == "Completed" #status log
