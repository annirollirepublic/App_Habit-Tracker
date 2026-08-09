# Import pytest to mark tests as unit tests
import pytest
pytestmark = pytest.mark.unit

class TestAnalyzerCalculations:

    def test_calculate_streak(self, mock_habit, mock_dependencies, sample_records, mock_analyzer):
        """Test that the streak is calculated correctly."""

        # Mock the habit's records to return the sample records from conftest.py
        mock_dependencies["record_repo"].find_by_habit_id.return_value = sample_records[0]

        # Call the function to test
        result = mock_analyzer.calculate_streak(mock_habit)

        # Check against the expected streak value
        assert result == sample_records[1]["streak"]

    def test_calculate_longest_streak(self, mock_habit, mock_dependencies, sample_records, mock_analyzer):
        """Test that the longest streak is calculated correctly."""

        # Mock the habit's records to return the sample records from conftest.py
        mock_dependencies["record_repo"].find_by_habit_id.return_value = sample_records[0]

        # Call the function to test
        result = mock_analyzer.calculate_longest_streak(mock_habit)

        # Check against the expected longest streak value
        assert result == sample_records[1]["longest"]

    def test_calculate_completion_rate(self, mock_habit, mock_dependencies, sample_records, mock_analyzer):
        """Test that the completion rate is calculated correctly."""

        # Mock the habit's records to return the sample records from conftest.py
        mock_dependencies["record_repo"].find_by_habit_id.return_value = sample_records[0]

        # Call the function to test
        result = mock_analyzer.calculate_completion_rate(mock_habit)

        # Check against the expected completion rate value
        assert result == pytest.approx(sample_records[1]["rate"], rel=0.01)

    def test_calculate_finished_on_time(self, mock_habit, mock_dependencies, sample_records, mock_analyzer):
        """Test that the finished on-time rate is calculated correctly."""

        # Mock the habit's records to return the sample records from conftest.py'
        mock_dependencies["record_repo"].find_by_habit_id.return_value = sample_records[0]

        # Call the function to test
        result = mock_analyzer.calculate_finished_ontime_rate(mock_habit)

        # Check against the expected finished on-time rate value
        assert result == pytest.approx(sample_records[1]["on_time"], rel=0.01)

