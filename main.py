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

    def __create_task(self):
        pass

    def __recalculate_task(self, _start_date, _period):
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

    def create(self, habit):
        pass

    def update(self, habit):
        pass

    def delete(self, habit):
        pass

    def browse_all(self):
        pass

    def find_habit_by_name(self, habit_name):
        pass

    def find_habit_by_id(self, habit_id):
        pass


class Task:
    """
    Object that represents the actual, tick-off tasks that arise from a corresponding habit and its defined period.
    Tasks are created by the app, given the information from the habit. The user cannot create tasks independently.
    """

    def __init__(self, habit_name, habit_id):
        self.__habit_name = habit_name
        self.__habit_id = habit_id
        self.__due_date = None
        self._check_out = False
        self._completion_status = 'Pending'

    def complete(self, date):
        pass

    def skip(self, date):
        pass

    def __publish_to_record(self, _completion_status, date):
        pass

    def __is_overdue(self, __due_date, date):
        pass


class TaskRepository:
    """
    Object that contains all the management logics of the tasks and provides an interface to the database where the task data is persisted.
    Tasks records will be deleted, once they are checked off and the next follow-up task will be created
    """

    def __create(self, task):
        pass

    def __update(self, task):
        pass

    def __delete(self, task):
        pass

    def find_task_by_habit_name(self, habit_name):
        pass

    def find_task_by_habit_id(self, habit_id):
        pass

class CompletionRecord:
    """
    Object that is generated, when triggered by the task completion as described above.
    They do contain a reference to the corresponding habit, as well as the completion date and status.
    They represent the actual historical data and cannot be changed by the user directly.
    """

    def __init__(self, habit_name, habit_id, completion_date, completion_status):
        self.__habit_name = habit_name
        self.__habit_id = habit_id
        self.__completion_date = completion_date
        self.__completion_status = 'Completed'

class CompletionRecordRepository:
    """
    Object that contains all the management logics of the completion records and provides an interface to the database where the task data is persisted.
    All further analysis can be calculated from this class.
    """

    def __add_record(self, completion_record):
        pass

    def find_records_by_habit_name(self, habit_name):
        pass

    def find_records_by_habit_id(self, habit_id):
        pass

    def calculate_streak(self):
        pass
