import class_definitions as cd
from class_definitions import HabitRepository

#my_first_habit = cd.Habit("Make Laundry 20", cd.Period.DAILY)

#my_first_habit.habit_name = "Handle Laundry 20"

#my_first_habit.delete()

#my_second_habit = cd.Habit("Go for a Run 3", cd.Period.WEEKLY)

#my_second_habit.period = cd.Period.MONTHLY

my_third_habit = cd.Habit("Clean Windows 2", cd.Period.MONTHLY)

my_third_habit.start_date = "2026-08-15"

my_third_habit.skip()

#my_second_habit.delete()