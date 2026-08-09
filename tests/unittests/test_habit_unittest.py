# Import pytest to mark tests as unit tests
import pytest
pytestmark = pytest.mark.unit

# Import necessary modules from source
from source.helpers.exceptions import DuplicateHabitError
from source.app_logic.habit import Habit
from source.helpers.enums import Period, Status

# Import datetime for datetime calculations
from datetime import datetime

class TestHabitInitialization:

    def test_handling_duplicate_naming(self, mock_habit_for_habit_class_tests, mock_dependencies):
        """Test that a DuplicateHabitError is raised when a habit with the same name already exists."""

        # Set duplicates to 1 temporally to test
        mock_dependencies["habit_repo"].duplicate_naming.return_value = 1

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
        """Test that the habit is initially in an active status."""

        assert mock_habit_for_habit_class_tests.status.value == Status.ACTIVE.value

    def test_calculated_id(self, mock_habit_for_habit_class_tests):
        """Test that the habit ID is calculated correctly."""

        assert mock_habit_for_habit_class_tests.habit_id == 101

    def test_initial_default_start_date(self, mock_habit_for_habit_class_tests):
        """Test that the habit's start date is set to the current date."""

        # Check whether start date is within 5 seconds of current date (handle edge case of midnight habit creation) 
        assert abs((mock_habit_for_habit_class_tests.start_date - datetime.today()).total_seconds()) < 10


class TestHabitInstantiateDependencies:

    def test_habit_repo_instantiation(self, mock_habit_for_habit_class_tests, mock_dependencies):
        """Test that the habit repository is instantiated correctly."""

        mock_dependencies["HabitRepoClass"].assert_called_once_with()
        mock_dependencies["habit_repo"].create.assert_called_once_with(mock_habit_for_habit_class_tests)

    def test_task_repo_instantiation(self, mock_habit_for_habit_class_tests, mock_dependencies):
        """Test that the task repository is instantiated correctly."""

        mock_dependencies["TaskRepoClass"].assert_called_once_with()

    def test_record_repo_instantiation(self, mock_habit_for_habit_class_tests, mock_dependencies):
        """Test that the record repository is instantiated correctly."""

        mock_dependencies["RecordRepoClass"].assert_called_once_with()

    def test_task_manager_instantiation(self, mock_habit_for_habit_class_tests, mock_dependencies):
        """Test that the task manager is instantiated correctly."""

        mock_dependencies["TaskManagerClass"].assert_called_once_with(mock_dependencies["task_repo"], mock_dependencies["record_repo"])
        mock_dependencies["task_manager"].create_first_task.assert_called_once_with(mock_habit_for_habit_class_tests)

    def test_record_analyzer_instantiation(self, mock_habit_for_habit_class_tests, mock_dependencies):
        """Test that the record analyzer is instantiated correctly."""

        mock_dependencies["RecordAnalyzerClass"].assert_called_once_with(mock_dependencies["record_repo"])


class TestHabitSetterMethods:

    def test_set_habit_name(self, mock_habit_for_habit_class_tests, mock_dependencies):
        """Test that the habit name can be set correctly."""

        # Set habit name
        mock_habit_for_habit_class_tests.habit_name = "New Habit Name"

        # Check whether habit name was set correctly and dependencies were called
        assert mock_habit_for_habit_class_tests.habit_name == "New Habit Name"
        mock_dependencies["habit_repo"].update.assert_called_once_with(mock_habit_for_habit_class_tests)
        mock_dependencies["task_manager"].update_current_task.assert_called_once_with(mock_habit_for_habit_class_tests)

    def test_set_period(self, mock_habit_for_habit_class_tests, mock_dependencies):
        """Test that the habit period can be set correctly."""

        # Set habit period
        mock_habit_for_habit_class_tests.period = Period.WEEKLY

        # Check whether habit period was set correctly and dependencies were called
        assert mock_habit_for_habit_class_tests.period == Period.WEEKLY
        mock_dependencies["habit_repo"].update.assert_called_once_with(mock_habit_for_habit_class_tests)
        mock_dependencies["task_manager"].update_current_task.assert_called_once_with(mock_habit_for_habit_class_tests)

    def test_set_start_date(self, mock_habit_for_habit_class_tests, mock_dependencies,):
        """Test that the habit start date can be set correctly."""

        # Set habit start date
        mock_habit_for_habit_class_tests.start_date = "2023-01-01"

        # Check whether habit start date was set correctly and dependencies were called
        assert mock_habit_for_habit_class_tests.start_date == "2023-01-01"
        mock_dependencies["habit_repo"].update.assert_called_once_with(mock_habit_for_habit_class_tests)
        mock_dependencies["task_manager"].update_current_task.assert_called_once_with(mock_habit_for_habit_class_tests)


