import sys, os

# add source folder to path
sys.path.append(os.path.abspath("source"))

from source.analyzer_modules import RecordAnalyzer
from source.manager_modules import TaskManager
from source.habit import Habit
from source.task import Task
from source.enums import Period, Status, CompletionStatus

from datetime import datetime
import pytest
from unittest.mock import Mock

# === REPOSITORY MOCKING ===
@pytest.fixture(scope="function", name="mock_dependencies",)
def mock_dependencies(mocker):
    """Mocks all dependencies for the repositories, no database connection is required"""

    #Mocking Habit Repository
    MockHabitRepo = mocker.patch("source.habit.HabitRepository")
    MockHabitRepo.return_value.duplicate_naming.return_value = 0
    MockHabitRepo.return_value.get_largest_id.return_value = 100

    #Mocking Task and Record Repository
    MockTaskRepo = mocker.patch("source.habit.TaskRepository")
    MockRecordRepo = mocker.patch("source.habit.CompletionRecordRepository")

    #Mocking Task Manager and Record Analyzer
    MockTaskManager = mocker.patch("source.habit.TaskManager")
    MockRecordAnalyzer = mocker.patch("source.habit.RecordAnalyzer")

    return {
        "habit_repo": MockHabitRepo.return_value,
        "task_repo": MockTaskRepo.return_value,
        "record_repo": MockRecordRepo.return_value,
        "task_manager": MockTaskManager.return_value,
        "record_analyzer": MockRecordAnalyzer.return_value,

        "HabitRepoClass": MockHabitRepo,
        "TaskRepoClass": MockTaskRepo,
        "RecordRepoClass": MockRecordRepo,
        "TaskManagerClass": MockTaskManager,
        "RecordAnalyzerClass": MockRecordAnalyzer,
    }

# === ANALYZER MOCKING ===
@pytest.fixture(scope="function", name="mock_analyzer")
def mock_analyzer(mock_dependencies):
    mocked_analyzer = RecordAnalyzer(mock_dependencies["record_repo"])
    return mocked_analyzer

# === MANAGER MOCKING ===
@pytest.fixture(scope="function", name="mock_manager")
def mock_manager(mock_dependencies):
    mocked_manager = TaskManager(mock_dependencies["task_repo"], mock_dependencies["record_repo"])
    return mocked_manager

# === HABIT MOCKING ===
@pytest.fixture(params=[("30 Minutes Walk", 123, Period.DAILY, datetime(2023, 5, 12), Status.ACTIVE),
                        ("Do Meditation", 456, Period.WEEKLY, datetime(2024, 1, 24), Status.PAUSED),
                        ("Calculate Budget for Shopping", 789, Period.MONTHLY, datetime(2025, 6, 15), Status.ACTIVE),
                        ("Start a new Book", 1, Period.BIWEEKLY, datetime(2026, 3, 12), Status.ACTIVE),
                        ("Learn French", 1012, Period.DAILY, datetime(1999, 1, 1), Status.ACTIVE)],
                ids=["30 Minutes Walk", "Do Meditation", "Calculate Budget for Shopping", "Start a new Book", "Learn French"])
def mock_habit(request):
    name, habit_id, period, start_date, status = request.param

    mock_habit = Mock(spec=Habit)
    mock_habit.habit_name = name
    mock_habit.habit_id = habit_id
    mock_habit.period = period
    mock_habit.start_date = start_date
    mock_habit.status = status

    return mock_habit

@pytest.fixture(params=[("30 Minutes Walk", Period.DAILY)],
                ids=["30 Minutes Walk"])
def mock_habit_for_habit_class_tests(request):
    name, period = request.param
    return Habit(name, period)

# TASK MOCKING
@pytest.fixture(params=[("Sample Task", 999, datetime(2024, 6, 10), 0)],
                ids=["Sample Task"])
def mock_task(request):
    habit_name, habit_id, due_date, is_overdue = request.param

    mock_task = Mock(spec=Task)
    mock_task.habit_name = habit_name
    mock_task.habit_id = habit_id
    mock_task.due_date = due_date
    mock_task.is_overdue = is_overdue
    mock_task.completion_status = CompletionStatus.PENDING

    return mock_task

# RECORD TUPLE MOCKING
@pytest.fixture(params=[
    ("Sample Record 1", 999, 1, datetime.strptime("2024-01-03", "%Y-%m-%d"), 0, datetime.strptime("2024-01-03", "%Y-%m-%d"), "Completed"),
    ("Sample Record 2", 123, 7, datetime.strptime("2023-04-12", "%Y-%m-%d"), 1, datetime.strptime("2023-04-16", "%Y-%m-%d"), "Completed"),
    ("Sample Record 3", 12, 14, datetime.strptime("2022-12-31", "%Y-%m-%d"), 0, datetime.strptime("2022-12-31", "%Y-%m-%d"), "Skipped"),
], ids=["Completed on time", "Overdue", "Skipped"])
def mock_record_tuple(request):
    habit_name, habit_id, period, due_date, was_overdue, completion_date, completion_status = request.param

    tuple_record = (habit_name, habit_id, period, due_date, was_overdue, completion_date, completion_status)

    return tuple_record

# === DATABASE PATH MOCKING ===
@pytest.fixture(scope="function", autouse=True, name="db_path_for_testing")
def db_path_for_testing():
    return str("habit_tracker_test.db")

# === SAMPLE DATABASE RECORDS ===
@pytest.fixture(params=[
                        ([# 3 times full completion without any issues
                             {"due_date": "2024-01-03", "completion_status": CompletionStatus.COMPLETED.value, "was_overdue": 0},
                             {"due_date": "2024-01-02", "completion_status": CompletionStatus.COMPLETED.value, "was_overdue": 0},
                             {"due_date": "2024-01-01", "completion_status": CompletionStatus.COMPLETED.value, "was_overdue": 0},
                         ], {"streak": 3, "longest": 3, "rate": 1.0, "on_time": 1.0}),

                        ([# One overdue breaks current streak but longest stays
                             {"due_date": "2024-01-03", "completion_status": CompletionStatus.COMPLETED.value, "was_overdue": 1},
                             {"due_date": "2024-01-02", "completion_status": CompletionStatus.COMPLETED.value, "was_overdue": 0},
                             {"due_date": "2024-01-01", "completion_status": CompletionStatus.COMPLETED.value, "was_overdue": 0},
                         ], {"streak": 0, "longest": 2, "rate": 1.0, "on_time": 0.67}),

                        ([# Skipped in middle affects counts
                             {"due_date": "2024-01-03", "completion_status": CompletionStatus.COMPLETED.value, "was_overdue": 0},
                             {"due_date": "2024-01-02", "completion_status": CompletionStatus.SKIPPED.value, "was_overdue": 0},
                             {"due_date": "2024-01-01", "completion_status": CompletionStatus.COMPLETED.value, "was_overdue": 0},
                         ], {"streak": 1, "longest": 1, "rate": 0.67, "on_time": 0.67}),

                        ([# Empty records edge case
                         ], {"streak": 0, "longest": 0, "rate": 0.0, "on_time": 0.0}),
                        ], ids=["full_completions", "one_overdue", "skipped_middle", "empty_records"])
def sample_records(request):
    records, exp_values = request.param
    return records, exp_values

# === SAMPLE TASK RECORD ===
@pytest.fixture(params=
                [{"habit_name": "Sample Task", "habit_id":999, "due_date":"2026-06-10", "is_overdue":0, "completion_status":"Pending"}],
                ids=["Sample Task"])
def sample_task(request):
    return request.param