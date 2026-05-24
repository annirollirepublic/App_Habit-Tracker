import datetime

class Habit:
    """
    Object that represents the actual habit. It contains all the crucial information about the habit, that determines the subsequent business logic.
    It is the only class object that can be instantiated by the user.
    Args: habit_name: string, period: Period, start_date: datetime (today by default)
    """

    def __init__(self, habit_name, period, start_date=datetime.now()):
        self._habit_name = habit_name
        self._period = period
        self._start_date = start_date
        self._status = 'Active'
        self.__habit_id = None
        self.__streak = 0

    def create_task(self):
        pass

    def recalculate_task(self, _start_date, _period):
        pass

    def pause(self):
        pass

    def reactivate(self):
        pass

    def rename(self, new_name):
        pass

    def change_periodicity(self, new_period):
        pass

    def change_start_date(self, new_start_date):
        pass

class HabitRepository:
    """
    Object that contains all the management logics of the habits and provides an interface to the database where the habit data is persisted.
    """

class Task:
    """
    Object that represents the actual, tick-off tasks that arise from a corresponding habit and its defined period.
    Tasks are created by the app, given the information from the habit. The user cannot create tasks independently.
    """

class TaskRepository:
    """
    Object that contains all the management logics of the tasks and provides an interface to the database where the task data is persisted.
    Tasks records will be deleted, once they are checked off and the next follow-up task will be created
    """

class CompletionRecord:
    """
    Object that is generated, when triggered by the task completion as described above.
    They do contain a reference to the corresponding habit, as well as the completion date and status.
    They represent the actual historical data and cannot be changed by the user directly.
    """

class CompletionRecordRepository:
    """
    Object that contains all the management logics of the completion records and provides an interface to the database where the task data is persisted.
    All further analysis can be calculated from this class.
    """