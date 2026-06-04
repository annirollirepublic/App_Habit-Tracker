#import ABC to provide an abstract interface for the repository interfaces
from abc import ABC, abstractmethod
#import sqlite3 for database connection
import sqlite3
from typing import Any

#import main classes
from class_definitions import *

#========== REPOSITORY CLASSES ==========

class RepositoryInterface(ABC):
    @abstractmethod
    def create(self, data = Any):
        pass
    @abstractmethod
    def update(self):
        pass
    @abstractmethod
    def delete(self, data = Any):
        pass

    @classmethod
    @abstractmethod
    def find_by_habit_id(cls, value:int):
        pass
    @classmethod
    @abstractmethod
    def find_by_habit_name(cls, value:str):
        pass
    @classmethod
    @abstractmethod
    def browse_all(cls):
        pass

class HabitRepository(RepositoryInterface):
    """
    Object that contains all the management logics of the habits and provides an interface to the database where the habit data is persisted.
    Args: referenced Habit object, path to SQlite database
    """

    #Database is the same for all Objects of Class
    __DB_PATH = "habit-tracker-data-6.db"

    def __init__(self, habit_reference: Habit):
        self.habit_reference = habit_reference
        self.db_path = self.__DB_PATH

        #Connect to database or create if not existent
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute(""" CREATE TABLE IF NOT EXISTS habits (
                                    habit_name TEXT NOT NULL,
                                    habit_id INTEGER NOT NULL,
                                    period INTEGER NOT NULL,
                                    start_date TEXT NOT NULL,
                                    status TEXT NOT NULL)
                                """)
        self.conn.commit()

    def create(self, data=None):
        """Creates a new habit datapoint in database with all corresponding attributes"""

        data = (self.habit_reference.habit_name,
                self.habit_reference.habit_id,
                self.habit_reference.period.value,
                self.habit_reference.start_date,
                self.habit_reference.status.value)

        self.cursor.execute("INSERT INTO habits VALUES (?, ?, ?, ?, ?)", data)
        self.conn.commit()

    def update(self):
        """Updates an existing habit datapoint in database with reference to the corresponding habit_id"""
        ref_id = self.habit_reference.habit_id

        logging.info("objecttype id: %s, value: %s", type(ref_id), str(ref_id))

        data = (self.habit_reference.habit_name,
                self.habit_reference.period.value,
                self.habit_reference.start_date,
                self.habit_reference.status.value)

        self.cursor.execute("UPDATE habits SET habit_name=?, period=?, start_date=?, status=? WHERE habit_id=?", data+(ref_id,))
        self.conn.commit()

    def delete(self, data=None):
        ref_id = self.habit_reference.habit_id

        self.cursor.execute("DELETE FROM habits WHERE habit_id=?", (ref_id,))
        self.conn.commit()

    def get_largest_id(self):
        """Derive the largest id from the database"""
        # Get all IDs as list
        self.cursor.execute("SELECT habit_id FROM habits")
        id_tuple = self.cursor.fetchall()
        self.conn.commit()

        # Get maximum value, return 0 if not entry is available
        id_list = [id_entry[0] for id_entry in id_tuple]
        return max(id_list, default=0)

    def check_for_duplicates(self):
        """Checks whether a habit with the same name has already been created"""
        input_name = self.habit_reference.habit_name

        # Check for same name in database as input name, case-sensitive
        self.cursor.execute("SELECT * FROM habits WHERE LOWER(habit_name)=?", (input_name.lower(),))
        duplicates_tuple = self.cursor.fetchall()
        self.conn.commit()

        duplicates_list = [duplicate[0] for duplicate in duplicates_tuple]
        return duplicates_list

    @classmethod
    def find_by_habit_id(cls, input_id: int):
        """Searches for the given ID within the database
        Args: input_id (int): The ID to be searched for
        Return:
            dict: A dictionary containing the habit data (habit_name, habit_id, period, start_date, status), if found.
            None: If no Habit with the given ID exists
        """

        # Start connection
        conn = sqlite3.connect(cls.__DB_PATH)
        cursor = conn.cursor()

        # Search for ID in database
        cursor.execute("SELECT habit_name, habit_id, period, start_date, status FROM habits WHERE habit_id=?", (input_id,))

        # Return search result (only one, since it is assured, that ID is unique)
        habit_datapoint = cursor.fetchone()
        conn.commit()

        # Bring output into readable form and return
        if habit_datapoint:
            return {"habit_name": habit_datapoint[0],
                    "habit_id": habit_datapoint[1],
                    "period": habit_datapoint[2],
                    "start_date": habit_datapoint[3],
                    "status": habit_datapoint[4]}
        # Return None, if there is no search result
        else:
            return None

    @classmethod
    def find_by_habit_name(cls, input_name: str):
        """Searches for the given name within the database
        Args: input_name (str): The name to be searched for
        Return:
            List of dict: A list of dictionaries containing the habit data (habit_name, habit_id, period, start_date, status) for all found habits with the given name.
            None: If no Habit with the given name exists
        """
        # Start connection
        conn = sqlite3.connect(cls.__DB_PATH)
        cursor = conn.cursor()

        # Search for name (lowercase) in database
        cursor.execute("SELECT habit_name, habit_id, period, start_date, status FROM habits WHERE LOWER(habit_name)=?", (input_name.lower(),)) #AttributeError: 'int' object has no attribute 'lower'

        # Return search results (more than one, since double naming is possible)
        habit_datapoints = cursor.fetchall()
        conn.commit()

        # Bring output into readable form and return
        if habit_datapoints:
            return [{"habit_name": datapoint[0],
                    "habit_id": datapoint[1],
                    "period": datapoint[2],
                    "start_date": datapoint[3],
                    "status": datapoint[4]}
                    for datapoint in habit_datapoints]
        # Return None, if there is no search result
        else:
            return None

    @classmethod
    def browse_all(cls):
        """Searches for the given name within the database
        Args: None
        Return:
            List of dict: A list of dictionaries containing all the habit data (habit_name, habit_id, period, start_date, status)
            None: If database is empty
        """
        # Start connection
        conn = sqlite3.connect(cls.__DB_PATH)
        cursor = conn.cursor()

        # Get all entries
        cursor.execute("SELECT * FROM habits")

        # Return search results
        habit_datapoints = cursor.fetchall()
        conn.commit()

        # Bring output into readable form and return
        if habit_datapoints:
            return [{"habit_name": datapoint[0],
                     "habit_id": datapoint[1],
                     "period": datapoint[2],
                     "start_date": datapoint[3],
                     "status": datapoint[4]}
                    for datapoint in habit_datapoints]
        # Return None, if there is no search result
        else:
            return None

