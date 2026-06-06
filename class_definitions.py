# Import ABC to provide an abstract interface for the repository interfaces
from abc import ABC, abstractmethod

# Import sqlite3 for database connection
import sqlite3

# Import typing to handle different type inputs in abstract class
from typing import Any

# Import enum for the enumeration classes
from enum import Enum

# Import datetime to handle time related data
from datetime import datetime, timedelta
# Import helper to handle conversion string to datetime and vice versa
import utils_datetime_helper as dt

# Import exceptions and logging for activity screening and debugging
from exceptions import *
# Import Logging for Bug Fixing
import logging
logging.basicConfig(level=logging.INFO, filename="habit-tracker.log", filemode="w", format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Set global database
from pathlib import Path
global_db_path = "habit-tracker-data-9.db"

#========== ENUMERATION CLASSES ==========

class Period(Enum):
    """Enumeration for the periodicity of the habits (in days)

    Values:
        DAILY (1: int)
        WEEKLY (7: int)
        BIWEEKLY (14: int)
        MONTHLY (30: int)

    Notes:
        The values represent the days between two tasks.
        MONTHLY is approximated to 30 days for consistent calculations"""

    DAILY = 1
    WEEKLY = 7
    BIWEEKLY = 14
    MONTHLY = 30

class Status(Enum):
    """Enumeration for the status of the habit

    Values:
        ACTIVE ("Active": str): The habit is active. Tasks to tick off to complete the habit are generated
        PAUSED ("Paused": str): The habit is paused. No Tasks to tick off will be generated until the habit is reactivated
        """

    ACTIVE = 'Active'
    PAUSED = 'Paused'

class CompletionStatus(Enum):
    """Enumeration of all valid statuses for the completion of tasks and therefore the completion records

    Values:
        PENDING ("Pending": str): task is open for completion/tick off
        COMPLETED ("Completed": str): task has been marked as completed. Record entry will hold the information "Completed".
        SKIPPED ("Skipped": str): task has been marked as skipped. Record entry will hold the information "Skipped".
        """

    PENDING = 'Pending'
    COMPLETED = 'Completed'
    SKIPPED = 'Skipped'

#========== MAIN CLASSES ==========

class Habit:
    """
    Object that represents the actual habit and manges the business logic.

    This is the only class object that can be instantiated by the user.
    It can be considered to be the actual API.
    This class encapsulates the habit data and delegates complex methods to the TaskManager
    and the Repositories.

    Args:
        habit_name (str): user-specific of the habit,
        period (Period): chosen period by the user
        start_date (datetime): optional chosen start date (default: datetime.today())

    Note:
        The user has no further influence on how tasks and records are stored.
        TaskManager and the repository interfaces take care about these methods in the background.
    """

    def __init__(self, habit_name: str, period: Period, start_date: datetime = datetime.today()):
        """Initiates the Habit object and creates connection to the TaskManager, as well as the repository interfaces
        With initiation of a habit a corresponding Task is directly instantiated by the corresponding TaskManager."""

        ## ATTRIBUTE ASSIGNMENT

        # User input variables
        self._habit_name = habit_name
        self._period = period
        self._start_date = start_date #datetime format

        # Automatic variables
        self._status: Status = Status.ACTIVE

        # Initialize calculated values
        self._habit_id = None
        self._streak = None

        ## REPOSITORY CONNECTIONS

        # Connect to habit repository interface
        self.__habit_repo = HabitRepository()
        self.__task_repo = TaskRepository(self)
        self.__record_repo = CompletionRecordRepository(self)

        # Create habit entry
        self._habit_id = self.__habit_repo.get_largest_id() + 1
        self.__habit_repo.create(self)

        ## TASK MANAGER (for further task related methods)

        # Initiate Task Manager
        self.__task_manager = TaskManager(self.__task_repo, self.__record_repo)
        # Create first task entry
        self.__task_manager.create_first_task(self)

    @property
    def habit_name(self):
        return self._habit_name
    @property
    def habit_id(self):
        return self._habit_id
    @property
    def period(self):
        return self._period
    @property
    def start_date(self):
        return self._start_date
    @property
    def status(self):
        return self._status

    # INTERACTION

    def complete(self):
        """Call for the completion of the corresponding task
        -> calls TaskManager for complex business logics

        Returns:
            None
        """
        self.__task_manager.complete_current_task(self)

    def skip(self):
        """Call for the skipping of the corresponding task
        -> calls TaskManager for complex business logics

        Returns:
            None
        """
        self.__task_manager.skip_current_task(self)

    # ADMINISTRATION

    def pause(self):
        """Sets habit status to "Paused" (only if it has been "Active" before)
        -> Calls habit repository interface to update the habit table
        -> Calls task manager to remove corresponding task from task table

        Returns:
            None
        """

        #Missing the check whether habit has been active before.
        self._status = Status.PAUSED
        self.__habit_repo.update(self)
        self.__task_manager.delete_current_task(self)

    def reactivate(self):
        """Sets habit status to "Active" (only if it has been "Paused" before)
        -> Calls habit repository interface to update the habit table
        -> Calls task manager to create corresponding task and make entry in task table

        Returns:
            None
        """

        # Missing the check whether habit has been paused before.
        self._status = Status.ACTIVE
        self.__habit_repo.update(self)
        # Create first task entry
        self.__task_manager.create_first_task(self)

    def delete(self):
        """Deletes habit from habit table and all corresponding tasks
        -> Calls habit repository interface to delete the habit from habit table
        -> Calls task manager to delete corresponding task from task table

        Returns:
            None

        Notes:
            Right now it is unclear how to handle the corresponding records.
        """

        self.__habit_repo.delete(self)
        self.__task_manager.delete_current_task(self)

    @habit_name.setter
    def habit_name(self, value: str):
        """With this setter method the user is able to change the habit name.
        When the name is changed, this function ensures that all dependencies (task, task repository, habit repository) are updated accordingly.
        -> Calls habit repository interface to change the name in the habit table
        -> Calls task manager to change the name of the corresponding task
        -> Calls task manager to update the name of the corresponding task in the task table

        Args:
            value (str): New habit name

        Returns:
            None
        """
        self._habit_name = value
        self.__habit_repo.update(self)
        self.__task_manager.update_current_task(self)

    @period.setter
    def period(self, value: Period):
        """With this setter method the user is able to change the habit period.
        When the period is changed, this function ensures that all dependencies (task (incl due_date), task repository, habit repository) are updated accordingly.
        -> Calls habit repository interface to change the period in the habit table
        -> Calls task manager to change the due_date of the corresponding task
        -> Calls task manager to update the due_date of the corresponding task in the table

        Args:
            value (Period): New habit period

        Returns:
            None
        """
        self._period = value
        self.__habit_repo.update(self)
        self.__task_manager.update_current_task(self)

    @start_date.setter
    def start_date(self, value: str):
        """With this setter method the user is able to change the habit start_date.
        When the start_date is changed, this function ensures that all dependencies (task (incl due_date), task repository, habit repository) are updated accordingly.
        -> Calls habit repository interface to change the start_date in the habit table
        -> Calls task manager to change the due_date of the corresponding task
        -> Calls task manager to update the due_date of the corresponding task in the table

        Args:
            value (Period): New habit period

        Returns:
            None
        """

        self._start_date = dt.string_to_dt(value)
        self.__habit_repo.update(self)
        self.__task_manager.update_current_task(self)

class Task:
    """Task is a value class containing only the attributes of the task
    and the business logic to calculate whether a task is overdue or not.
    They are managed by the TaskManager and do not intract with the task repository by themselves
    """

    def __init__(self, habit_id: int, habit_name: str, due_date: datetime, completion_status: CompletionStatus):
        self.habit_name = habit_name
        self.habit_id = habit_id
        self.due_date = due_date
        self.completion_status = completion_status

    @property
    #overdue as a dynamic property, since it is recalculated every day
    def is_overdue(self):
        return self.due_date < datetime.today()

#========== REPOSITORY CLASSES ==========

class RepositoryInterface(ABC):
    @abstractmethod
    def create(self, data: Any):
        pass
    @abstractmethod
    def update(self, data: Any):
        pass
    @abstractmethod
    def delete(self, data: Any):
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
    Object that provides an interface to the database where the habit data is persisted.
    It inherits its basic functionalities from the abstract RepositoryInterface class

    This class is not directly affected by the user and only gets called from the Habit class
    The class takes no arguments in instantiation. However, it is mandatory, that the global_db_path is provided and valid

    Note:
        The Habit Repository class does only interact with the Habit class.
        It has no interface to Task objects, Record objects or other Repository objects
    """

    #Database is the same for all Objects of Class
    __DB_PATH = global_db_path

    def __init__(self):
        """Initiates the HabitRepository object and sets up the basic attributes"""
        self.db_path = self.__DB_PATH
        self.conn: sqlite3.Connection | None = None

    def __ensure_connection(self) -> None:
        """Ensures that the connection to the database is valid"""

        if self.conn is not None:
            # If no open connection available, check whether connection is live
            try:
                test_cursor = self.conn.cursor()
                test_cursor.execute("SELECT 1") #If this does not through an error, the connection is live
                return
            except sqlite3.Error: #If it through an error, the connection must be renewed
                self.conn = None
                self.cursor = None

        # Create new connection
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # Ensure habits scheme
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS habits (
                               habit_name TEXT NOT NULL,
                               habit_id INTEGER NOT NULL,
                               period INTEGER NOT NULL,
                               start_date TEXT NOT NULL,
                               status TEXT NOT NULL)""")
        self.conn.commit()
        logging.debug(f"Database connection established to {self.db_path}")

    def __duplicate_naming(self, habit: Habit) -> int:
        """Checks whether a habit with the same name has already been created"""

        self.__ensure_connection()

        input_name = habit.habit_name

        try:
            self.cursor.execute("SELECT * FROM habits WHERE LOWER(habit_name)=?", (input_name.lower(),))
            duplicates_tuple = self.cursor.fetchall()
            duplicates_list = [duplicate[0] for duplicate in duplicates_tuple]
            return len(duplicates_list)

        except Exception as e:
            msg = f"Error while finding duplicates:  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseFetchDataError(reason=msg, original_error=e)

    def get_largest_id(self) -> int:

        self.__ensure_connection()

        try:
            # Get all IDs as list
            self.cursor.execute("SELECT habit_id FROM habits")
            id_tuple = self.cursor.fetchall()

            # Get maximum value, return 0 if not entry is available
            id_list = [id_entry[0] for id_entry in id_tuple]
            return max(id_list, default=0)

        except Exception as e:
            msg = f"Error while fetching largest ID:  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseFetchDataError(reason=msg, original_error=e)

    def create(self, habit: Habit) -> None :
        """Creates a new habit datapoint in database with all corresponding attributes.
        Before a new habit datapoint is created is checked whether a habit with the same name already exists in the database (case-sensitive)

        Args:
            habit (Habit): New habit for which a datapoint should be created
        """

        self.__ensure_connection()

        data = (habit.habit_name,
                habit.habit_id,
                habit.period.value,
                dt.dt_to_string(habit.start_date), #converted datetime
                habit.status.value)

        if self.__duplicate_naming(habit) == 0:
            try:
                self.cursor.execute("INSERT INTO habits VALUES (?, ?, ?, ?, ?)", data)
                self.conn.commit()
                logging.debug(f"Habit \"{habit.habit_name}\" (ID:{habit.habit_id}) created successfully\"")

            except Exception as e:
                msg = f"Error while creation Habit \"{habit.habit_name}\" (ID:{habit.habit_id}):  {type(e).__name__} | {e}"
                logging.critical(msg)
                raise DatabaseUpdateError(reason=msg, original_error=e)

        else:
            print("That is a duplicate!") #Problem duplicate Habit objects will be created (with new ID, but no entry) > Confusion

    def update(self, habit: Habit) -> None:
        """Updates an existing habit datapoint in database with reference to the corresponding habit_id
        Before a habit datapoint is updated is checked whether a habit with the same name already exists in the database (case-sensitive)

        Args:
            habit (Habit): Habit with updated information (ID is persistent).
        """

        self.__ensure_connection()

        data = (habit.habit_name,
                habit.period.value,
                dt.dt_to_string(habit.start_date), #converted datetime
                habit.status.value)

        if self.__duplicate_naming(habit) > 1:
            print("That is a duplicate!")

        try:
            print(habit.habit_id)
            self.cursor.execute("UPDATE habits SET habit_name=?, period=?, start_date=?, status=? WHERE habit_id=?", (*data, habit.habit_id))
            self.conn.commit()
            #logging.debug(f"Habit \"{habit.habit_name}\" (ID:{habit.habit_id}) updated successfully\"")

        except Exception as e:
            msg = f"Error while updating Habit \"{habit.habit_name}\" (ID:{habit.habit_id}):  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseUpdateError(reason=msg, original_error=e)

    def delete(self, habit: Habit) -> None:
        """Deletes an existing datapoint in database with reference to the corresponding habit_id

        Args:
            habit (Habit): Habit that should be deleted from database.
        """

        self.__ensure_connection()

        try:
            self.cursor.execute("DELETE FROM habits WHERE habit_id=?", (habit.habit_id,))
            self.conn.commit()
            logging.debug(f"Habit \"{habit.habit_name}\" (ID:{habit.habit_id}) deleted successfully\"")

        except Exception as e:
            msg = f"Error while deleting Habit \"{habit.habit_name}\" (ID:{habit.habit_id}):  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseUpdateError(reason=msg, original_error=e)

    @classmethod
    def __cls_connect(cls):
        """This private method tries to set up a connection with the database in accordance to the provided global_db_path"""

        try:
            logging.info(f"CLASS: Connecting to database {cls.__DB_PATH}")

            # --- STEP 1 ---
            # Check whether folder exists
            db_folder = Path(cls.__DB_PATH).parent
            db_folder.mkdir(parents=True, exist_ok=True)

            # --- STEP 2 ---
            # Connect to database
            conn = sqlite3.connect(cls.__DB_PATH)
            cursor = conn.cursor()

            logging.debug(f"CLASS: Database connected successfully")
            return conn, cursor

        except sqlite3.Error as sql_error:
            logging.error(f"CLASS: Database connection failed due to SQLite Error: {sql_error}")
            raise DatabaseConnectionError(reason="CLASS: SQLite Error - Failed to connect to database",
                                          original_error=sql_error)

        except Exception as unspecific_error:
            logging.error(f"CLASS: Database connection failed due to Unexpected Error: {unspecific_error}")
            raise DatabaseConnectionError(reason="CLASS: Unexpected Error - Failed to connect to database",
                                          original_error=unspecific_error)

    @classmethod
    def find_by_habit_id(cls, input_id: int):
        """Searches for the given ID within the database
        Args: input_id (int): The ID to be searched for
        Return:
            dict: A dictionary containing the habit data (habit_name, habit_id, period, start_date, status), if found.
            None: If no Habit with the given ID exists
        """

        # Start connection
        conn, cursor = cls.__cls_connect()

        try:
            # Search for ID in database
            cursor.execute("SELECT habit_name, habit_id, period, start_date, status FROM habits WHERE habit_id=?", (input_id,))
            # Return search result (only one, since it is assured, that ID is unique)
            habit_datapoint = cursor.fetchone()

            # Bring output into readable form and return
            if habit_datapoint:
                logging.debug(f"CLASS: Found habit with provided ID in database")
                return {"habit_name": habit_datapoint[0],
                        "habit_id": habit_datapoint[1],
                        "period": habit_datapoint[2],
                        "start_date": habit_datapoint[3], #string format
                        "status": habit_datapoint[4]}
            # Return None, if there is no search result
            else:
                logging.debug(f"CLASS: Habit with provided ID not found in database")
                return None

        except sqlite3.Error as sql_error:
            logging.error(f"CLASS: Could not find provided id from database due to SQLite Error: {sql_error}")
            raise DatabaseFetchDataError(reason="CLASS: SQLite Error - Failed to fetch data from database",
                                          original_error=sql_error)

        except Exception as unspecific_error:
            logging.error(f"CLASS: Could not find provided id from database due to Unexpected Error: {unspecific_error}")
            raise DatabaseFetchDataError(reason="CLASS: Unexpected Error - Failed to fetch data from database",
                                          original_error=unspecific_error)


    @classmethod
    def find_by_habit_name(cls, input_name: str):
        """Searches for the given name within the database
        Args: input_name (str): The name to be searched for
        Return:
            List of dict: A list of dictionaries containing the habit data (habit_name, habit_id, period, start_date, status) for all found habits with the given name.
            None: If no Habit with the given name exists
        """

        # Start connection
        conn, cursor = cls.__cls_connect()

        try:
            # Search for name (lowercase) in database
            cursor.execute(
                "SELECT habit_name, habit_id, period, start_date, status FROM habits WHERE LOWER(habit_name)=?",
                (input_name.lower(),))  # AttributeError: 'int' object has no attribute 'lower'
            # Return search result (only one, since it is assured, that ID is unique)
            habit_datapoint = cursor.fetchone()

            # Bring output into readable form and return
            if habit_datapoint:
                logging.debug(f"CLASS: Found habit with provided name in database")
                return {"habit_name": habit_datapoint[0],
                        "habit_id": habit_datapoint[1],
                        "period": habit_datapoint[2],
                        "start_date": habit_datapoint[3],  # string format
                        "status": habit_datapoint[4]}
            # Return None, if there is no search result
            else:
                logging.debug(f"CLASS: Habit with provided name not found in database")
                return None

        except sqlite3.Error as sql_error:
            logging.error(f"CLASS: Could not find provided name from database due to SQLite Error: {sql_error}")
            raise DatabaseFetchDataError(reason="CLASS: SQLite Error - Failed to fetch data from database",
                                         original_error=sql_error)

        except Exception as unspecific_error:
            logging.error(
                f"CLASS: Could not find provided name from database due to Unexpected Error: {unspecific_error}")
            raise DatabaseFetchDataError(reason="CLASS: Unexpected Error - Failed to fetch data from database",
                                         original_error=unspecific_error)

    @classmethod
    def browse_all(cls):
        """Searches for the given name within the database
        Args: None
        Return:
            List of dict: A list of dictionaries containing all the habit data (habit_name, habit_id, period, start_date, status)
            None: If database is empty
        """
        # Start connection
        conn, cursor = cls.__cls_connect()

        try:
            # Get all entries
            cursor.execute("SELECT * FROM habits")

            # Return search results
            habit_datapoints = cursor.fetchall()

            # Bring output into readable form and return
            if habit_datapoints:
                logging.debug(f"CLASS: Loaded all habits from database")
                return [{"habit_name": datapoint[0],
                         "habit_id": datapoint[1],
                         "period": datapoint[2],
                         "start_date": datapoint[3], #string format
                         "status": datapoint[4]}
                        for datapoint in habit_datapoints]
            # Return None, if there is no search result
            else:
                logging.debug(f"CLASS: No habits in database")
                return None

        except sqlite3.Error as sql_error:
            logging.error(f"CLASS: Could not load habits from database due to SQLite Error: {sql_error}")
            raise DatabaseFetchDataError(reason="CLASS: SQLite Error - Failed to fetch data from database",
                                         original_error=sql_error)

        except Exception as unspecific_error:
            logging.error(
                f"CLASS: Could not load habits from database due to Unexpected Error: {unspecific_error}")
            raise DatabaseFetchDataError(reason="CLASS: Unexpected Error - Failed to fetch data from database",
                                         original_error=unspecific_error)

