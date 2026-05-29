from datetime import datetime
#import traceback and logging for activity screening and debugging
import traceback
import logging
logging.basicConfig(level=logging.INFO, filename="habit-tracker.log", filemode="w", format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#import enum for the enumeration classes
from enum import Enum
#import ABC to provide an abstract interface for the repository interfaces
from abc import ABC, abstractmethod
#import sqlite3 for database connection
import sqlite3

#========== ENUMERATION CLASSES ==========

class Period(Enum):
    """Enumeration class, that contains all valid periods for the habits"""
    DAILY = "Daily"
    WEEKLY = "Weekly"
    BIWEEKLY = "Biweekly"
    MONTHLY = "Monthly"

class Status(Enum):
    """Enumeration class, that contains all valid statuses for the habits"""
    ACTIVE = 'Active'
    PAUSED = 'Paused'

class CompletionStatus(Enum):
    """Enumeration class, that contains all valid statuses for the completion of tasks and therefore also the completion records"""
    PENDING = 'Pending'
    COMPLETED = 'Completed'
    SKIPPED = 'Skipped'

#========== MAIN CLASSES ==========

class Habit:
    """
    Object that represents the actual habit. It contains all the crucial information about the habit, that determines the subsequent business logic.
    It is the only class object that can be instantiated by the user.
    Args: habit_name: string, period: Period, start_date: datetime (today by default)
    """

    #Class variable to continuously increase habit_id
    _next_id = 1

    def __init__(self, habit_name: str, period: Period, start_date: datetime = datetime.now()):

        #User input variables
        self._habit_name = habit_name
        self._period = period
        self._start_date = start_date

        #Automatic variables
        self._status: Status = Status.ACTIVE

        #Calculated variables
        self.__habit_id = Habit._next_id
        Habit._next_id += 1

        #Log entry
        logging.info("New Habit Instantiated: %s, %s, %s, %s", self._habit_name, self._period, self._start_date, self._status)

        #repository interfaces
        self.__habit_repo_interface: HabitRepository = HabitRepository(self)
        # Create datapoint habit in database, sheet 'habits'
        self.__habit_repo_interface.create()
        logging.info("Habit is connected to habits table")

        self.__task_repo_interface: TaskRepository = TaskRepository(self)
        # Create datapoint for corresponding task in database, sheet 'tasks'
        self.__task_repo_interface.create()
        logging.info("Habit is connected to task table")
        #self.__record_repo_interface: CompletionRecordRepository = CompletionRecordRepository()


        self.__streak = None

    @property
    def habit_name(self):
        return self._habit_name
    @property
    def habit_id(self):
        return self.__habit_id
    @property
    def period(self):
        return self._period
    @property
    def start_date(self):
        return self._start_date
    @property
    def status(self):
        return self._status

    def pause(self):
        self._status = Status.PAUSED
        self.__habit_repo_interface.update()
        self.__task_repo_interface.delete()

    def reactivate(self):
        self._status = Status.ACTIVE
        self.__habit_repo_interface.update()
        self.__task_repo_interface.create()

    @habit_name.setter
    def habit_name(self, value: str):
        self._habit_name = value
        self.__habit_repo_interface.update()
        self.__task_repo_interface.update()

    @period.setter
    def period(self, value: Period):
        self._period = value
        self.__habit_repo_interface.update()
        self.__task_repo_interface.update()

    @start_date.setter
    def start_date(self, value: datetime):
        self._start_date = value
        self.__habit_repo_interface.update()
        self.__task_repo_interface.update()

#========== REPOSITORY CLASSES ==========

class RepositoryInterface(ABC):
    @abstractmethod
    def create(self):
        pass
    @abstractmethod
    def update(self):
        pass
    @abstractmethod
    def delete(self):
        pass
    @abstractmethod
    def find_by_habit_id(self):
        pass
    @abstractmethod
    def find_by_habit_name(self):
        pass
    @abstractmethod
    def browse_all(self):
        pass

class HabitRepository(RepositoryInterface):
    """
    Object that contains all the management logics of the habits and provides an interface to the database where the habit data is persisted.
    Args: referenced Habit object, path to SQlite database
    """
    def __init__(self, habit_reference: Habit, db_path: str = "habit-tracker-data-2.db"):
        self.habit_reference = habit_reference
        self.db_path = db_path

        #Connect to database or create if not existent
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute(""" CREATE TABLE IF NOT EXISTS habits (
                                    habit_name TEXT NOT NULL,
                                    habit_id INTEGER NOT NULL,
                                    period TEXT NOT NULL,
                                    start_date TEXT NOT NULL,
                                    status TEXT NOT NULL)
                                """)
        self.conn.commit()

    def create(self):

        data = (self.habit_reference.habit_name,
                self.habit_reference.habit_id,
                self.habit_reference.period.value,
                self.habit_reference.start_date,
                self.habit_reference.status.value)

        self.cursor.execute("INSERT INTO habits VALUES (?, ?, ?, ?, ?)", data)
        self.conn.commit()

    def update(self):
        ref_id = self.habit_reference.habit_id

        logging.info("objecttype id: %s, value: %s", type(ref_id), str(ref_id))

        data = (self.habit_reference.habit_name,
                self.habit_reference.period.value,
                self.habit_reference.start_date,
                self.habit_reference.status.value)

        print(self.cursor.fetchall())

        self.cursor.execute("UPDATE habits SET habit_name=?, period=?, start_date=?, status=? WHERE habit_id=?", data+(ref_id,))
        self.conn.commit()

    def delete(self):
        ref_id = self.habit_reference.habit_id

        self.cursor.execute("DELETE FROM habits WHERE habit_id = ?", (ref_id,))
        self.conn.commit()

    def find_by_habit_id(self):
        pass

    def find_by_habit_name(self):
        pass

    def browse_all(self):
        pass


class TaskRepository(RepositoryInterface):
    """
    Object that contains all the management logics of the tasks and provides an interface to the database where the task data is persisted.
    Tasks records will be deleted, once they are checked off and the next follow-up task will be created
    Args: referenced Habit object, path to SQlite database
    """

    def __init__(self, habit_reference: Habit, db_path: str = "habit-tracker-data-2.db"):
        self.habit_reference = habit_reference
        self.db_path = db_path

        #Connect to database or create if not existent
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute(""" CREATE TABLE IF NOT EXISTS tasks (
                                    habit_name TEXT NOT NULL,
                                    period TEXT NOT NULL,
                                    start_date TEXT NOT NULL,
                                    status TEXT NOT NULL)
                                """)
        self.conn.commit()

    def create(self):
        pass

    def update(self):
        pass

    def delete(self):
        pass

    def find_by_habit_id(self):
        pass

    def find_by_habit_name(self):
        pass

    def browse_all(self):
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