class TaskRepository(RepositoryInterface):
    """
    Object that contains all the management logics of the tasks and provides an interface to the database where the task data is persisted.
    Tasks records will be deleted, once they are checked off and the next follow-up task will be created
    Args: referenced Habit object, path to SQlite database
    """

    # Database is the same for all Objects of Class
    __DB_PATH = "habit-tracker-data-6.db"

    def __init__(self, habit_reference: Habit):
        self.habit_reference = habit_reference
        self.db_path = self.__DB_PATH

        #Connect to database or create if not existent
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS tasks (
                                    habit_name TEXT NOT NULL,
                                    habit_id INTEGER NOT NULL,
                                    due_date TEXT NOT NULL,
                                    is_overdue BOOLEAN NOT NULL,
                                    completion_status TEXT NOT NULL)
                                """)
        self.conn.commit()

    def create(self, task: Task):
        #Generate data
        data = (task.habit_name,
                task.habit_id,
                task.due_date,
                task.is_overdue,
                task.completion_status)

        self.cursor.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", data)
        self.conn.commit()

    def update(self):
        ref_id = self.habit_reference.habit_id

        # Calculate potentially new due date and overdue data
        due_date = self.habit_reference.start_date + timedelta(days=self.habit_reference.period.value)
        is_overdue = due_date < datetime.today()

        # Generate data
        data = (self.habit_reference.habit_name,
                self.habit_reference.habit_id,
                due_date,
                is_overdue,
                CompletionStatus.PENDING.value)

        # Update database
        self.cursor.execute("UPDATE tasks SET habit_name=?, due_date=?, is_overdue=?, completion_status=? WHERE habit_id=?", data + (ref_id,))
        self.conn.commit()

    def delete(self, ref_id: int):

        self.cursor.execute("DELETE FROM tasks WHERE habit_id=?", (ref_id,))
        self.conn.commit()

    @classmethod
    def find_by_habit_id(cls, input_id:int) -> list[dict[str, Any]] | None:
        """Searches for the given ID within the database
        Args: input_id (int): The ID to be searched for
        Return:
            List of dict: A list of dictionaries containing the task data (habit_name, habit_id, due_date, is_overdue, completion_status) for all found tasks with the given ID.
            None: If no Habit with the given name exists"""
        # Start connection
        conn = sqlite3.connect(cls.__DB_PATH)
        cursor = conn.cursor()

        # Search for name (lowercase) in database
        cursor.execute("SELECT habit_name, habit_id, due_date, is_overdue, completion_status FROM tasks WHERE habit_id=?",
                       (input_id,))

        # Return search results (more than one, since double naming is possible)
        habit_datapoints = cursor.fetchall()
        conn.commit()

        # Bring output into readable form and return
        if habit_datapoints:
            return [{"habit_name": datapoint[0],
                     "habit_id": datapoint[1],
                     "due_date": datapoint[2],
                     "is_overdue": datapoint[3],
                     "completions_status": datapoint[4]}
                    for datapoint in habit_datapoints]
        # Return None, if there is no search result
        else:
            return None

    @classmethod
    def find_by_habit_name(cls, value:str):
        pass

    @classmethod
    def browse_all(cls):
        pass

class CompletionRecordRepository(RepositoryInterface):
    """
    Object that is generated, when triggered by the task completion as described above.
    They do contain a reference to the corresponding habit, as well as the completion date and status.
    They represent the actual historical data and cannot be changed by the user directly.
    """

    # Database is the same for all Objects of Class
    __DB_PATH = "habit-tracker-data-6.db"

    def __init__(self, reference: object):
        self.reference = reference # Can be referenced either by Task or by Habit
        self.db_path = self.__DB_PATH

        # Connect to database or create if not existent
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute(""" CREATE TABLE IF NOT EXISTS completion_records (
                                habit_name TEXT NOT NULL,
                                habit_id INTEGER NOT NULL,
                                completion_date TEXT NOT NULL,
                                completion_status TEXT NOT NULL)
                            """)
        self.conn.commit()

    def create(self, data=tuple):

        self.cursor.execute("INSERT INTO completion_records VALUES (?, ?, ?, ?)", data)
        self.conn.commit()

    def update(self):
        pass # Is not implemented yet, might make sense later on

    def delete(self):
        ref_id = self.reference.habit_id

        self.cursor.execute("DELETE FROM completion_records WHERE habit_id=?", (ref_id,))
        self.conn.commit()

    @classmethod
    def find_by_habit_id(cls, value:int):
        pass

    @classmethod
    def find_by_habit_name(cls, value:str):
        pass

    @classmethod
    def browse_all(cls):
        pass

    # Additional statistics
    def calculate_streak(self):
        pass