class TaskRepository(RepositoryInterface):
    """
    Object that contains all the management logics of the tasks and provides an interface to the database where the task data is persisted.
    Tasks records will be deleted, once they are checked off and the next follow-up task will be created
    Args: referenced Habit object, path to SQlite database
    """

    # Database is the same for all Objects of Class
    __DB_PATH = global_db_path

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
                dt.dt_to_string(task.due_date), #converted datetime
                task.is_overdue,
                task.completion_status.value)

        self.cursor.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", data)
        self.conn.commit()

    def update(self, task: Task):
        ref_id = task.habit_id

        # Generate data
        data = (task.habit_name,
                dt.dt_to_string(task.due_date), #converted datetime
                task.is_overdue,
                task.completion_status.value)

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
    __DB_PATH = global_db_path

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

    def create(self, data: tuple):

        self.cursor.execute("INSERT INTO completion_records VALUES (?, ?, ?, ?)", data)
        self.conn.commit()

    def update(self, data=None):
        pass # Is not implemented yet, might make sense later on

    def delete(self, data=None):
        pass # Is not implemented yet, might make sense later on
        #ref_id = self.reference.habit_id
        #self.cursor.execute("DELETE FROM completion_records WHERE habit_id=?", (ref_id,))
        #self.conn.commit()

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

