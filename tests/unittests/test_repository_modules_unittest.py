# Import pytest to mark tests as unit tests
import pytest
pytestmark = pytest.mark.unit
# Import mock to mock dependencies
from unittest.mock import Mock

# Import necessary modules from source
from source.repository.repository_modules import HabitRepository

# Most of the repository functions are strongly coupled with the database, so they cannot be tested in isolation.
# Therefore, they cannot be tested in an unittest but must be tested in an integration test instead.
# See test_integration.py for detailes integration testing.

# Mock the habit repository
@pytest.fixture
def mock_habit_repo(db_path_for_testing):
    return HabitRepository(db_path_for_testing)

class TestHabitRepoInitialization:

    def test_db_path(self, mock_habit_repo, db_path_for_testing):
        """Test that the database path is correctly set and the connection is not established."""

        assert mock_habit_repo.db_path == db_path_for_testing
        assert mock_habit_repo.conn is None

class TestHabitReadFromDatabase:
    """Test Class that explicitly tests the read-only methods of the HabitRepository class."""

    @pytest.fixture(autouse=True, scope="function")
    def mock_connection_and_cursor(self, mock_habit_repo):
        """Prepare a mocked connection and cursor before each test."""
        mock_habit_repo.conn = Mock()
        mock_habit_repo.cursor = Mock()

    @pytest.mark.parametrize("match",
                             [[],[(1,)],[(1,),(2,)],[(1,),(2,),(3,)]],
                             ids=["no match","1 match", "2 matches", "3 matches"])
    def test_duplicate_naming_count(self, mock_habit_repo, mock_habit, match):
        """Check whether the number of duplicate habits is returned correctly."""

        # Mock the habit_repo.cursor.fetchall() method to return the match list
        mock_habit_repo.cursor.fetchall.return_value = match

        # Call the duplicate_naming() method
        result = mock_habit_repo.duplicate_naming(mock_habit)

        # Check the result against the expected values
        assert result == len(match)
        assert isinstance(result, int)
        mock_habit_repo.cursor.execute.assert_called_once()
        mock_habit_repo.cursor.fetchall.assert_called_once()

    @pytest.mark.parametrize("found_ids",
                             [[], [(100,)], [(12,), (25,)], [(55,), (42,), (12,)]],
                             ids=["0 habits", "1 habit", "2 habits", "3 habits"])
    def test_get_largest_id(self, mock_habit_repo, found_ids):
        """Check whether the largest habit ID is returned correctly."""

        # Mock the habit_repo.cursor.fetchall() method to return the found_ids list
        mock_habit_repo.cursor.fetchall.return_value = found_ids
        list_of_ids = [i[0] for i in found_ids]

        # Call the get_largest_id() method
        result = mock_habit_repo.get_largest_id()

        # Check the result against the expected values
        assert result == max(list_of_ids, default=0)
        assert isinstance(result, int)
        mock_habit_repo.cursor.execute.assert_called_once()
        mock_habit_repo.cursor.fetchall.assert_called_once()

    # Logic of find_by_habit_name(),find_habit_by_id() and browse_all() take place within the database mainly.
    # Therefore, they cannot be adequately tested in a unit test but must be tested in an integration test instead.



