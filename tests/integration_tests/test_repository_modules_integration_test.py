# Test Connection Repositories <> Database
from unittest.mock import Mock

from source.helpers.enums import Period
from source.app_logic.habit import Habit

import pytest

from source.helpers.utils_datetime_helper import dt_to_string
from tests.conftest import mock_habit

pytestmark = pytest.mark.integration
import datetime


class TestHabitRepositoryIntegrationSetup:

    def test_table_creation(self, habit_repo_with_temp_path):
        """Test that the habit table is created and has the correct columns"""

        # Tigger connection setup
        # This will create the table if it doesn't exist
        habit_repo_with_temp_path._ensure_connection()

        # Get the table info
        habit_repo_with_temp_path.cursor.execute("PRAGMA table_info(habits)")
        columns = habit_repo_with_temp_path.cursor.fetchall()

        # Check the column names
        column_names = [column[1] for column in columns]
        assert column_names == [
            "habit_name",
            "habit_id",
            "period",
            "start_date",
            "status",
        ]


class TestHabitRepositoryRead:

    def test_find_by_id(self, habit_repo_with_reg_path):
        """Test that a habit can be found by its ID"""

        # Search a habit by its ID
        result = habit_repo_with_reg_path.find_by_habit_id(9876)

        # Check against the expected results
        assert len(result) == 1
        assert result[0]["habit_id"] == 9876
        assert result[0]["habit_name"] == "Drink Water"
        assert result[0]["start_date"] == "2023-05-12"
        assert result[0]["period"] == 1
        assert result[0]["status"] == "Active"

    def test_find_by_name(self, habit_repo_with_reg_path):
        """Test that a habit can be found by its name"""

        # Search a habit by its name
        result = habit_repo_with_reg_path.find_by_habit_name("Stretching Routine")

        # Check against the expected results
        assert len(result) == 1
        assert result[0]["habit_id"] == 5432
        assert result[0]["habit_name"] == "Stretching Routine"
        assert result[0]["start_date"] == "1999-01-01"
        assert result[0]["period"] == 1
        assert result[0]["status"] == "Active"

    def test_browse_all(self, habit_repo_with_reg_path):
        """Test that all habits can be found and returned correctly"""

        # Search for all habits
        result = habit_repo_with_reg_path.browse_all()

        # Extract the expected results to list format
        habit_ids = [habit["habit_id"] for habit in result]
        habit_names = [habit["habit_name"] for habit in result]
        habit_periods = [habit["period"] for habit in result]
        habit_start_dates = [habit["start_date"] for habit in result]
        habit_statuses = [habit["status"] for habit in result]

        # Expected results
        expected_habit_ids = [9876, 8765, 7654, 6543, 5432]
        expected_habit_names = ["Drink Water", "Read 50 Pages", "Write Blog", "Change Bed Laundry", "Stretching Routine"]
        expected_habit_periods = [1, 7, 30, 14, 1]
        expected_start_dates = ["2023-05-12", "2024-01-24", "2025-06-15", "2026-03-12", "1999-01-01"]
        expected_statuses = ["Active", "Paused", "Active", "Active", "Active"]

        # Check if the results match the expected values (independent of order)
        assert len(result) == 5
        assert sorted(habit_ids) == sorted(expected_habit_ids)
        assert sorted(habit_names) == sorted(expected_habit_names)
        assert sorted(habit_periods) == sorted(expected_habit_periods)
        assert sorted(habit_start_dates) == sorted(expected_start_dates)
        assert sorted(habit_statuses) == sorted(expected_statuses)

    def test_get_largest_id(self, habit_repo_with_reg_path): #only for habit repository
        """Test that the largest habit ID can be retrieved"""

        # Get the largest habit ID
        result = habit_repo_with_reg_path.get_largest_id()

        # Check against the expected result
        assert result == 9876

    def test_duplicate_naming(self, habit_repo_with_reg_path, monkeypatch): #only for habit repository
        """Test that a duplicate habit name is detected and returns 1"""

        # Mock habit object with a duplicate habit name
        mock_habit = Mock(spec=Habit)
        mock_habit.habit_name = "Write Blog"

        # Check for duplicates to mocked habit object
        result = habit_repo_with_reg_path.duplicate_naming(mock_habit)

        # Check result against expected value
        assert result == 1


