from unittest.mock import Mock
from source.exceptions import DatabaseFetchDataError
import pytest
from source.habit import Habit
from source.enums import Period, Status
from source.repository_modules import HabitRepository
import datetime
import sqlite3

# Most of the repository functions are strongly coupled with the database, so they cannot be tested in isolation.
# Therefore, they cannot be tested in a unit test, but must be tested in an integration test instead.
# See test_integration.py for detailes integration testing.

@pytest.fixture
def mock_habit_repo(db_path_for_testing):
    return HabitRepository(db_path_for_testing)

class TestHabitRepoInitialization:

    def test_db_path(self, mock_habit_repo, db_path_for_testing):
        assert mock_habit_repo.db_path == db_path_for_testing
        assert mock_habit_repo.conn is None

class TestHabitReadFromDatabase:
    """Test Class that explicitly tests the read-only methods of the HabitRepository class."""

    @pytest.fixture(autouse=True, scope="function")
    def cursor(self, mock_habit_repo):
        """Setup the mock cursor before each test. This ensures that each test starts with a clean cursor state."""
        mock_habit_repo.conn = Mock()
        mock_habit_repo.cursor = Mock()

    @pytest.mark.parametrize("match",
                             [[],[(1,)],[(1,),(2,)],[(1,),(2,),(3,)]],
                             ids=["no match","1 match", "2 matches", "3 matches"])
    def test_duplicate_naming_count(self, mock_habit_repo, mock_habit, match):
        """Check whether the number of duplicate habits is returned correctly."""
        mock_habit_repo.cursor.fetchall.return_value = match

        result = mock_habit_repo.duplicate_naming(mock_habit)

        assert result == len(match)
        assert isinstance(result, int)

    def test_duplicate_exception(self, mock_habit_repo, mock_habit):
        """Test the exception handling when fetching duplicate habits."""
        mock_habit_repo.cursor.execute.side_effect = sqlite3.Error("Some error")

        with pytest.raises(DatabaseFetchDataError) as e:
            mock_habit_repo.duplicate_naming(mock_habit)

        assert f"Error while finding duplicates" in str(e.value)

    @pytest.mark.parametrize("found_ids",
                             [[], [(100,)], [(12,), (25,)], [(55,), (42,), (12,)]],
                             ids=["0 habits", "1 habit", "2 habits", "3 habits"])
    def test_get_largest_id(self, mock_habit_repo, found_ids):
        """Check whether the largest habit ID is returned correctly."""
        mock_habit_repo.cursor.fetchall.return_value = found_ids
        list_of_ids = [i[0] for i in found_ids]

        result = mock_habit_repo.get_largest_id()

        assert result == max(list_of_ids, default=0)
        assert isinstance(result, int)

    def test_get_largest_id_exception(self, mock_habit_repo):
        """Test the exception handling when fetching the largest habit ID."""
        mock_habit_repo.cursor.execute.side_effect = sqlite3.Error("Some error")

        with pytest.raises(DatabaseFetchDataError) as e:
            mock_habit_repo.get_largest_id()

        assert f"Error while fetching largest ID" in str(e.value)

    # Logic of find_by_habit_name(),find_habit_by_id() and browse_all() take place within the database mainly.
    # Therefore, they cannot be adequately tested in a unit test, but must be tested in integration test instead.



