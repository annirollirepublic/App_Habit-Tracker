# Import datetime helper / USER-DEFINED
from source.helpers.utils_datetime_helper import string_to_dt

# Import logging for activity screening and debugging / BUILT-IN
import logging

# Import enumeration classes / USER-DEFINED
from source.helpers.enums import CompletionStatus

# Import repository modules / USER-DEFINED
from source.repository.repository_modules import CompletionRecordRepository

# Set logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

#========== SERVICES CLASSES ==========

class RecordAnalyzer:
    """
    Service class for calculating habit statistics from completion records.

    RecordAnalyzer reads historical completion records from
    CompletionRecordRepository and derives analytics for individual habits.
    These analytics include current streaks, longest streaks, completion rates,
    and on-time completion rates.

    Args:
        record_repo (CompletionRecordRepository): Repository used to retrieve completion history.

    Attributes:
        record_repo (CompletionRecordRepository): Repository containing completion records.

    Notes:
        The analyzer does not modify habit, task, or record data. It only reads
        completion records and returns calculated statistics.
    """

    def __init__(self, record_repo: CompletionRecordRepository):
        # Record Analyzer gets records from repository
        self.record_repo = record_repo

    def calculate_streak(self, habit):
        """Calculates the current streak for a given habit."""

        # Get all records for habit sorted according to their due date
        ref_records = self.record_repo.find_by_habit_id(habit.habit_id)
        ref_records_sorted = sorted(ref_records, key=lambda x: string_to_dt(x['due_date']), reverse=True)

        # Count the number of completed records that are not overdue/skipped
        # Stop counting when a skipped/overdue record is encountered
        streak = 0
        for record in ref_records_sorted:
            if record["completion_status"] == CompletionStatus.COMPLETED.value and record["was_overdue"] == 0:
                streak += 1
            else:
                break

        return streak

    def calculate_longest_streak(self, habit):
        """Calculates the longest streak for a given habit."""

        # Get all records for habit sorted according to their due date
        ref_records = self.record_repo.find_by_habit_id(habit.habit_id)
        ref_records_sorted = sorted(ref_records, key=lambda x: string_to_dt(x['due_date']), reverse=True)

        # Count the number of completed records that are not overdue/skipped
        # Restart streak count when a skipped/overdue record is encountered
        # Append streak before restarting to list
        streak_list = []
        streak = 0
        for record in ref_records_sorted:
            if record["completion_status"] == CompletionStatus.COMPLETED.value and record["was_overdue"] == 0:
                streak += 1
            else:
                streak_list.append(streak)
                streak = 0
        streak_list.append(streak)
        # Possible that one streak is appended double, but this does not affect the correctness of the outcome

        return max(streak_list)

    def calculate_completion_rate(self, habit):
        """Calculates the completion rate for a given habit."""

        # Get all records for a given habit
        ref_records = self.record_repo.find_by_habit_id(habit.habit_id)

        # Calculate ratio of completed records to total records
        total_records = len(ref_records)
        completed_records = sum(1 for record in ref_records if record['completion_status'] == 'Completed')

        if total_records == 0:
            return 0
        return completed_records / total_records

    def calculate_finished_ontime_rate(self, habit):
        """Calculates the on-time completion rate for a given habit."""

        # Get all records for a given habit
        ref_records = self.record_repo.find_by_habit_id(habit.habit_id)

        # Calculate ratio of completed records that were not overdue to total records
        total_records = len(ref_records)
        ontime_records = sum(1 for record in ref_records if record['was_overdue'] == 0 and record['completion_status'] == 'Completed')

        if total_records == 0:
            return 0
        return ontime_records / total_records

    def habit_history(self, habit):
        """Returns a list of all completion records for a given habit."""

        # Get all records for a given habit
        ref_records = self.record_repo.find_by_habit_id(habit.habit_id)

        ref_records = ref_records

        # Bring records into chronological order
        ref_records_sorted = sorted(ref_records, key=lambda x: string_to_dt(x['due_date']), reverse=True)

        # Bring records into human-readable format
        ref_records_formatted = []
        for record in ref_records_sorted:
            ref_records_formatted.append({
                "habit_name": record["habit_name"],
                "completion_date": record["completion_date"],
                "completion_status": record["completion_status"],
                "was_overdue": record["was_overdue"]
            })

        return ref_records_formatted

#------------NOT IMPLEMENTED YET------------

    def calculate_most_consistent_habit(self):
        """Calculates the habit with the highest streak.
        NOT IMPLEMENTED YET"""
        pass

        # Get all unique IDs in records list

        # for each ID in records list, do calculate_longest_streak(habit_id)
        # Compare longest streaks against each other
        # Which ID belongs to overall longest streak?
        # Search habit datapoint according to ID
        # return habit and longest streak for habit

    def habit_with_highest_completion_rate(self):
        """Calculates the habit with the highest completion rate.
        NOT IMPLEMENTED YET"""
        pass