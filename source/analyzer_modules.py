# Import datetime helper / USER-DEFINED
from source.utils_datetime_helper import string_to_dt

# Import enumeration classes / USER-DEFINED
from source.enums import CompletionStatus

# Import repository modules / USER-DEFINED
from source.repository_modules import CompletionRecordRepository


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
        self.record_repo = record_repo

    def calculate_streak(self, habit):

        ref_records = self.record_repo.find_by_habit_id(habit.habit_id)

        ref_records_sorted = sorted(ref_records, key=lambda x: string_to_dt(x['due_date']), reverse=True)

        streak = 0
        for record in ref_records_sorted:
            if record["completion_status"] == CompletionStatus.COMPLETED.value and record["was_overdue"] == 0:
                streak += 1
            else:
                break

        return streak

    def calculate_longest_streak(self, habit):

        ref_records = self.record_repo.find_by_habit_id(habit.habit_id)

        ref_records_sorted = sorted(ref_records, key=lambda x: string_to_dt(x['due_date']), reverse=True)

        streak_list = []
        streak = 0
        for record in ref_records_sorted:
            if record["completion_status"] == CompletionStatus.COMPLETED.value and record["was_overdue"] == 0:
                streak += 1
            else:
                streak_list.append(streak)
                streak = 0
        streak_list.append(streak) # Possible that one streak is appended double, but this does not affect the correctness of the outcome

        return max(streak_list)

    def calculate_completion_rate(self, habit):

        ref_records = self.record_repo.find_by_habit_id(habit.habit_id)

        total_records = len(ref_records)
        completed_records = sum(1 for record in ref_records if record['completion_status'] == 'Completed')

        if total_records == 0:
            return 0
        return completed_records / total_records

    def calculate_finished_ontime_rate(self, habit):

        ref_records = self.record_repo.find_by_habit_id(habit.habit_id)
        total_records = len(ref_records)

        ontime_records = sum(1 for record in ref_records if record['was_overdue'] == 0 and record['completion_status'] == 'Completed')

        if total_records == 0:
            return 0
        return ontime_records / total_records

    def calculate_most_consistent_habit(self):
        pass

        # Get all unique IDs in records list

        # for each ID in records list, do calculate_longest_streak(habit_id)
        # Compare longest streaks against each other
        # Which ID belongs to overall longest streak?
        # Search habit datapoint according to ID
        # return habit and longest streak for habit

    def habit_with_highest_completion_rate(self):
        pass