# Import ABC to provide an abstract interface for the repository interfaces / BUILT-IN
from abc import ABC, abstractmethod

# Import sqlite3 for database connection / BUILT-IN
import sqlite3

# Import typing to handle different type inputs in the abstract class / BUILT-IN
from typing import Any

# Import exceptions and logging for activity screening and debugging / BUILT-IN
from source.exceptions import *

# Set logger
import logging
logger = logging.getLogger(__name__)

# Import helper to handle conversion string to datetime and vice versa / USER-DEFINED
from source.utils_datetime_helper import dt_to_string

# Import database path / USER-DEFINED
from source.config import global_db_path

# Import task class / USER-DEFINED
from source.task import Task

# ========== REPOSITORY CLASSES ==========

class RepositoryInterface(ABC):
    """
    Abstract base class for all repository implementations.

    The repository interface defines the common database operations used by
    habit, task, and completion record repositories. It centralizes the
    database path, manages the SQLite connection, and requires subclasses to
    implement CRUD and lookup methods.

    Subclasses are responsible for creating their own database tables and
    converting database rows into the data structures expected by the rest
    of the application.

    Attributes:
        db_path (str): Path to the SQLite database file.
        conn (sqlite3.Connection | None): Active SQLite database connection, if available.
        cursor (sqlite3.Cursor): Cursor used to execute database statements after connection setup.

    Notes:
        This class should not be instantiated directly. Use one of its concrete
        subclasses instead, such as HabitRepository, TaskRepository, or
        CompletionRecordRepository.
    """

    def __init__(self, db_path: str = global_db_path):
        self.db_path = db_path
        self.conn: sqlite3.Connection | None = None

    @abstractmethod
    def _create_scheme(self):
        pass

    @abstractmethod
    def _fetch_data(self):
        pass

    @abstractmethod
    def create(self, data: Any):
        pass

    @abstractmethod
    def update(self, data: Any):
        pass

    @abstractmethod
    def delete(self, data: Any):
        pass

    @abstractmethod
    def find_by_habit_id(self, value: int):
        pass

    @abstractmethod
    def find_by_habit_name(self, value: str):
        pass

    @abstractmethod
    def browse_all(self):
        pass

    def _ensure_connection(self):

        logger.info(f"Checking for open connection")

        if self.conn is not None:
            # If no open connection available, check whether connection is live
            try:
                test_cursor = self.conn.cursor()
                test_cursor.execute("SELECT 1")  # If this does not through an error, the connection is live
                return
            except sqlite3.Error:  # If it through an error, the connection must be renewed
                self.conn = None
                self.cursor = None

        logger.info(f"No open connection available. Creating new connection")

        # Create a new connection
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self._create_scheme()