class TestHabitRepositoryWrite:

    def test_create_record(self, mock_habit, habit_repo_with_temp_path):
        """Test that a habit can be created and saved to the database"""

        # Create a habit record using a mock habit object
        habit_repo_with_temp_path.create(mock_habit)

        # Search for the created habit in the database
        result = habit_repo_with_temp_path.find_by_habit_id(mock_habit.habit_id)

        # Check if created habit in database matches expected values
        assert len(result) == 1
        assert result[0]["habit_id"] == mock_habit.habit_id
        assert result[0]["habit_name"] == mock_habit.habit_name
        assert result[0]["start_date"] == dt_to_string(mock_habit.start_date)
        assert result[0]["period"] == mock_habit.period.value
        assert result[0]["status"] == mock_habit.status.value

    def test_update_record(self, mock_habit, habit_repo_with_temp_path):
        """Test that a habit can be updated and saved to the database"""

        # Create a habit record using a mock habit object
        habit_repo_with_temp_path.create(mock_habit)

        # Change the habit name and update the habit record
        mock_habit.habit_name = "Changed Habit Name"
        mock_habit.period = Period.DAILY
        mock_habit.start_date = datetime.datetime.today()
        habit_repo_with_temp_path.update(mock_habit)

        # Search for the updated habit in the database
        result = habit_repo_with_temp_path.find_by_habit_id(mock_habit.habit_id)

        # Check if updated habit in database matches expected values
        assert len(result) == 1
        assert result[0]["habit_id"] == mock_habit.habit_id #ID will not change
        assert result[0]["habit_name"] == "Changed Habit Name"
        assert result[0]["start_date"] == dt_to_string(datetime.datetime.today())
        assert result[0]["period"] == Period.DAILY.value
        assert result[0]["status"] == mock_habit.status.value

    def test_delete_record(self, mock_habit, habit_repo_with_temp_path):
        """Test that a habit can be deleted and removed from the database"""

        # Create a habit record using a mock habit object
        habit_repo_with_temp_path.create(mock_habit)

        # Delete the habit record from the database
        habit_repo_with_temp_path.delete(mock_habit)

        # Search for the deleted habit in the database
        result = habit_repo_with_temp_path.find_by_habit_id(mock_habit.habit_id)

        # Check if deleted habit is not found in the database as expected
        assert len(result) == 0


class TestTaskRepositoryIntegrationSetup:

    def test_table_creation(self, task_repo_with_temp_path):
        """Test that the task table is created and has the correct columns"""

        # Trigger connection setup
        # This will create the table if it doesn't exist
        task_repo_with_temp_path._ensure_connection()

        # Get the table info
        task_repo_with_temp_path.cursor.execute("PRAGMA table_info(tasks)")
        columns = task_repo_with_temp_path.cursor.fetchall()

        # Check the column names
        column_names = [column[1] for column in columns]
        assert column_names == [
            "habit_name",
            "habit_id",
            "due_date",
            "is_overdue",
            "completion_status",
        ]


class TestTaskRepositoryRead:

    def test_find_by_id(self, task_repo_with_reg_path):
        """Test that habit ID can find the corresponding task"""

        # Search a task by habit ID
        result = task_repo_with_reg_path.find_by_habit_id(9876)

        # Check against the expected results
        assert len(result) == 1
        assert result[0]["habit_id"] == 9876
        assert result[0]["habit_name"] == "Drink Water"
        assert result[0]["due_date"] == "2026-07-10"
        assert result[0]["is_overdue"] == 0
        assert result[0]["completion_status"] == "Pending"

    def test_find_by_name(self, task_repo_with_reg_path):
        """Test that habit name can find the corresponding task"""

        # Search a task by habit name
        result = task_repo_with_reg_path.find_by_habit_name("Stretching Routine")

        # Check against the expected results
        assert len(result) == 1
        assert result[0]["habit_id"] == 5432
        assert result[0]["habit_name"] == "Stretching Routine"
        assert result[0]["due_date"] == "2026-07-11"
        assert result[0]["is_overdue"] == 0
        assert result[0]["completion_status"] == "Pending"

    def test_browse_all(self, task_repo_with_reg_path):
        """Test that all tasks can be found and returned correctly"""

        # Search for all tasks
        result = task_repo_with_reg_path.browse_all()

        # Extract the expected results to list format
        task_ids = [task["habit_id"] for task in result]
        task_names = [task["habit_name"] for task in result]
        task_due_dates = [task["due_date"] for task in result]
        task_overdue_statuses = [task["is_overdue"] for task in result]
        task_completion_statuses = [task["completion_status"] for task in result]

        # Expected results
        expected_task_ids = [9876, 7654, 6543, 5432]
        expected_task_names = ["Drink Water", "Write Blog", "Change Bed Laundry", "Stretching Routine"]
        expected_task_due_dates = ["2026-07-10", "2026-07-01", "2026-07-15", "2026-07-11"]
        expected_task_overdue_statuses = [0, 1, 0, 0]
        expected_task_completion_statuses = ["Pending", "Pending", "Pending", "Pending"]

        # Check if the results match the expected values (independent of order)
        assert len(result) == 4
        assert sorted(task_ids) == sorted(expected_task_ids)
        assert sorted(task_names) == sorted(expected_task_names)
        assert sorted(task_due_dates) == sorted(expected_task_due_dates)
        assert sorted(task_overdue_statuses) == sorted(expected_task_overdue_statuses)
        assert sorted(task_completion_statuses) == sorted(expected_task_completion_statuses)


