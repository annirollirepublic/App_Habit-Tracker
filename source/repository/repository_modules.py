# Import config
from source import config

# Import ABC to provide an abstract interface for the repository interfaces / BUILT-IN
from abc import ABC, abstractmethod

# Import sqlite3 for database connection / BUILT-IN
import sqlite3

# Import typing to handle different type inputs in the abstract class / BUILT-IN
from typing import Any

# Import exceptions and logging for activity screening and debugging / BUILT-IN
from source.helpers.exceptions import *

# Import logging for activity screening and debugging / BUILT-IN
import logging

# Import helper to handle conversion string to datetime and vice versa / USER-DEFINED
from source.helpers.utils_datetime_helper import dt_to_string

# Import task class / USER-DEFINED
from source.app_logic.task import Task

# Set logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ========== REPOSITORY CLASSES ==========

class RepositoryInterface(ABC):
    """
    Abstract base class for all repository implementations.

    The repository interface defines the common database operations used by
    habit, task, and completion record repositories. It centralizes the
    database path, manages the SQLite connection, and requires subclasses to
    implement CRUD and lookup methods.

    Attributes:
        db_path (str): Path to the SQLite database file.
        conn (sqlite3.Connection | None): Active SQLite database connection, if available.
        cursor (sqlite3.Cursor): Cursor used to execute database statements after connection setup.

    Notes:
        This class should not be instantiated directly. Use one of its concrete
        subclasses instead, such as HabitRepository, TaskRepository, or
        CompletionRecordRepository.
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path if db_path is not None else config.global_db_path
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
        """This method ensures that a database connection is available.
        It checks if a connection is already open, and if not, attempts to create a new one."""

        logger.info(f"SQL: Checking for open connection")

        # Check if a connection is already open
        if self.conn is not None:
            # If no open connection available, check whether connection is live
            try:
                test_cursor = self.conn.cursor()
                test_cursor.execute("SELECT 1")  # If this does not through an error, the connection is live
                return
            except sqlite3.Error:  # If it through an error, the connection must be renewed
                self.conn = None
                self.cursor = None

        logger.info(f"SQL: No open connection available. Creating new connection")

        # Create a new connection
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            # Set up the database scheme
            self._create_scheme()
        except sqlite3.Error as e:
            logger.critical(f"SQL: Failed to create database connection: {type(e).__name__} | {e}")
            raise DatabaseConnectionError(reason=str(e), original_error=e)


class HabitRepository(RepositoryInterface):
    """
    Repository for persisting and retrieving current habits.

    The habit repository provides database access for Habit objects. It creates
    and manages the habit table, stores the currently open habit,
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

    def _create_scheme(self):
        """Sets up the database scheme for the habit table if it does not exist."""

        logger.info(f"SQL: Setting up scheme for habit table")

        # Set up the database scheme with all relevant columns
        try:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS habits
                                   (
                                       habit_name TEXT    NOT NULL,
                                       habit_id   INTEGER NOT NULL,
                                       period     INTEGER NOT NULL,
                                       start_date TEXT    NOT NULL,
                                       status     TEXT    NOT NULL
                                   )""")
            self.conn.commit()
            logger.debug(f"SQL: Scheme for habit table set up successfully")

        except Exception as e:
            logger.critical(f"SQL: Failed to set up scheme for habit table: {type(e).__name__} | {e}")
            raise DatabaseSchemeError(reason=str(e), original_error=e)

    def _fetch_data(self) -> list[dict[str, Any]] | list[Any]:

        logger.info(f"SQL: Fetching data from habit table")

        try:
            # Fetch all data from the database
            datapoint = self.cursor.fetchall()

            # Check if data is available and convert to list of dictionaries
            # If no data is available, return an empty list
            if datapoint and isinstance(datapoint, (tuple, list)):
                result = [{"habit_name": datapoint[i][0],
                           "habit_id": datapoint[i][1],
                           "period": datapoint[i][2],
                           "start_date": datapoint[i][3],  # string format
                           "status": datapoint[i][4]} for i in range(len(datapoint))]
                return result
            else:
                return []

        except Exception as e:
            logger.critical(f"SQL: Failed to fetch data from habit table: {type(e).__name__} | {e}")
            raise DatabaseFetchDataError(reason=str(e), original_error=e)

    def duplicate_naming(self, habit) -> int:
        """Checks whether a habit with the same name has already been created"""

        super()._ensure_connection()
        input_name = habit.habit_name

        logger.info(f"SQL: Checking for duplicate habit name: {input_name.lower()}")

        # Search for name (lowercase) in database and check how many entries are returned
        # Return number of duplicates (0 if no duplicates)
        try:
            self.cursor.execute("SELECT * FROM habits WHERE LOWER(habit_name)=?", (input_name.lower(),))
            duplicates_tuple = self.cursor.fetchall()
            duplicates_list = [duplicate[0] for duplicate in duplicates_tuple]
            return len(duplicates_list)

        except Exception as e:
            logger.error(f"SQL: Error while checking for duplicate habit name:  {type(e).__name__} | {e}")
            raise DatabaseFetchDataError(reason=str(e), original_error=e)

    def get_largest_id(self) -> int:
        """Returns the largest habit ID currently in use"""

        super()._ensure_connection()

        logger.info(f"SQL: Fetching largest ID")

        try:
            # Get all IDs as list
            self.cursor.execute("SELECT habit_id FROM habits")
            id_tuple = self.cursor.fetchall()

            # Get maximum value, return 0 if not entry is available
            id_list = [id_entry[0] for id_entry in id_tuple]
            return max(id_list, default=0)

        except Exception as e:
            logger.error(f"SQL: Error while fetching largest ID:  {type(e).__name__} | {e}")
            raise DatabaseFetchDataError(reason=str(e), original_error=e)

    def create(self, habit) -> None:
        """Creates a new habit datapoint in the database with all corresponding attributes.
        Before a new habit datapoint is created is checked whether a habit with the same name already exists in the database (case-sensitive)

        Args:
            habit (Habit): New habit for which a datapoint should be created
        """

        super()._ensure_connection()

        # Collect data for insertion in tuple format
        data = (habit.habit_name,
                habit.habit_id,
                habit.period.value,
                dt_to_string(habit.start_date),  # converted datetime
                habit.status.value)

        logger.info(f"SQL: Creating datapoint for habit: {habit.habit_name} (ID:{habit.habit_id})")

        # Insert data into database, if no duplicate is found
        if self.duplicate_naming(habit) == 0:
            try:
                self.cursor.execute("INSERT INTO habits VALUES (?, ?, ?, ?, ?)", data)
                self.conn.commit()
                logger.debug(f"SQL: Habit \"{habit.habit_name}\" (ID:{habit.habit_id}) created successfully\"")

            except Exception as e:
                logger.error(f"SQL: Error while creating Habit \"{habit.habit_name}\" (ID:{habit.habit_id}):  {type(e).__name__} | {e}")
                raise DatabaseUpdateError(reason=str(e), original_error=e)

        else:
            print("This habit already exists! Please edit the existing habit or choose a different name for your new habit.")

    def update(self, habit) -> None:
        """Updates an existing habit datapoint in the database with reference to the corresponding habit_id
        Before a habit datapoint is updated is checked whether a habit with the same name already exists in the database (case-sensitive)

        Args:
            habit (Habit): Habit with updated information (ID is persistent).
        """

        super()._ensure_connection()

        # Collect data for insertion in tuple format
        data = (habit.habit_name,
                habit.period.value,
                dt_to_string(habit.start_date),  # converted datetime
                habit.status.value)

        logger.info(f"SQL: Update datapoint for habit: {habit.habit_name} (ID:{habit.habit_id})")

        if self.duplicate_naming(habit) > 1:
            print("This habit already exists! Please edit the existing habit or choose a different name for your new habit.")

        try:
            self.cursor.execute("UPDATE habits SET habit_name=?, period=?, start_date=?, status=? WHERE habit_id=?",
                                (*data, habit.habit_id))
            self.conn.commit()
            logger.debug(f"SQL: Habit \"{habit.habit_name}\" (ID:{habit.habit_id}) updated successfully\"")

        except Exception as e:
            logger.error(f"SQL: Error while updating Habit \"{habit.habit_name}\" (ID:{habit.habit_id}):  {type(e).__name__} | {e}")
            raise DatabaseUpdateError(reason=str(e), original_error=e)

    def delete(self, habit) -> None:
        """Deletes an existing datapoint in the database with reference to the corresponding habit_id

        Args:
            habit (Habit): Habit that should be deleted from the database.
        """

        super()._ensure_connection()

        logger.info(f"SQL: Deleting habit datapoint")

        # Delete habit with specific habit_id
        try:
            self.cursor.execute("DELETE FROM habits WHERE habit_id=?", (habit.habit_id,))
            self.conn.commit()
            logger.debug(f"SQL: Habit \"{habit.habit_name}\" (ID:{habit.habit_id}) deleted successfully\"")

        except Exception as e:
            logger.error(f"SQL: Error while deleting Habit \"{habit.habit_name}\" (ID:{habit.habit_id}):  {type(e).__name__} | {e}")
            raise DatabaseUpdateError(reason=str(e), original_error=e)

    def find_by_habit_id(self, input_id: int) -> list[dict[str, Any]] | list[Any]:
        """Searches for the given ID within the database

        Args:
            input_id (int): The ID to be searched for

        Return:
            dict: A dictionary containing the habit data (habit_name, habit_id, period, start_date, status), if found.
            None: If no Habit with the given ID exists
        """

        super()._ensure_connection()

        logger.info(f"SQL: Searching for habit with ID: {input_id}")

        try:
            # Search for ID in database
            self.cursor.execute("SELECT habit_name, habit_id, period, start_date, status FROM habits WHERE habit_id=?",
                                (input_id,))
            return self._fetch_data()

        except Exception as e:
            logger.error(f"SQL: Error while reading habit table:  {type(e).__name__} | {e}")
            raise DatabaseFetchDataError(reason=str(e), original_error=e)

    def find_by_habit_name(self, input_name: str) -> list[dict[str, Any]] | list[Any]:
        """Searches for the given name within the database

        Args:
            input_name (str): The name to be searched for

        Returns:
            List of dict: A list of dictionaries containing the habit data (habit_name, habit_id, period, start_date, status) for all found habits with the given name.
            None: If no Habit with the given name exists
        """

        super()._ensure_connection()

        logger.info(f"SQL: Searching for habit with name: {input_name}")

        try:
            # Search for name (lowercase) in database
            self.cursor.execute(
                "SELECT habit_name, habit_id, period, start_date, status FROM habits WHERE LOWER(habit_name)=?",
                (input_name.lower(),))  # AttributeError: 'int' object has no attribute 'lower'
            return self._fetch_data()

        except Exception as e:
            logger.error(f"SQL: Error while reading habit table:  {type(e).__name__} | {e}")
            raise DatabaseFetchDataError(reason=str(e), original_error=e)

    def browse_all(self) -> list[dict[str, Any]] | list[Any]:
        """Searches for the given name within the database

        Returns:
            List of dict: A list of dictionaries containing all the habit data (habit_name, habit_id, period, start_date, status)
            None: If the database is empty
        """

        super()._ensure_connection()

        logger.info(f"SQL: Browsing all habits")

        try:
            # Get all entries
            self.cursor.execute("SELECT * FROM habits")
            return self._fetch_data()

        except Exception as e:
            logger.error(f"SQL: Error while reading habit table:  {type(e).__name__} | {e}")
            raise DatabaseFetchDataError(reason=str(e), original_error=e)


class TaskRepository(RepositoryInterface):
    """
    Repository for persisting and retrieving current habit tasks.

    The task repository provides database access for Task objects. It creates
    and manages the task table, stores the currently open task for each habit,
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
        super().__init__(db_path) if db_path is not None else super().__init__()

    def _create_scheme(self) -> None:
        """Sets up the database scheme for the task table if it does not exist."""

        logger.info(f"SQL: Setting up scheme for task table")

        # Set up the database scheme with all relevant columns
        try:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS tasks
                                   (
                                       habit_name        TEXT    NOT NULL,
                                       habit_id          INTEGER NOT NULL,
                                       due_date          TEXT    NOT NULL,
                                       is_overdue        BOOLEAN NOT NULL,
                                       completion_status TEXT    NOT NULL
                                   )""")
            self.conn.commit()
            logger.debug(f"SQL: Scheme for task table set up successfully")

        except Exception as e:
            logger.critical(f"SQL: Error while setting up scheme for task table:  {type(e).__name__} | {e}")
            raise DatabaseSchemeError(reason=str(e), original_error=e)

    def _fetch_data(self) -> list[dict[str, Any]] | list[Any]:

        logger.info(f"SQL: Fetching data from task table")

        try:
            # Fetch all data from the database
            datapoint = self.cursor.fetchall()

            # Check if data is available and convert to list of dictionaries
            # If no data is available, return an empty list
            if datapoint and isinstance(datapoint, (tuple, list)):
                result = [{"habit_name": datapoint[i][0],
                           "habit_id": datapoint[i][1],
                           "due_date": datapoint[i][2],  # string format
                           "is_overdue": datapoint[i][3],
                           "completion_status": datapoint[i][4]} for i in range(len(datapoint))]
                return result
            else:
                return []

        except Exception as e:
            logger.critical(f"SQL: Error while fetching data from task table:  {type(e).__name__} | {e}")
            raise DatabaseFetchDataError(reason=str(e), original_error=e)

    def create(self, task: Task) -> None:
        """Creates a new task in the database with the given attributes.

        Args:
            task (Task): task for which a datapoint should be created
        """

        super()._ensure_connection()

        # Collect data for insertion in tuple format
        data = (task.habit_name,
                task.habit_id,
                dt_to_string(task.due_date),  # converted datetime
                task.is_overdue,
                task.completion_status.value)

        logger.info(f"SQL: Creating task for habit: {task.habit_name} (ID:{task.habit_id})")

        # Insert data into database
        try:
            self.cursor.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", data)
            self.conn.commit()
            logger.debug(f"SQL: Task for habit \"{task.habit_name}\" (ID:{task.habit_id}) created successfully\"")

        except Exception as e:
            logger.error(f"SQL: Error while creating task for Habit \"{task.habit_name}\" (ID:{task.habit_id}):  {type(e).__name__} | {e}")
            raise DatabaseUpdateError(reason=str(e), original_error=e)

    def update(self, task: Task) -> None:
        """Updates an existing task in the database with the given attributes.

        Args:
            task (Task): Task with updated information (ID is persistent)."""

        super()._ensure_connection()

        # Collect data for insertion in tuple format
        data = (task.habit_name,
                dt_to_string(task.due_date),  # converted datetime
                task.is_overdue,
                task.completion_status.value)

        logger.info(f"SQL: Updating task for habit: {task.habit_name} (ID:{task.habit_id})")

        try:
            self.cursor.execute(
                "UPDATE tasks SET habit_name=?, due_date=?, is_overdue=?, completion_status=? WHERE habit_id=?",
                (*data, task.habit_id))
            self.conn.commit()
            logger.debug(f"SQL: Task \"{task.habit_name}\" (ID:{task.habit_id}) updated successfully\"")

        except Exception as e:
            logger.error(f"SQL: Error while updating task for Habit \"{task.habit_name}\" (ID:{task.habit_id}):  {type(e).__name__} | {e}")
            raise DatabaseUpdateError(reason=str(e), original_error=e)

    def delete(self, task: Task) -> None:
        """Deletes an existing task in the database for a referenced id.

        Args:
            task (Task): Task that should be deleted from the database"""

        super()._ensure_connection()

        logger.info(f"SQL: Deleting task for habit: {task.habit_name} (ID:{task.habit_id})")

        # Delete task with specific habit_id
        try:
            self.cursor.execute("DELETE FROM tasks WHERE habit_id=?", (task.habit_id,))
            self.conn.commit()
            logger.debug(f"SQL: Task \"{task.habit_name}\" (ID:{task.habit_id}) deleted successfully\"")

        except Exception as e:
            logger.error(f"SQL: Error while deleting task for Habit \"{task.habit_name}\" (ID:{task.habit_id}):  {type(e).__name__} | {e}")
            raise DatabaseUpdateError(reason=str(e), original_error=e)

    def find_by_habit_id(self, input_id: int) -> list[dict[str, Any]] | list[Any]:
        """Searches for the given ID within the database

        Args:
            input_id (int): The ID to be searched for

        Returns:
            List of dict: A list of dictionaries containing the task data (habit_name, habit_id, due_date, is_overdue, completion_status) for all found tasks with the given ID.
            None: If no Habit with the given name exists"""

        super()._ensure_connection()

        logger.info(f"SQL: Searching for task with ID: {input_id}")

        try:
            # Search for ID in database
            self.cursor.execute(
                "SELECT habit_name, habit_id, due_date, is_overdue, completion_status FROM tasks WHERE habit_id=?",
                (input_id,))
            return self._fetch_data()

        except Exception as e:
            logger.error(f"SQL: Error while reading task table:  {type(e).__name__} | {e}")
            raise DatabaseFetchDataError(reason=str(e), original_error=e)

    def find_by_habit_name(self, input_name: str) -> list[dict[str, Any]] | list[Any]:
        """Searches for the given name within the database

        Args:
            input_name (str): The name to be searched for

        Returns:
            List of dict: A list of dictionaries containing the task data (habit_name, habit_id, due_date, is_overdue, completion_status) for all found tasks with the given ID.
            None: If no Habit with the given name exists"""

        super()._ensure_connection()

        logger.info(f"SQL: Searching for task with name: {input_name}")

        try:
            # Search for name (lowercase) in database
            self.cursor.execute(
                "SELECT habit_name, habit_id, due_date, is_overdue, completion_status FROM tasks WHERE LOWER(habit_name)=?",
                (input_name.lower(),))
            return self._fetch_data()

        except Exception as e:
            logger.error(f"SQL: Error while reading task table:  {type(e).__name__} | {e}")
            raise DatabaseFetchDataError(reason=str(e), original_error=e)

    def browse_all(self) -> list[dict[str, Any]] | list[Any]:
        """Searches for the given name within the database

        Returns:
            List of dict: A list of dictionaries containing all the task data (habit_name, habit_id, due_date, is_overdue, completion_status)
            None: If the database is empty
        """

        super()._ensure_connection()

        logger.info(f"SQL: Browsing all tasks")

        try:
            # Get all entries
            self.cursor.execute("SELECT * FROM tasks")
            return self._fetch_data()

        except Exception as e:
            logger.error(f"SQL: Error while reading task table:  {type(e).__name__} | {e}")
            raise DatabaseFetchDataError(reason=str(e), original_error=e)


class CompletionRecordRepository(RepositoryInterface):
    """
    Repository for persisted historical completion records.

    Completion records represent the history of completed or skipped tasks.
    Unlike Task objects, records are not intended to be changed directly by
    the user. They are created when TaskManager processes a task completion
    or skips action.

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
        super().__init__(db_path) if db_path is not None else super().__init__()

    def _create_scheme(self) -> None:
        """Sets up the database scheme for the record table if it does not exist."""

        logger.info(f"SQL: Setting up scheme for completion_records table")

        # Set up the database scheme with all relevant columns
        try:
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
            logger.debug(f"SQL: Scheme for completion_records table set up successfully")

        except Exception as e:
            logger.critical(f"SQL: Error while setting up scheme for completion_records table:  {type(e).__name__} | {e}")
            raise DatabaseSchemeError(reason=str(e), original_error=e)

    def _fetch_data(self) -> list[dict[str, Any]] | list[Any]:

        logger.info(f"SQL: Fetching data from completion_records table")

        try:
            # Fetch all data from the database
            datapoint = self.cursor.fetchall()

            # Check if data is available and convert to list of dictionaries
            # If no data is available, return an empty list
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

        except Exception as e:
            logger.critical(f"SQL: Error while fetching data from completion_records table:  {type(e).__name__} | {e}")
            raise DatabaseFetchDataError(reason=str(e), original_error=e)

    def _convert_tuple(self, data: tuple) -> tuple:
        """Converts a tuple of data into a tuple of strings for insertion into the database."""

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

    def create(self, data: tuple) -> None:
        """Creates a new completion record in the database with the given attributes.

        Args:
            data (Data to CompletionRecord): completion record for which a datapoint should be created
        """

        super()._ensure_connection()

        # Convert the tuple to a tuple of strings for insertion into the database
        converted_data = self._convert_tuple(data)

        # Insert data into database
        try:
            self.cursor.execute("INSERT INTO completion_records VALUES (?, ?, ?, ?, ?, ?, ?)", converted_data)
            self.conn.commit()
            logger.debug(f"SQL: Completion record for Habit \"{converted_data[0]}\" (ID:{converted_data[1]}) created successfully\"")

        except Exception as e:
            logger.error(f"SQL: Error while creating completion_records table:  {type(e).__name__} | {e}")
            raise DatabaseUpdateError(reason=str(e), original_error=e)

    def update(self, data: tuple) -> None:
        """Updates an existing record in the database with the given attributes.

        Args:
            data (Data to CompletionRecord): tuple to CompletionRecord with updated information (ID is persistent)."""

        super()._ensure_connection()

        logger.info(f"SQL: Updating completion record for habit: {data[0]} (ID:{data[1]})")

        try:
            # Update database
            self.cursor.execute(
                "UPDATE main.completion_records SET habit_name=? WHERE habit_id=?",
                data)
            self.conn.commit()
            logging.debug(f"SQL: Completion record for Habit \"{data[0]}\" (ID:{data[1]}) updated successfully\"")

        except Exception as e:
            logger.error(f"SQL: Error while updating completion_records table:  {type(e).__name__} | {e}")
            raise DatabaseUpdateError(reason=str(e), original_error=e)

    def delete(self, data : tuple) -> None:
        """Deletes all existing records in the database for a referenced id.

        Args:
            data (tuple): tuple with corresponding habit_name and habit_id
        """

        super()._ensure_connection()

        logger.info(f"SQL: Deleting completion record for habit: {data[0]} (ID:{data[1]})")

        try:
            self.cursor.execute("DELETE FROM completion_records WHERE habit_id=?", (data[1],))
            self.conn.commit()
            logger.debug(f"SQL: Records to \"{data[0]}\" (ID:{data[1]}) deleted successfully\"")

        except Exception as e:
            logger.error(f"SQL: Error while deleting completion_records table:  {type(e).__name__} | {e}")
            raise DatabaseUpdateError(reason=str(e), original_error=e)

    def find_by_habit_id(self, input_id: int) -> list[dict[str, Any]] | list[Any]:
        """Searches for the given ID within the database

        Args:
            input_id (int): The ID to be searched for

        Returns:
            List of dict: A list of dictionaries containing the task data (habit_name, habit_id, due_date, is_overdue, completion_status) for all found tasks with the given ID.
            None: If no Habit with the given name exists"""

        super()._ensure_connection()

        logger.info(f"SQL: Searching for completion_records with ID: {input_id}")

        try:
            # Search for ID in database
            self.cursor.execute(
                "SELECT habit_name, habit_id, period, due_date, was_overdue, completion_date, completion_status FROM completion_records WHERE habit_id=?",
                (input_id,))
            return self._fetch_data()

        except Exception as e:
            logger.error(f"SQL: Error while reading completion_records table:  {type(e).__name__} | {e}")
            raise DatabaseFetchDataError(reason=str(e), original_error=e)

    def find_by_habit_name(self, input_name: str) -> list[dict[str, Any]] | list[Any]:
        """Searches for the given name within the database

        Args:
            input_name (str): The name to be searched for

        Returns:
            List of dict: A list of dictionaries containing the task data (habit_name, habit_id, due_date, is_overdue, completion_status) for all found tasks with the given ID.
            None: If no Habit with the given name exists"""

        super()._ensure_connection()

        logger.info(f"SQL: Searching for completion_records with name: {input_name}")

        try:
            # Search for name (lowercase) in database
            self.cursor.execute(
                "SELECT habit_name, habit_id, period, due_date, was_overdue, completion_date, completion_status FROM completion_records WHERE LOWER(habit_name)=?",
                (input_name.lower(),))
            return self._fetch_data()

        except Exception as e:
            logger.error(f"SQL: Error while reading completion_records table:  {type(e).__name__} | {e}")
            raise DatabaseFetchDataError(reason=str(e), original_error=e)

    def browse_all(self) -> list[dict[str, Any]] | list[Any]:
        """Searches for the given name within the database

        Returns:
            List of dict: A list of dictionaries containing all the task data (habit_name, habit_id, due_date, is_overdue, completion_status)
            None: If the database is empty
        """

        super()._ensure_connection()

        logger.info(f"SQL: Browsing all completion_records")

        try:
            # Get all entries
            self.cursor.execute("SELECT * FROM completion_records")
            return self._fetch_data()

        except Exception as e:
            logger.error(f"SQL: Error while reading completion_records table:  {type(e).__name__} | {e}")
            raise DatabaseFetchDataError(reason=str(e), original_error=e)
