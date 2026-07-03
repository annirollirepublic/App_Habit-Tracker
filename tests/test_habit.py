from source.exceptions import DuplicateHabitError
from source.habit import Habit
from source.enums import Period, Status
import pytest
from datetime import datetime
from source.utils_datetime_helper import dt_to_string

@pytest.fixture(scope="function", autouse=True, name="mock_dependencies")
def mock_dependencies(mocker):
    """Mocks all dependencies for the repositories, no database connection is required"""

    #Mocking Habit Repository and all used methods
    MockHabitRepo = mocker.patch("source.habit.HabitRepository")
    MockHabitRepo.return_value.duplicate_naming.return_value = 0
    MockHabitRepo.return_value.get_largest_id.return_value = 100

    #Mocking Task and Record Repository for __save_habit()
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

@pytest.fixture(scope="function",
                params=[("Habit A", Period.DAILY),
                        ("Habit B", Period.WEEKLY),
                        ("Habit C", Period.MONTHLY),
                        ("Habit D", Period.BIWEEKLY),
                        ("Habit E", Period.DAILY)])

def mock_habit(request, mock_dependencies):
    name, period = request.param
    return Habit(name, period)

class TestInitialAttributes:

    def test_handling_duplicate_naming(self, mock_habit, mock_dependencies):
        mock_dependencies["habit_repo"].duplicate_naming.return_value = 1 #Set duplicates to 1 temporally to test
        with pytest.raises(Exception, match=f"Habit \"{mock_habit.habit_name}\" already exists in database."):
            Habit(mock_habit.habit_name, mock_habit.period)

    def test_initial_status(self, mock_habit):
        assert mock_habit.status.value == Status.ACTIVE.value

    def test_calculated_id(self, mock_habit):
        assert mock_habit.habit_id == 101

    def test_initial_default_start_date(self, mock_habit):
        assert dt_to_string(mock_habit.start_date) == dt_to_string(datetime.today())

class TestInstantiateDependencies:

    def test_habit_repo_instantiation(self, mock_habit, mock_dependencies):
        mock_dependencies["HabitRepoClass"].assert_called_once_with()
        mock_dependencies["habit_repo"].create.assert_called_once_with(mock_habit)

    def test_task_repo_instantiation(self, mock_habit, mock_dependencies):
        mock_dependencies["TaskRepoClass"].assert_called_once_with()

    def test_record_repo_instantiation(self, mock_habit, mock_dependencies):
        mock_dependencies["RecordRepoClass"].assert_called_once_with()

    def test_task_manager_instantiation(self, mock_habit, mock_dependencies):
        mock_dependencies["TaskManagerClass"].assert_called_once_with(mock_dependencies["task_repo"], mock_dependencies["record_repo"])
        mock_dependencies["task_manager"].create_first_task.assert_called_once_with(mock_habit)

    def test_record_analyzer_instantiation(self, mock_habit, mock_dependencies):
        mock_dependencies["RecordAnalyzerClass"].assert_called_once_with(mock_dependencies["record_repo"])

class TestSetterMethods:

    def test_set_habit_name(self, mock_habit):
        mock_habit.habit_name = "New Habit Name"
        assert mock_habit.habit_name == "New Habit Name"

    def test_set_period(self, mock_habit):
        mock_habit.period = Period.WEEKLY
        assert mock_habit.period == Period.WEEKLY

    def test_set_start_date(self, mock_habit):
        mock_habit.start_date = "2023-01-01"
        assert dt_to_string(mock_habit.start_date) == "2023-01-01"

class TestInteraction:

    def test_complete_habit(self, mock_habit, mock_dependencies):
        mock_habit.complete()
        mock_dependencies["task_manager"].complete_current_task.assert_called_once_with(mock_habit)

    def test_skip_habit(self, mock_habit, mock_dependencies):
        mock_habit.skip()
        mock_dependencies["task_manager"].skip_current_task.assert_called_once_with(mock_habit)

    def test_pause_habit(self, mock_habit, mock_dependencies):
        mock_habit.pause()
        assert mock_habit.status.value == Status.PAUSED.value
        mock_dependencies["habit_repo"].update.assert_called_once_with(mock_habit)
        mock_dependencies["task_manager"].delete_current_task.assert_called_once_with(mock_habit)

    def test_reactivate_habit(self, mock_habit, mock_dependencies):
        mock_habit.reactivate()
        assert mock_habit.status.value == Status.ACTIVE.value
        mock_dependencies["habit_repo"].update.assert_called_once_with(mock_habit)
        assert mock_dependencies["task_manager"].create_first_task.call_count > 1

    def test_delete_habit(self, mock_habit, mock_dependencies):
        mock_habit.delete()
        mock_dependencies["habit_repo"].delete.assert_called_once_with(mock_habit)
        mock_dependencies["task_manager"].delete_current_task.assert_called_once_with(mock_habit)

class TestCalculateStreak:

    def test_calculate_streak(self, mock_habit, mock_dependencies):
        mock_habit.calculate_current_streak()
        mock_dependencies["record_analyzer"].calculate_streak.assert_called_once_with(mock_habit)

class TestLogger:
    pass



