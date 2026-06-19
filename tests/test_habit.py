from source.habit import Habit
from source.enums import Period, Status
from datetime import datetime
from source.utils_datetime_helper import dt_to_string

def test_habit_creation():
    habit = Habit("Test Habit 7", Period.DAILY)

    assert habit.habit_name == "Test Habit 7"
    assert habit.period.value == Period.DAILY.value
    assert habit.status.value == Status.ACTIVE.value
    assert habit.habit_id is not None
    assert dt_to_string(habit.start_date) == dt_to_string(datetime.today())
