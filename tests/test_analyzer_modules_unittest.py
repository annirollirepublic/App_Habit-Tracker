from source.analyzer_modules import RecordAnalyzer
import pytest

class TestAnalyzerCalculations:

    def test_calculate_streak(self, mock_habit, mock_dependencies, sample_records):
        mock_dependencies["record_repo"].find_by_habit_id.return_value = sample_records[0]
        mock_analyzer = RecordAnalyzer(mock_dependencies["record_repo"])

        result = mock_analyzer.calculate_streak(mock_habit)

        assert result == sample_records[1]["streak"]

    def test_calculate_longest_streak(self, mock_habit, mock_dependencies, sample_records):
        mock_dependencies["record_repo"].find_by_habit_id.return_value = sample_records[0]
        mock_analyzer = RecordAnalyzer(mock_dependencies["record_repo"])

        result = mock_analyzer.calculate_longest_streak(mock_habit)

        assert result == sample_records[1]["longest"]

    def test_calculate_completion_rate(self, mock_habit, mock_dependencies, sample_records):
        mock_dependencies["record_repo"].find_by_habit_id.return_value = sample_records[0]
        mock_analyzer = RecordAnalyzer(mock_dependencies["record_repo"])

        result = mock_analyzer.calculate_completion_rate(mock_habit)

        assert result == pytest.approx(sample_records[1]["rate"], rel=0.01)

    def test_calculate_finished_on_time(self, mock_habit, mock_dependencies, sample_records):
        mock_dependencies["record_repo"].find_by_habit_id.return_value = sample_records[0]
        mock_analyzer = RecordAnalyzer(mock_dependencies["record_repo"])

        result = mock_analyzer.calculate_finished_ontime_rate(mock_habit)

        assert result == pytest.approx(sample_records[1]["on_time"], rel=0.01)
