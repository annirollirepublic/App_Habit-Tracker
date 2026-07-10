from source.exceptions import DuplicateHabitError
from source.utils_datetime_helper import dt_to_string
from source.habit import Habit
from source.enums import Period, Status

import pytest
pytestmark = pytest.mark.unit
from datetime import datetime

# TODO: Implement logger tests

class TestHabitInitialization:

    def test_handling_duplicate_naming(self, mock_habit_for_habit_class_tests, mock_dependencies):
        mock_dependencies["habit_repo"].duplicate_naming.return_value = 1 #Set duplicates to 1 temporally to test

        # Reset mocks that are already called in mock_habit
        for key in ["habit_repo", "TaskManagerClass", "RecordAnalyzerClass", "TaskRepoClass", "RecordRepoClass"]:
            mock_dependencies[key].reset_mock()

        # Error is raised
        with pytest.raises(DuplicateHabitError, match=f"Habit \"{mock_habit_for_habit_class_tests.habit_name}\" already exists in database."):
            Habit(mock_habit_for_habit_class_tests.habit_name, mock_habit_for_habit_class_tests.period)

        # Check whether dependencies were not called due to previous error
        mock_dependencies["habit_repo"].create.assert_not_called()
        mock_dependencies["habit_repo"].get_largest_id.assert_not_called()
        mock_dependencies["TaskManagerClass"].assert_not_called()
        mock_dependencies["RecordAnalyzerClass"].assert_not_called()
        mock_dependencies["TaskRepoClass"].assert_not_called()
        mock_dependencies["RecordRepoClass"].assert_not_called()

    def test_initial_status(self, mock_habit_for_habit_class_tests):
        assert mock_habit_for_habit_class_tests.status.value == Status.ACTIVE.value

    def test_calculated_id(self, mock_habit_for_habit_class_tests):
        assert mock_habit_for_habit_class_tests.habit_id == 101

    def test_initial_default_start_date(self, mock_habit_for_habit_class_tests):
        # Check whether start date is within 5 seconds of current date (handle edge case of midnight habit creation) 
        assert abs((mock_habit_for_habit_class_tests.start_date - datetime.today()).total_seconds()) < 5

    @pytest.mark.skip(reason="Logger behavior will be covered later")
    def test_logger_initialization(self):
        pass

class TestHabitInstantiateDependencies:

    def test_habit_repo_instantiation(self, mock_habit_for_habit_class_tests, mock_dependencies):
        mock_dependencies["HabitRepoClass"].assert_called_once_with()
        mock_dependencies["habit_repo"].create.assert_called_once_with(mock_habit_for_habit_class_tests)

    def test_task_repo_instantiation(self, mock_habit_for_habit_class_tests, mock_dependencies):
        mock_dependencies["TaskRepoClass"].assert_called_once_with()

    def test_record_repo_instantiation(self, mock_habit_for_habit_class_tests, mock_dependencies):
        mock_dependencies["RecordRepoClass"].assert_called_once_with()

    def test_task_manager_instantiation(self, mock_habit_for_habit_class_tests, mock_dependencies):
        mock_dependencies["TaskManagerClass"].assert_called_once_with(mock_dependencies["task_repo"], mock_dependencies["record_repo"])
        mock_dependencies["task_manager"].create_first_task.assert_called_once_with(mock_habit_for_habit_class_tests)

    def test_record_analyzer_instantiation(self, mock_habit_for_habit_class_tests, mock_dependencies):
        mock_dependencies["RecordAnalyzerClass"].assert_called_once_with(mock_dependencies["record_repo"])

    # def test_logger_habit_creation_successful(self, mock_habit, mock_dependencies, caplog):
    #     with caplog.at_level(logging.INFO):
    #         assert f"Creating Habit '{mock_habit.habit_name}' (ID {mock_habit.habit_id})." in caplog.messages

class TestHabitSetterMethods:

    def test_set_habit_name(self, mock_habit_for_habit_class_tests, mock_dependencies):
        mock_habit_for_habit_class_tests.habit_name = "New Habit Name"
        assert mock_habit_for_habit_class_tests.habit_name == "New Habit Name"
        mock_dependencies["habit_repo"].update.assert_called_once_with(mock_habit_for_habit_class_tests)
        mock_dependencies["task_manager"].update_current_task.assert_called_once_with(mock_habit_for_habit_class_tests)

    def test_set_period(self, mock_habit_for_habit_class_tests, mock_dependencies):
        mock_habit_for_habit_class_tests.period = Period.WEEKLY
        assert mock_habit_for_habit_class_tests.period == Period.WEEKLY
        mock_dependencies["habit_repo"].update.assert_called_once_with(mock_habit_for_habit_class_tests)
        mock_dependencies["task_manager"].update_current_task.assert_called_once_with(mock_habit_for_habit_class_tests)

    def test_set_start_date(self, mock_habit_for_habit_class_tests, mock_dependencies,):
        mock_habit_for_habit_class_tests.start_date = "2023-01-01"
        assert dt_to_string(mock_habit_for_habit_class_tests.start_date) == "2023-01-01"
        mock_dependencies["habit_repo"].update.assert_called_once_with(mock_habit_for_habit_class_tests)
        mock_dependencies["task_manager"].update_current_task.assert_called_once_with(mock_habit_for_habit_class_tests)

class TestHabitInteraction:

    def test_complete_habit(self, mock_habit_for_habit_class_tests, mock_dependencies):
        mock_habit_for_habit_class_tests.complete()
        
        mock_dependencies["task_manager"].complete_current_task.assert_called_once_with(mock_habit_for_habit_class_tests)

    def test_skip_habit(self, mock_habit_for_habit_class_tests, mock_dependencies):
        mock_habit_for_habit_class_tests.skip()
        
        mock_dependencies["task_manager"].skip_current_task.assert_called_once_with(mock_habit_for_habit_class_tests)

    def test_pause_habit(self, mock_habit_for_habit_class_tests, mock_dependencies):
        mock_habit_for_habit_class_tests.pause()
        
        assert mock_habit_for_habit_class_tests.status.value == Status.PAUSED.value
        mock_dependencies["habit_repo"].update.assert_called_once_with(mock_habit_for_habit_class_tests)
        mock_dependencies["task_manager"].delete_current_task.assert_called_once_with(mock_habit_for_habit_class_tests)

    def test_reactivate_habit(self, mock_habit_for_habit_class_tests, mock_dependencies):
        mock_dependencies["task_manager"].create_first_task.reset_mock()
        mock_habit_for_habit_class_tests.reactivate()

        assert mock_habit_for_habit_class_tests.status.value == Status.ACTIVE.value
        mock_dependencies["habit_repo"].update.assert_called_once_with(mock_habit_for_habit_class_tests)
        mock_dependencies["task_manager"].create_first_task.assert_called_once_with(mock_habit_for_habit_class_tests)

    def test_delete_habit(self, mock_habit_for_habit_class_tests, mock_dependencies):
        mock_habit_for_habit_class_tests.delete()
        
        mock_dependencies["habit_repo"].delete.assert_called_once_with(mock_habit_for_habit_class_tests)
        mock_dependencies["task_manager"].delete_current_task.assert_called_once_with(mock_habit_for_habit_class_tests)

class TestHabitCalculateStreak:

    def test_calculate_streak(self, mock_habit_for_habit_class_tests, mock_dependencies):
        mock_habit_for_habit_class_tests.calculate_current_streak()
        mock_dependencies["record_analyzer"].calculate_streak.assert_called_once_with(mock_habit_for_habit_class_tests)


