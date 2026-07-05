# Test Connection Repositories <> Database
from source.repository_modules import HabitRepository, TaskRepository, CompletionRecordRepository
from source.enums import Period, Status

import pytest

from source.utils_datetime_helper import dt_to_string
from tests.conftest import mock_habit

pytestmark = pytest.mark.integration
import datetime

# TODO: How can I assure, that the input database is always suitable for testing?

@pytest.fixture
def habit_repo(db_path_for_testing):
    return HabitRepository(db_path=db_path_for_testing)

# @pytest.fixture
# def task_repo(db_path_for_testing):
#     return TaskRepository(db_path=db_path_for_testing)
#
# @pytest.fixture
# def record_repo(db_path_for_testing):
#     return RecordRepository(db_path=db_path_for_testing)

class TestHabitRepositoryIntegrationSetup:

    def test_table_creation(self, mock_habit, habit_repo):

        assert True

class TestHabitRepositoryIntegration:

    def test_create_record(self, mock_habit, habit_repo):
        habit_repo.create(mock_habit)

        result = habit_repo.find_by_habit_id(mock_habit.habit_id)

        assert len(result) == 1
        assert result[0]["habit_id"] == mock_habit.habit_id
        assert result[0]["habit_name"] == mock_habit.habit_name
        assert result[0]["start_date"] == dt_to_string(mock_habit.start_date)
        assert result[0]["period"] == mock_habit.period.value
        assert result[0]["status"] == mock_habit.status.value

    def test_update_record(self, mock_habit, habit_repo):
        mock_habit.habit_name = "Changed Habit Name"
        mock_habit.period = Period.DAILY
        mock_habit.start_date = datetime.datetime.today()
        habit_repo.update(mock_habit)

        result = habit_repo.find_by_habit_id(mock_habit.habit_id)

        assert len(result) == 1
        assert result[0]["habit_id"] == mock_habit.habit_id #ID will not change
        assert result[0]["habit_name"] == "Changed Habit Name"
        assert result[0]["start_date"] == dt_to_string(datetime.datetime.today())
        assert result[0]["period"] == Period.DAILY.value
        assert result[0]["status"] == mock_habit.status.value

    def test_delete_record(self):
        pass

    def test_find_by_id(self):
        pass

    def test_find_by_name(self):
        pass

    def test_browse_all(self):
        pass

    def test_get_largest_id(self): #only for habit repository
        pass

    def test_duplicate_naming(self): #only for habit repository
        pass

    def test_empty_db_behavior(self):
        pass