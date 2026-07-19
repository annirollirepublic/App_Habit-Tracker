from source.helpers.utils_datetime_helper import string_to_dt
from source.helpers.enums import CompletionStatus

import pytest
pytestmark = pytest.mark.unit
from datetime import timedelta

class TestTaskManagerInitialization:

    def test_create_task_new(self, mock_dependencies, mock_manager, mock_habit):
        mock_dependencies["task_repo"].find_by_habit_id.return_value = None

        result = mock_manager.create_first_task(mock_habit)

        assert result.habit_name == mock_habit.habit_name
        assert result.habit_id == mock_habit.habit_id
        assert result.due_date == mock_habit.start_date
        assert result.completion_status.value == CompletionStatus.PENDING.value

    def test_create_task_from_db(self, mock_dependencies, mock_manager, mock_habit, sample_task):
        mock_dependencies["task_repo"].find_by_habit_id.return_value = sample_task

        result = mock_manager.create_first_task(mock_habit)

        assert result.habit_name == sample_task["habit_name"]
        assert result.habit_id == sample_task["habit_id"]
        assert result.due_date == string_to_dt(sample_task["due_date"])
        assert result.completion_status.value == sample_task["completion_status"]

class TestTaskManagerInteraction:

    def test_complete_task(self, mock_manager, mock_habit, mock_dependencies, sample_task, mock_task):
        mock_manager.task = mock_task
        mock_dependencies["task_repo"].find_by_habit_id.return_value = sample_task
        result = mock_manager.complete_current_task(mock_habit)

        # Check record repository was called for record creation
        mock_dependencies["record_repo"].create.assert_called_once()
        provided_status = mock_dependencies["record_repo"].create.call_args[0][0][-1]
        assert provided_status == "Completed"

        # Check whether task repository was called for deletion of old an creation of new task
        mock_dependencies["task_repo"].delete.assert_called_once()
        mock_dependencies["task_repo"].create.assert_called_once()

        # Check whether new due_date was calculated correctly
        assert result.due_date == string_to_dt(sample_task["due_date"]) + timedelta(days=mock_habit.period.value)

    def test_skip_task(self, mock_manager, mock_habit, mock_dependencies, sample_task, mock_task):
        mock_manager.task = mock_task
        mock_dependencies["task_repo"].find_by_habit_id.return_value = sample_task
        result = mock_manager.skip_current_task(mock_habit)

        # Check record repository was called for record creation
        mock_dependencies["record_repo"].create.assert_called_once()
        provided_status = mock_dependencies["record_repo"].create.call_args[0][0][-1]
        assert provided_status == "Skipped"

        # Check whether task repository was called for deletion of old an creation of new task
        mock_dependencies["task_repo"].delete.assert_called_once()
        mock_dependencies["task_repo"].create.assert_called_once()

        # Check whether new due_date was calculated correctly
        assert result.due_date == string_to_dt(sample_task["due_date"]) + timedelta(days=mock_habit.period.value)

    def test_delete_task(self, mock_manager, mock_dependencies, mock_task):
        mock_manager.task = mock_task
        mock_manager.delete_current_task()

        # Check whether task repository was called for deletion of old an creation of new task
        mock_dependencies["task_repo"].delete.assert_called_once()

    def test_update_task_no_time_related_changes(self, mock_manager, mock_habit, mock_dependencies, sample_task, mock_task, mocker):
        """Tests that task is UPDATED when habit_name changes, but due_date stays the same (period/start_date unchanged)."""

        # Setup mocks
        mock_manager.task = mock_task
        mock_dependencies["task_repo"].find_by_habit_id.return_value = [sample_task]

        # Mock HabitRepository inside TaskManager module (source.manager_modules)
        mock_habit_repo = mocker.patch("source.manager_modules.HabitRepository")
        mock_habit_repo.return_value.find_by_habit_id.return_value = [{
            "habit_name": "Old Name",  # Different name triggers update
            "habit_id": mock_habit.habit_id,
            "period": mock_habit.period.value,  # SAME period
            "start_date": mock_habit.start_date.strftime("%Y-%m-%d"),  # SAME start_date
            "status": "Active"
        }]

        # Mock CompletionRecordRepository inside TaskManager module
        mock_record_repo = mocker.patch("source.manager_modules.CompletionRecordRepository")
        mock_record_repo.return_value.find_by_habit_id.return_value = []  # No records → last_record_date = None

        result = mock_manager.update_current_task(mock_habit)

        # Task SHOULD be updated (habit_name changed)
        mock_dependencies["task_repo"].update.assert_called_once()
        mock_dependencies["record_repo"].update.assert_called_once_with((mock_habit.habit_name, mock_habit.habit_id))

        # But due_date should NOT be recalculated (period/start_date unchanged)
        assert result.due_date == string_to_dt(sample_task["due_date"])

    def test_update_task_time_related_changes(self, mock_manager, mock_habit, mock_dependencies, sample_task, mock_task, mocker):
        """Tests that task IS updated when period or start_date changes, with recalculated due_date."""

        # Setup mocks
        mock_manager.task = mock_task
        mock_dependencies["task_repo"].find_by_habit_id.return_value = [sample_task]

        # Mock HabitRepository with DIFFERENT period
        mock_habit_repo = mocker.patch("source.manager_modules.HabitRepository")
        mock_habit_repo.return_value.find_by_habit_id.return_value = [{
            "habit_name": "Different Name",
            "habit_id": mock_habit.habit_id,
            "period": 7,  # DIFFERENT from mock_habit.period.value
            "start_date": mock_habit.start_date.strftime("%Y-%m-%d"),
            "status": "Active"
        }]

        # Mock CompletionRecordRepository with no records
        mock_record_repo = mocker.patch("source.manager_modules.CompletionRecordRepository")
        mock_record_repo.return_value.find_by_habit_id.return_value = []

        result = mock_manager.update_current_task(mock_habit)

        # Both repos should be called (period changed → task needs recalculation)
        mock_dependencies["task_repo"].update.assert_called_once()
        mock_dependencies["record_repo"].update.assert_called_once()

        # Due date SHOULD be recalculated (period changed)
        days_diff = abs((result.due_date - mock_habit.start_date).days)
        assert days_diff % mock_habit.period.value == 0 or days_diff < mock_habit.period.value

        # Due date should be >= old due_date (respecting the while loop logic)
        assert result.due_date >= string_to_dt(sample_task["due_date"])

    def test_update_task_complete_no_changes(self, mock_manager, mock_habit, mock_dependencies, sample_task, mock_task, mocker):
        """Tests that task is NOT updated when NOTHING changed (same name, period, start_date)."""

        # Setup mocks
        mock_manager.task = mock_task
        mock_dependencies["task_repo"].find_by_habit_id.return_value = [sample_task]

        # Mock HabitRepository with EXACTLY SAME data
        mock_habit_repo = mocker.patch("source.manager_modules.HabitRepository")
        mock_habit_repo.return_value.find_by_habit_id.return_value = [{
            "habit_name": mock_habit.habit_name,  # SAME
            "habit_id": mock_habit.habit_id,
            "period": mock_habit.period.value,  # SAME
            "start_date": mock_habit.start_date.strftime("%Y-%m-%d"),  # SAME
            "status": "Active"
        }]

        # Mock CompletionRecordRepository with no records
        mock_record_repo = mocker.patch("source.manager_modules.CompletionRecordRepository")
        mock_record_repo.return_value.find_by_habit_id.return_value = []

        result = mock_manager.update_current_task(mock_habit)

        # Nothing should be updated (no changes at all)
        mock_dependencies["task_repo"].update.assert_not_called()
        mock_dependencies["record_repo"].update.assert_not_called()

    def test_update_task_with_last_record_date(self, mock_manager, mock_habit, mock_dependencies, sample_task, mock_task, mocker):
        """Tests that new due_date respects last_record_date when calculating (handles overdue case)."""

        # Setup mocks
        mock_manager.task = mock_task
        mock_dependencies["task_repo"].find_by_habit_id.return_value = [sample_task]

        # Mock HabitRepository with CHANGED period (triggers recalculation)
        mock_habit_repo = mocker.patch("source.manager_modules.HabitRepository")
        mock_habit_repo.return_value.find_by_habit_id.return_value = [{
            "habit_name": "Changed Name",
            "habit_id": mock_habit.habit_id,
            "period": 14,  # Changed to biweekly
            "start_date": mock_habit.start_date.strftime("%Y-%m-%d"),
            "status": "Active"
        }]

        # Mock CompletionRecordRepository WITH records (so last_record_date is set)
        mock_record_repo = mocker.patch("source.manager_modules.CompletionRecordRepository")
        mock_record_repo.return_value.find_by_habit_id.return_value = [
            {
                "habit_name": mock_habit.habit_name,
                "habit_id": mock_habit.habit_id,
                "period": 1,
                "due_date": "2026-01-15",
                "was_overdue": 0,
                "completion_date": "2026-01-16",  # Last completed task
                "completion_status": "Completed"
            }
        ]

        result = mock_manager.update_current_task(mock_habit)

        # Task should be updated
        mock_dependencies["task_repo"].update.assert_called_once()

        # Due date should be calculated AFTER last_record_date
        last_record_date = string_to_dt("2026-01-16")
        assert result.due_date > last_record_date