class HabitRepository(RepositoryInterface):
    """
    Repository for persisting and retrieving current habits.

    The habit repository provides database access for Habit objects. It creates
    and manages the habits table, stores the currently open habit,
    and supports lookup by habit ID or habit name.

    This class is not directly affected by the user and only gets called from the Habit class
    The class takes no arguments in instantiation. However, it is mandatory that
    the global_db_path is provided and valid

    Inherits:
        RepositoryInterface: Provides the shared database connection handling
        and abstract repository method definitions.

    Note:
        The Habit Repository class does only interact with the Habit class.
        It has no interface to Task objects, Record objects, or other Repository objects
    """

    def __init__(self, db_path = None):
        """Initiates the HabitRepository object and sets up the basic attributes"""
        super().__init__(db_path) if db_path is not None else super().__init__()

    def _create_scheme(self) -> None:

        logger.info(f"Setting up scheme for habit table")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS habits
                               (
                                   habit_name TEXT    NOT NULL,
                                   habit_id   INTEGER NOT NULL,
                                   period     INTEGER NOT NULL,
                                   start_date TEXT    NOT NULL,
                                   status     TEXT    NOT NULL
                               )""")
        self.conn.commit()

    def _fetch_data(self):

        logger.info(f"Fetching data from habit table")
        datapoint = self.cursor.fetchall()

        if datapoint and isinstance(datapoint, (tuple, list)):
            result = [{"habit_name": datapoint[i][0],
                       "habit_id": datapoint[i][1],
                       "period": datapoint[i][2],
                       "start_date": datapoint[i][3],  # string format
                       "status": datapoint[i][4]} for i in range(len(datapoint))]
            return result
        else:
            return []

    def duplicate_naming(self, habit) -> int:
        """Checks whether a habit with the same name has already been created"""

        super()._ensure_connection()
        input_name = habit.habit_name

        logger.info(f"Checking for duplicate habit name: {input_name.lower()}")

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

        super()._ensure_connection()

        logger.info(f"Fetching largest ID")

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

    def create(self, habit) -> None:
        """Creates a new habit datapoint in database with all corresponding attributes.
        Before a new habit datapoint is created is checked whether a habit with the same name already exists in the database (case-sensitive)

        Args:
            habit (Habit): New habit for which a datapoint should be created
        """

        super()._ensure_connection()

        data = (habit.habit_name,
                habit.habit_id,
                habit.period.value,
                dt_to_string(habit.start_date),  # converted datetime
                habit.status.value)

        if self.duplicate_naming(habit) == 0:
            try:
                self.cursor.execute("INSERT INTO habits VALUES (?, ?, ?, ?, ?)", data)
                self.conn.commit()
                logging.debug(f"Habit \"{habit.habit_name}\" (ID:{habit.habit_id}) created successfully\"")

            except Exception as e:
                msg = f"Error while creation Habit \"{habit.habit_name}\" (ID:{habit.habit_id}):  {type(e).__name__} | {e}"
                logging.critical(msg)
                raise DatabaseUpdateError(reason=msg, original_error=e)

        else:
            print(
                "That is a duplicate!")  # Problem duplicate Habit objects will be created (with new ID, but no entry) > Confusion

    def update(self, habit) -> None:
        """Updates an existing habit datapoint in database with reference to the corresponding habit_id
        Before a habit datapoint is updated is checked whether a habit with the same name already exists in the database (case-sensitive)

        Args:
            habit (Habit): Habit with updated information (ID is persistent).
        """

        super()._ensure_connection()

        data = (habit.habit_name,
                habit.period.value,
                dt_to_string(habit.start_date),  # converted datetime
                habit.status.value)

        if self.duplicate_naming(habit) > 1:
            print("That is a duplicate!")

        try:
            self.cursor.execute("UPDATE habits SET habit_name=?, period=?, start_date=?, status=? WHERE habit_id=?",
                                (*data, habit.habit_id))
            self.conn.commit()
            logging.debug(f"Habit \"{habit.habit_name}\" (ID:{habit.habit_id}) updated successfully\"")

        except Exception as e:
            msg = f"Error while updating Habit \"{habit.habit_name}\" (ID:{habit.habit_id}):  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseUpdateError(reason=msg, original_error=e)

    def delete(self, habit) -> None:
        """Deletes an existing datapoint in database with reference to the corresponding habit_id

        Args:
            habit (Habit): Habit that should be deleted from database.
        """

        super()._ensure_connection()

        logger.info(f"Deleting habit datapoint")

        try:
            self.cursor.execute("DELETE FROM habits WHERE habit_id=?", (habit.habit_id,))
            self.conn.commit()
            logging.debug(f"Habit \"{habit.habit_name}\" (ID:{habit.habit_id}) deleted successfully\"")

        except Exception as e:
            msg = f"Error while deleting Habit \"{habit.habit_name}\" (ID:{habit.habit_id}):  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseUpdateError(reason=msg, original_error=e)

    def find_by_habit_id(self, input_id: int):
        """Searches for the given ID within the database
        Args: input_id (int): The ID to be searched for
        Return:
            dict: A dictionary containing the habit data (habit_name, habit_id, period, start_date, status), if found.
            None: If no Habit with the given ID exists
        """

        super()._ensure_connection()

        logger.info(f"Searching for habit with ID: {input_id}")

        try:
            # Search for ID in database
            self.cursor.execute("SELECT habit_name, habit_id, period, start_date, status FROM habits WHERE habit_id=?",
                                (input_id,))
            # Return search result (only one, since it is assured, that ID is unique)

            return self._fetch_data()

        except Exception as e:
            msg = f"Error while reading habit table:  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseFetchDataError(reason=msg, original_error=e)

    def find_by_habit_name(self, input_name: str):
        """Searches for the given name within the database
        Args: input_name (str): The name to be searched for
        Return:
            List of dict: A list of dictionaries containing the habit data (habit_name, habit_id, period, start_date, status) for all found habits with the given name.
            None: If no Habit with the given name exists
        """

        super()._ensure_connection()

        logger.info(f"Searching for habit with name: {input_name}")

        try:
            # Search for name (lowercase) in database
            self.cursor.execute(
                "SELECT habit_name, habit_id, period, start_date, status FROM habits WHERE LOWER(habit_name)=?",
                (input_name.lower(),))  # AttributeError: 'int' object has no attribute 'lower'
            # Return search result (only one, since it is assured, that ID is unique)
            return self._fetch_data()

        except Exception as e:
            msg = f"Error while reading habit table:  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseFetchDataError(reason=msg, original_error=e)

    def browse_all(self):
        """Searches for the given name within the database
        Args: None
        Return:
            List of dict: A list of dictionaries containing all the habit data (habit_name, habit_id, period, start_date, status)
            None: If database is empty
        """

        super()._ensure_connection()

        logger.info(f"Browsing all habits")

        try:
            # Get all entries
            self.cursor.execute("SELECT * FROM habits")

            return self._fetch_data()

        except Exception as e:
            msg = f"Error while reading habit table:  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseFetchDataError(reason=msg, original_error=e)


class TaskRepository(RepositoryInterface):
    """
    Repository for persisting and retrieving current habit tasks.

    The task repository provides database access for Task objects. It creates
    and manages the tasks table, stores the currently open task for each habit,
    and supports lookup by habit ID or habit name.

    Task rows are usually temporary: when a task is completed or skipped, the
    old task is removed and a new follow-up task is created by TaskManager.

    Inherits:
        RepositoryInterface: Provides the shared database connection handling
        and abstract repository method definitions.

    Notes:
        This repository should normally be used through TaskManager instead of
        being called directly by user-facing code.
    """

    def __init__(self, db_path=None):
        """Initiates the TaskRepository object and sets up the basic attributes"""
        super().__init__(db_path) if db_path is not None else super().__init__()

    def _create_scheme(self) -> None:

        logger.info(f"Setting up scheme for task table")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS tasks
                               (
                                   habit_name        TEXT    NOT NULL,
                                   habit_id          INTEGER NOT NULL,
                                   due_date          TEXT    NOT NULL,
                                   is_overdue        BOOLEAN NOT NULL,
                                   completion_status TEXT    NOT NULL
                               )""")
        self.conn.commit()  ##

    def _fetch_data(self):

        datapoint = self.cursor.fetchall()

        logger.info(f"Fetching data from task table")

        if datapoint and isinstance(datapoint, (tuple, list)):
            result = [{"habit_name": datapoint[i][0],
                       "habit_id": datapoint[i][1],
                       "due_date": datapoint[i][2],  # string format
                       "is_overdue": datapoint[i][3],
                       "completion_status": datapoint[i][4]} for i in range(len(datapoint))]
            return result
        else:
            return []

    def create(self, task: Task):

        super()._ensure_connection()

        # Generate data
        data = (task.habit_name,
                task.habit_id,
                dt_to_string(task.due_date),  # converted datetime
                task.is_overdue,
                task.completion_status.value)

        try:
            self.cursor.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", data)
            self.conn.commit()
            logging.debug(f"Task \"{task.habit_name}\" (ID:{task.habit_id}) created successfully\"")

        except Exception as e:
            msg = f"Error while task creation for Habit \"{task.habit_name}\" (ID:{task.habit_id}):  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseUpdateError(reason=msg, original_error=e)

    def update(self, task: Task):

        super()._ensure_connection()

        # Generate data
        data = (task.habit_name,
                dt_to_string(task.due_date),  # converted datetime
                task.is_overdue,
                task.completion_status.value)

        try:
            # Update database
            self.cursor.execute(
                "UPDATE tasks SET habit_name=?, due_date=?, is_overdue=?, completion_status=? WHERE habit_id=?",
                (*data, task.habit_id))
            self.conn.commit()
            logging.debug(f"Task \"{task.habit_name}\" (ID:{task.habit_id}) updated successfully\"")

        except Exception as e:
            msg = f"Error while task update for Habit \"{task.habit_name}\" (ID:{task.habit_id}):  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseUpdateError(reason=msg, original_error=e)

    def delete(self, task: Task):

        super()._ensure_connection()

        try:
            self.cursor.execute("DELETE FROM tasks WHERE habit_id=?", (task.habit_id,))
            self.conn.commit()
            logging.debug(f"Task \"{task.habit_name}\" (ID:{task.habit_id}) deleted successfully\"")

        except Exception as e:
            msg = f"Error while task removal for Habit \"{task.habit_name}\" (ID:{task.habit_id}):  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseUpdateError(reason=msg, original_error=e)

    def find_by_habit_id(self, input_id: int):
        """Searches for the given ID within the database
        Args: input_id (int): The ID to be searched for
        Return:
            List of dict: A list of dictionaries containing the task data (habit_name, habit_id, due_date, is_overdue, completion_status) for all found tasks with the given ID.
            None: If no Habit with the given name exists"""

        super()._ensure_connection()

        logger.info(f"Searching for task with ID: {input_id}")

        try:
            # Search for name (lowercase) in database
            self.cursor.execute(
                "SELECT habit_name, habit_id, due_date, is_overdue, completion_status FROM tasks WHERE habit_id=?",
                (input_id,))

            return self._fetch_data()

        except Exception as e:
            msg = f"Error while reading task table:  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseFetchDataError(reason=msg, original_error=e)

    def find_by_habit_name(self, value: str):

        super()._ensure_connection()

        logger.info(f"Searching for task with name: {value}")

        try:
            # Search for name (lowercase) in database
            self.cursor.execute(
                "SELECT habit_name, habit_id, due_date, is_overdue, completion_status FROM tasks WHERE LOWER(habit_name)=?",
                (value.lower(),))

            return self._fetch_data()

        except Exception as e:
            msg = f"Error while reading task table:  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseFetchDataError(reason=msg, original_error=e)

    def browse_all(self):

        super()._ensure_connection()

        logger.info(f"Browsing all tasks")

        try:
            # Get all entries
            self.cursor.execute("SELECT * FROM tasks")

            return self._fetch_data()

        except Exception as e:
            msg = f"Error while reading task table:  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseFetchDataError(reason=msg, original_error=e)