class TestTaskRepositoryWrite:

    def test_create_record(self, mock_task, task_repo_with_temp_path):
        """Test that a task can be created and saved to the database"""

        # Create a task record using a mock task object
        task_repo_with_temp_path.create(mock_task)

        # Search for the created task in the database
        result = task_repo_with_temp_path.find_by_habit_id(mock_task.habit_id)

        # Check if created task in database matches expected values
        assert len(result) == 1
        assert result[0]["habit_id"] == mock_task.habit_id
        assert result[0]["habit_name"] == mock_task.habit_name
        assert result[0]["due_date"] == dt_to_string(mock_task.due_date)
        assert result[0]["is_overdue"] == mock_task.is_overdue
        assert result[0]["completion_status"] == mock_task.completion_status.value

    def test_update_record(self, mock_task, task_repo_with_temp_path):
        """Test that a task can be updated and saved to the database"""

        # Create a task record using a mock task object
        task_repo_with_temp_path.create(mock_task)

        # Change the task name and update the task record
        mock_task.habit_name = "Changed Habit Name"
        mock_task.due_date = datetime.datetime.today()
        task_repo_with_temp_path.update(mock_task)

        # Search for the updated task in the database
        result = task_repo_with_temp_path.find_by_habit_id(mock_task.habit_id)

        # Check if updated task in database matches expected values
        assert len(result) == 1
        assert result[0]["habit_id"] == mock_task.habit_id #ID will not change
        assert result[0]["habit_name"] == "Changed Habit Name"
        assert result[0]["due_date"] == dt_to_string(datetime.datetime.today())
        assert result[0]["is_overdue"] == False
        assert result[0]["completion_status"] == mock_task.completion_status.value

    def test_delete_record(self, mock_task, task_repo_with_temp_path):
        """Test that a task can be deleted and removed from the database"""

        # Create a task record using a mock task object
        task_repo_with_temp_path.create(mock_task)

        # Delete the task record from the database
        task_repo_with_temp_path.delete(mock_task)

        # Search for the deleted task in the database
        result = task_repo_with_temp_path.find_by_habit_id(mock_task.habit_id)

        # Check if deleted task is not found in the database as expected
        assert len(result) == 0


class TestRecordRepositoryIntegrationSetup:

    def test_table_creation(self, record_repo_with_temp_path):
        """Test that the record table is created and has the correct columns"""

        # Trigger connection setup
        # This will create the table if it doesn't exist'
        record_repo_with_temp_path._ensure_connection()

        # Get the table info
        record_repo_with_temp_path.cursor.execute("PRAGMA table_info(completion_records)")
        columns = record_repo_with_temp_path.cursor.fetchall()

        # Check the column names
        column_names = [column[1] for column in columns]
        assert column_names == [
            "habit_name",
            "habit_id",
            "period",
            "due_date",
            "was_overdue",
            "completion_date",
            "completion_status",
        ]