#========== MANAGER CLASSES ==========

class TaskManager:

    def __init__(self, task_repo: TaskRepository, record_repo: CompletionRecordRepository):
        """Initiates the TaskManager object and creates connection to the repository interfaces of tasks and completion records.
        """

        self.__task_repo = task_repo
        self.__record_repo = record_repo

    def __create_new_task(self, habit: Habit):
        """Handles the deletion of an old task creation of a new one with updated due_date
        -> Calls the Task repository to get the old task by ID of the corresponding habit
        -> Calculates next due_date with the last due_date and the periodicity from the habit
        -> Calls the Task repository to delete the old task datapoint by ID
        -> Calls the Task repository to create a new task datapoint for the habit with the new due_date

        Args:
            habit(Habit): Habit for which the task should be deleted and created

        Returns:
            Task: Task with new due_date
        """

        # Get relevant information on referenced task from repository
        ref_task = self.__task_repo.find_by_habit_id(habit.habit_id)
        next_due_date = dt.string_to_dt(ref_task[0]["due_date"]) + timedelta(days=habit.period.value)

        # Create new task, delete old task
        self.__task_repo.delete(habit.habit_id)

        next_task = Task(habit_id=habit.habit_id,
                         habit_name=habit.habit_name,
                         due_date=next_due_date,
                         completion_status=CompletionStatus.PENDING)

        self.__task_repo.create(next_task)

        return next_task

    def create_first_task(self, habit: Habit):
        """Creates a new task for the given habit or instantiates an existing task from table.
        -> Calls task repository interface to check whether corresponding task in database exists
            if no: due_date is calculated (start_date + period) and new Task object is created
            if yes, task object is instantiated from the task table

        Args:
            habit (Habit): Habit object for which a Task object should be created

        Returns:
            Task: The created Task object will be returned
        """

        ref_task = self.__task_repo.find_by_habit_id(habit.habit_id)

        if not ref_task:
            # Calculate the due_date and make a new entry
            due_date = habit.start_date #datetime format

            initial_task = Task(habit_id=habit.habit_id,
                                habit_name=habit.habit_name,
                                due_date=due_date,
                                completion_status=CompletionStatus.PENDING)

            self.__task_repo.create(initial_task)
            return initial_task

        else:
            existing_task = ref_task[0]

            # Instantiate object from task table
            loaded_task = Task(habit_id=existing_task["habit_id"],
                                habit_name=existing_task["habit_name"],
                                due_date=dt.string_to_dt(existing_task["due_date"]), #conversion back to datetime format
                                completion_status=CompletionStatus.PENDING)

            return loaded_task

    def complete_current_task(self, habit: Habit):
        """Processes the completion of tasks by
        - Calling the CompletionRecord repository to add a completion record to the records table
        - Calculating the due_date of the next task and create a corresponding task object
        - Calling the Task repository to remove the completed task entry and create a new one with the new due date

        Args:
            habit (Habit): Habit object for which the task should be completed

        Returns:
              Task: The newly created Task object will be returned
        """

        # Make entry in records table
        completion_data = (habit.habit_name,
                           habit.habit_id,
                           dt.dt_to_string(datetime.today()),
                           CompletionStatus.COMPLETED.value)
        self.__record_repo.create(completion_data)

        # Create new task, delete old task
        new_task = self.__create_new_task(habit)

        return new_task

    def skip_current_task(self, habit: Habit):
        """Processes the skipping of tasks by
        - Calling the CompletionRecord repository to add a skipping record to the records table
        - Calculating the due_date of the next task and create a corresponding task object
        - Calling the Task repository to remove the completed task entry and create a new one with the new due date

        Args:
            habit (Habit): Habit object for which the task should be skipped

        Returns:
              Task: The newly created Task object will be returned
        """

        # Make entry in records table
        completion_data = (habit.habit_name,
                           habit.habit_id,
                           dt.dt_to_string(datetime.today()),
                           CompletionStatus.SKIPPED.value)
        self.__record_repo.create(completion_data)

        # Create new task, delete old task
        new_task = self.__create_new_task(habit)

        return new_task

    def delete_current_task(self, habit: Habit):
        """Processes the deletion of tasks by ID
        -> Calls Task repository to remove the task from table by ID

        Args:
            habit (Habit): Habit object for which the task should be deleted
        """
        self.__task_repo.delete(habit.habit_id)

    def update_current_task(self, habit: Habit):
        """Processes the update of a task, according to changes in the habit
        - Call the task repository to get the corresponding task entry
        - Re-calculate due_date under consideration of start_date and periodicity of habit
        - Call the task repository to change the task entry attributes according to changes in the habit

        Args:
            habit (Habit): Habit object for which the task should be updated

        Returns:
              Task: The newly created Task object will be returned

        Notes:
            The calculation for the new due_date will be executed also if start_date and periodicity has not changed.
            If there is no change the result will be new_due_date == old_due_date
        """
        ref_task = self.__task_repo.find_by_habit_id(habit.habit_id)

        old_due_date = dt.string_to_dt(ref_task[0]["due_date"]) #conversion from string to datetime format
        new_due_date = habit.start_date + timedelta(days=habit.period.value)
        while new_due_date <= old_due_date:
            new_due_date += timedelta(days=habit.period.value)

        updated_task = Task(habit_id=habit.habit_id,
                         habit_name=habit.habit_name,
                         due_date=new_due_date,
                         completion_status=CompletionStatus.PENDING)

        self.__task_repo.update(updated_task)
        return updated_task