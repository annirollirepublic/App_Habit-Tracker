from source.utils_datetime_helper import string_to_dt
from datetime import timedelta

class TestTaskManagerInitialization:

    def test_create_task_new(self, mock_dependencies, mock_manager, mock_habit):
        mock_dependencies["task_repo"].find_by_habit_id.return_value = None

        result = mock_manager.create_first_task(mock_habit)

        assert result.habit_name == mock_habit.habit_name
        assert result.habit_id == mock_habit.habit_id
        assert result.due_date == mock_habit.start_date
        assert result.completion_status.value == "Pending"

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

    def test_update_task(self, mock_manager, mock_habit, mock_dependencies, sample_task, mock_task):
        mock_manager.task = mock_task
        mock_dependencies["task_repo"].find_by_habit_id.return_value = sample_task
        result = mock_manager.update_current_task(mock_habit)

        # We expect the due_date to be updated and that it is greater or the same as the last due_date in sample_task
        assert result.due_date >= string_to_dt(sample_task["due_date"])

        # We expect the perioidicty to be respected in the calculation of the new due_date
        assert abs((result.due_date - mock_habit.start_date).days) % mock_habit.period.value == 0

        # Check whether task repository was called to update task record
        mock_dependencies["task_repo"].update.assert_called_once()
        mock_dependencies["record_repo"].update.assert_called_once_with((mock_habit.habit_name, mock_habit.habit_id))