class CompletionRecordRepository(RepositoryInterface):
    """
    Repository for persisted historical completion records.

    Completion records represent the history of completed or skipped tasks.
    Unlike Task objects, records are not intended to be changed directly by
    the user. They are created when TaskManager processes a task completion
    or skip action.

    Each record stores the related habit information, the original due date,
    whether the task was overdue, the completion date, and the final completion
    status.

    Inherits:
        RepositoryInterface: Provides the shared database connection handling
        and abstract repository method definitions.

    Notes:
        Completion records are used by RecordAnalyzer to calculate statistics
        such as streaks, completion rates, and on-time completion rates.
    """

    def __init__(self, db_path=None):
        """Initiates the RecordRepository object and sets up the basic attributes"""
        super().__init__(db_path) if db_path is not None else super().__init__()


    def _create_scheme(self):

        logger.info(f"Setting up scheme for completion_records table")
        self.cursor.execute(""" CREATE TABLE IF NOT EXISTS completion_records
                                (
                                    habit_name        TEXT    NOT NULL,
                                    habit_id          INTEGER NOT NULL,
                                    period            INTEGER NOT NULL,
                                    due_date          TEXT    NOT NULL,
                                    was_overdue       BOOLEAN NOT NULL,
                                    completion_date   TEXT    NOT NULL,
                                    completion_status TEXT    NOT NULL
                                )""")
        self.conn.commit()

    def _fetch_data(self):

        datapoint = self.cursor.fetchall()

        logger.info(f"Fetching data from completion_records table")

        if datapoint and isinstance(datapoint, (tuple, list)):
            result = [{"habit_name": datapoint[i][0],
                       "habit_id": datapoint[i][1],
                       "period": datapoint[i][2],
                       "due_date": datapoint[i][3],  # string format
                       "was_overdue": datapoint[i][4],
                       "completion_date": datapoint[i][5],  # string format
                       "completion_status": datapoint[i][6]} for i in range(len(datapoint))]
            return result
        else:
            return []

    def _convert_tuple(self, data: tuple):

        habit_name, habit_id, period, due_date, was_overdue, completion_date, completion_status = data

        converted_data = (
            habit_name,
            habit_id,
            period,
            dt_to_string(due_date),  # convert the datetime object to string
            was_overdue,
            dt_to_string(completion_date),  # convert the datetime object to string
            completion_status
        )

        return converted_data

    def create(self, data: tuple):

        super()._ensure_connection()

        converted_data = self._convert_tuple(data)

        try:
            self.cursor.execute("INSERT INTO completion_records VALUES (?, ?, ?, ?, ?, ?, ?)", converted_data)
            self.conn.commit()
            logging.debug(f"Completion record for Habit \"{converted_data[0]}\" (ID:{converted_data[1]}) created successfully\"")

        except Exception as e:
            msg = f"Error while record creation for Habit \"{converted_data[0]}\" (ID:{converted_data[1]}):  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseUpdateError(reason=msg, original_error=e)

    def update(self, data: tuple):

        super()._ensure_connection()

        try:
            # Update database
            self.cursor.execute(
                "UPDATE main.completion_records SET habit_name=? WHERE habit_id=?",
                data)
            self.conn.commit()
            logging.debug(f"Completion record for Habit \"{data[0]}\" (ID:{data[1]}) updated successfully\"")

        except Exception as e:
            msg = f"Error while updating completion_records table:  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseFetchDataError(reason=msg, original_error=e)

    def delete(self, data=None):
        pass  # Is not implemented yet, might make sense later on
        # ref_id = self.reference.habit_id
        # self.cursor.execute("DELETE FROM completion_records WHERE habit_id=?", (ref_id,))
        # self.conn.commit()

    def find_by_habit_id(self, input_id: int):

        super()._ensure_connection()

        logger.info(f"Searching for completion_records with ID: {input_id}")

        try:
            # Search for name (lowercase) in database
            self.cursor.execute(
                "SELECT habit_name, habit_id, period, due_date, was_overdue, completion_date, completion_status FROM completion_records WHERE habit_id=?",
                (input_id,))

            return self._fetch_data()

        except Exception as e:
            msg = f"Error while reading completion_records table:  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseFetchDataError(reason=msg, original_error=e)

    def find_by_habit_name(self, input_name: str):

        super()._ensure_connection()

        logger.info(f"Searching for completion_records with name: {input_name}")

        try:
            # Search for name (lowercase) in database
            self.cursor.execute(
                "SELECT habit_name, habit_id, period, due_date, was_overdue, completion_date, completion_status FROM completion_records WHERE LOWER(habit_name)=?",
                (input_name.lower(),))

            return self._fetch_data()

        except Exception as e:
            msg = f"Error while reading completion_records table:  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseFetchDataError(reason=msg, original_error=e)

    def browse_all(self):

        super()._ensure_connection()

        logger.info(f"Browsing all completion_records")

        try:
            # Get all entries
            self.cursor.execute("SELECT * FROM completion_records")

            return self._fetch_data()

        except Exception as e:
            msg = f"Error while reading completion_records table:  {type(e).__name__} | {e}"
            logging.critical(msg)
            raise DatabaseFetchDataError(reason=msg, original_error=e)