class TestRecordRepositoryRead:

    def test_find_by_id(self, record_repo_with_reg_path):
        """Test that habit ID can find the corresponding records"""

        # Search a record by habit ID
        result = record_repo_with_reg_path.find_by_habit_id(9876)

        # Check against the expected results
        assert len(result) == 7
        assert result[0]["habit_id"] == 9876
        assert result[0]["habit_name"] == "Drink Water"

    def test_find_by_name(self, record_repo_with_reg_path):
        """Test that habit name can find the corresponding records"""

        # Search a record by habit name
        result = record_repo_with_reg_path.find_by_habit_name("Stretching Routine")

        # Check against the expected results
        assert len(result) == 11
        assert result[0]["habit_id"] == 5432
        assert result[0]["habit_name"] == "Stretching Routine"

    def test_browse_all(self, record_repo_with_reg_path):
        """Test that all records can be found and returned correctly"""

        # Search for all records
        result = record_repo_with_reg_path.browse_all()

        # Extract the expected results to list format
        record_ids = [task["habit_id"] for task in result]
        record_names = [task["habit_name"] for task in result]

        # Expected results
        expected_record_amt_9876 = 7
        expected_record_amt_5432 = 11
        expected_record_amt_7654 = 3
        expected_record_amt_6543 = 1

        expected_record_amt_drink_water = 7
        expected_record_amt_write_blog = 3
        expected_record_amt_change_bed_laundry = 1
        expected_record_amt_stretching_routine = 11

        # Check if the results match the expected values
        assert len(record_ids) == 22
        assert len(record_names) == 22
        assert record_ids.count(9876) == expected_record_amt_9876
        assert record_ids.count(5432) == expected_record_amt_5432
        assert record_ids.count(7654) == expected_record_amt_7654
        assert record_ids.count(6543) == expected_record_amt_6543
        assert record_names.count("Drink Water") == expected_record_amt_drink_water
        assert record_names.count("Write Blog") == expected_record_amt_write_blog
        assert record_names.count("Change Bed Laundry") == expected_record_amt_change_bed_laundry
        assert record_names.count("Stretching Routine") == expected_record_amt_stretching_routine


class TestRecordRepositoryWrite:

    def test_create_record(self, mock_record_tuple, record_repo_with_temp_path):
        """Test that a record can be created and saved to the database"""

        # Create a record using a mock record tuple
        record_repo_with_temp_path.create(mock_record_tuple)

        # Search for the created record in the database
        result = record_repo_with_temp_path.find_by_habit_id(mock_record_tuple[1])

        # Check if created record in database matches expected values
        assert len(result) == 1
        assert result[0]["habit_name"] == mock_record_tuple[0]
        assert result[0]["habit_id"] == mock_record_tuple[1]
        assert result[0]["period"] == mock_record_tuple[2]
        assert result[0]["due_date"] == dt_to_string(mock_record_tuple[3])
        assert result[0]["was_overdue"] == mock_record_tuple[4]
        assert result[0]["completion_date"] == dt_to_string(mock_record_tuple[5])
        assert result[0]["completion_status"] == mock_record_tuple[6]

    def test_update_record(self, mock_record_tuple, record_repo_with_temp_path):
        """Test that a record can be updated and saved to the database"""

        # Create a record using a mock record tuple
        record_repo_with_temp_path.create(mock_record_tuple)

        # Change the record name and update the record
        habit_name, habit_id, period, due_date, was_overdue, completion_date, completion_status = mock_record_tuple
        mock_record_tuple_new = ("Changed Habit Name", habit_id)
        record_repo_with_temp_path.update(mock_record_tuple_new)

        # Search for the updated record in the database
        result = record_repo_with_temp_path.find_by_habit_id(mock_record_tuple[1])

        # Check if updated record in database matches expected values
        assert len(result) == 1
        assert result[0]["habit_name"] == "Changed Habit Name"

    def test_delete_record(self, mock_record_tuple, record_repo_with_temp_path):
        """Test that a record can be deleted and removed from the database"""

        # Create a record using a mock record tuple
        record_repo_with_temp_path.create(mock_record_tuple)

        # Delete the record from the database
        record_repo_with_temp_path.delete(mock_record_tuple)

        # Search for the deleted record in the database
        result = record_repo_with_temp_path.find_by_habit_id(mock_record_tuple[1])

        # Check if deleted record is not found in the database as expected
        assert len(result) == 0