# Test Connection Habits <> Repositories, TaskManager, RecordAnalyzer
import pytest
pytestmark = pytest.mark.integration

def test_habit_creation():
    # creating a habit creates a habit row and task row
    pass

def test_habit_rejection_on_duplicate_name():
    pass

def test_habit_task_completion():
    # completing a habit creates a completion record and next task
    pass

def test_habit_task_skipping():
    # skipping a habit creates a skipped record and next task
    pass

def test_pause_habit():
    # pausing a habit updates habit status and removes current task
    pass

def test_reactivate_habit():
    # reactivating a habit updates status and creates current task
    pass

def test_change_naming():
    # changing name updates habit and task
    pass

def test_change_period():
    # changing period updates habit and task due date
    pass

def test_delete_habit():
    # deleting habit removes habit and task
    pass

def test_calculate_habit_streak():
    # calculating streak delegates through analyzer using real records
    pass