class TestHabitInteraction:

    def test_complete_habit(self, mock_habit_for_habit_class_tests, mock_dependencies):
        """Test that the habit can be completed."""

        # Complete habit
        mock_habit_for_habit_class_tests.complete()

        # Check whether dependencies were called with the correct method
        mock_dependencies["task_manager"].complete_current_task.assert_called_once_with(mock_habit_for_habit_class_tests)

    def test_skip_habit(self, mock_habit_for_habit_class_tests, mock_dependencies):
        """Test that the habit can be skipped."""

        # Skip habit
        mock_habit_for_habit_class_tests.skip()

        # Check whether dependencies were called with the correct method
        mock_dependencies["task_manager"].skip_current_task.assert_called_once_with(mock_habit_for_habit_class_tests)

    def test_pause_habit(self, mock_habit_for_habit_class_tests, mock_dependencies):
        """Test that the habit can be paused."""

        # Pause habit
        mock_habit_for_habit_class_tests.pause()

        # Check whether habit status was set to paused and dependencies were called
        assert mock_habit_for_habit_class_tests.status.value == Status.PAUSED.value
        mock_dependencies["habit_repo"].update.assert_called_once_with(mock_habit_for_habit_class_tests)
        mock_dependencies["task_manager"].delete_current_task.assert_called_once_with(mock_habit_for_habit_class_tests)

    def test_reactivate_habit(self, mock_habit_for_habit_class_tests, mock_dependencies):
        """Test that the habit can be reactivated."""

        # Reset first task creation mock - fist task creation cannot be called twice
        mock_dependencies["task_manager"].create_first_task.reset_mock()
        # Reactivate habit
        mock_habit_for_habit_class_tests.reactivate()

        # Check whether habit status was set to active and dependencies were called
        assert mock_habit_for_habit_class_tests.status.value == Status.ACTIVE.value
        assert mock_dependencies["habit_repo"].update.call_count == 2
        mock_dependencies["task_manager"].create_first_task.assert_called_once_with(mock_habit_for_habit_class_tests)

    def test_delete_habit(self, mock_habit_for_habit_class_tests, mock_dependencies):
        """Test that the habit can be deleted."""

        # Delete habit
        mock_habit_for_habit_class_tests.delete()

        # Check whether dependencies were called with the correct method
        mock_dependencies["habit_repo"].delete.assert_called_once_with(mock_habit_for_habit_class_tests)
        mock_dependencies["task_manager"].delete_current_task.assert_called_once_with(mock_habit_for_habit_class_tests)


class TestHabitCalculateStreak:

    def test_calculate_streak(self, mock_habit_for_habit_class_tests, mock_dependencies):
        """Test that the habit streak is called correctly."""

        # Call calculate_streak method
        mock_habit_for_habit_class_tests.calculate_current_streak()

        # Check whether dependencies were called with the correct method
        mock_dependencies["record_analyzer"].calculate_streak.assert_called_once_with(mock_habit_for_habit_class_tests)


