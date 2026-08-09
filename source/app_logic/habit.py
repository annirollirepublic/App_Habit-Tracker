# Import datetime for datetime handling / BUILT-IN
from datetime import datetime
from idlelib import history

# Import exceptions and logging for activity screening and debugging / BUILT-IN
from source.helpers.exceptions import CreationFromDatabaseError, DuplicateHabitError

# Import logging for activity screening and debugging / BUILT-IN
import logging

# Import helper to handle conversion string to datetime and vice versa / USER-DEFINED
from source.helpers.utils_datetime_helper import string_to_dt

# Import enumeration classes / USER-DEFINED
from source.helpers.enums import Status, Period

# Import manager modules / USER-DEFINED
from source.app_logic.manager_modules import TaskManager

# Import analyzer modules / USER-DEFINED
from source.app_logic.analyzer_modules import RecordAnalyzer

# Import repository modules / USER-DEFINED
from source.repository.repository_modules import HabitRepository, TaskRepository, CompletionRecordRepository

# Set logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
        habit_id (int): existing habit ID (only for loading from DB, default: None)
        _from_db (bool): internal flag to skip duplicate check and save (default: False)

    Note:
        The user has no further influence on how tasks and records are stored.
        TaskManager and the repository interfaces take care of these methods in the background.
    """

    @classmethod
    def from_db(cls, habit_id: int):
        """Loading existing habit from the database without recreating it.
        This is necessary to launch habits for app operations from the database.
        Practically, this means this method ensures the possibility to create a habit for
        all habit-related operations without starting the initialization process.

        Args:
            habit_id (int): ID of the habit to be loaded from the database

        Returns:
            habit (Habit): Habit object with all attributes loaded from the database"""

        logger.info(f"APP: Loading Habit from DB with ID {habit_id}.")

        # Load habit data from database
        habit_repo = HabitRepository()
        habit_data_list = habit_repo.find_by_habit_id(habit_id)

        if not habit_data_list:
            logger.error(f"APP: No habit data found for ID {habit_id}. Cannot load habit.")
            raise ValueError(f"Habit with ID {habit_id} not found")

        # Extract habit data
        habit_data = habit_data_list[0]

        # Create without running __init__/__save_habit
        try:
            habit = cls.__new__(cls)

            # Set attributes directly
            habit._habit_id = habit_data["habit_id"]
            habit._habit_name = habit_data["habit_name"]
            habit._period = Period(int(habit_data["period"]))
            habit._start_date = string_to_dt(habit_data["start_date"])
            habit._status = Status(habit_data["status"])

            # Initialize internal repository interfaces
            habit.__habit_repo = HabitRepository()
            habit.__task_repo = TaskRepository()
            habit.__record_repo = CompletionRecordRepository()

            # Initiate Task Manager
            habit.__task_manager = TaskManager(habit.__task_repo, habit.__record_repo)

            # Load existing task from table (or create one if missing)
            # Only create task if habit is active, otherwise skip
            if habit._status == Status.ACTIVE:
                habit.__task_manager.create_first_task(habit)

            # Initiate Record Analyzer
            habit.__record_analyzer = RecordAnalyzer(habit.__record_repo)

            return habit

        except Exception as e:
            logger.critical(f"APP: Habit could not be created from database: {e}")
            raise CreationFromDatabaseError(reason=str(e), original_error=e)

    def __init__(self,
                 habit_name: str,
                 period: Period,
                 start_date: datetime = datetime.today(),
                 habit_id = None,
                 status = Status.ACTIVE):
        """Initiates the Habit object and creates connection to the TaskManager, as well as the repository interfaces
        With initiation of a habit a corresponding Task is directly instantiated by the corresponding TaskManager."""

        ## ATTRIBUTE ASSIGNMENT

        # User input variables
        self._habit_name = habit_name
        self._period = period
        self._start_date = start_date #datetime format

        # Automatic variables
        self._status = status

        # Initialize calculated values
        self._habit_id = habit_id

        logger.info(f"APP: Creating Habit object '{self.habit_name}' (ID {self._habit_id}).")

        # Create habit repository interface
        self.__habit_repo = HabitRepository()

        # Check whether input is duplicate - Creation will be blocked if is duplicate
        if self.__habit_repo.duplicate_naming(self) > 0:
            logger.error(f"APP: Duplicate habit name '{self._habit_name}' - creation blocked.")
            raise DuplicateHabitError(habit_name=self._habit_name)

        # If a duplicate check is passed, save to the repository and pass to the manager
        self.__save_habit()

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

    # INTERNAL CALLS

    def __save_habit(self):
        """Private method to save habit to a repository and create a corresponding task.
        This will only be called internally if a habit is newly created.
        Loading habits from the database will not trigger this method."""

        try:
            # Create habit entry
            self._habit_id = self.__habit_repo.get_largest_id() + 1
            self.__habit_repo.create(self)

            # Create interfaces to other repositories (to hand over to task manager)
            self.__task_repo = TaskRepository()
            self.__record_repo = CompletionRecordRepository()

            ## TASK MANAGER (for further task-related methods)

            # Initiate Task Manager
            self.__task_manager = TaskManager(self.__task_repo, self.__record_repo)
            # Create the first task entry
            self.__task_manager.create_first_task(self)

            # Initiate Record Analyzer
            self.__record_analyzer = RecordAnalyzer(self.__record_repo)

            logger.debug(f"APP: Habit '{self.habit_name}' (ID {self._habit_id}) data saved to repositories.")

        except Exception as e:
            logger.error(f"Error while creation of Habit '{self.habit_name}' (ID {self._habit_id}): {e}")
            raise e

    # INTERACTION

    def complete(self):
        """Call for the completion of the corresponding task
        -> calls TaskManager for complex business logics

        Returns:
            None
        """

        logger.info(f"APP: Completing current task for Habit '{self.habit_name}' (ID {self._habit_id}).")
        self.__task_manager.complete_current_task(self)

    def skip(self):
        """Call for the skipping of the corresponding task
        -> calls TaskManager for complex business logics

        Returns:
            None
        """

        logger.info(f"APP: Skipping current task for Habit '{self.habit_name}' (ID {self._habit_id}).")
        self.__task_manager.skip_current_task(self)

    # ADMINISTRATION

    def pause(self):
        """Sets habit status to "Paused" (only if it has been "Active" before)
        -> Calls habit repository interface to update the habit table
        -> Calls task manager to remove the corresponding task from the task table

        Returns:
            None
        """

        #Missing the check whether habit has been active before.
        self._status = Status.PAUSED
        logger.info(f"APP: Pausing Habit '{self.habit_name}' (ID {self._habit_id}).")
        self.__habit_repo.update(self)
        self.__task_manager.delete_current_task(self)

    def reactivate(self):
        """Sets habit status to "Active" (only if it has been "Paused" before)
        -> Calls habit repository interface to update the habit table
        -> Calls task manager to create a corresponding task and make entry in the task table

        Returns:
            None
        """

        # Missing the check whether habit has been paused before.
        self._status = Status.ACTIVE
        logger.info(f"APP: Reactivating Habit '{self.habit_name}' (ID {self._habit_id}).")
        self.__habit_repo.update(self)
        # Create the first task entry
        self.__task_manager.create_first_task(self)

    def delete(self):
        """Deletes habit from the habit table and all corresponding tasks
        -> Calls habit repository interface to delete the habit from the habit table
        -> Calls task manager to delete the corresponding task from the task table

        Returns:
            None

        Notes:
            Right now it is unclear how to handle the corresponding records.
        """

        logger.info(f"APP: Deleting Habit '{self.habit_name}' (ID {self._habit_id}).")
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
        logger.info(f"APP: Changing habit name to '{self.habit_name}' (ID {self._habit_id}).")
        self.__task_manager.update_current_task(self)
        self.__habit_repo.update(self)

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
        logger.info(f"APP: Changing habit period to '{self.period.value}' days (ID {self._habit_id}).")
        self.__task_manager.update_current_task(self)
        self.__habit_repo.update(self)

    @start_date.setter
    def start_date(self, value: datetime):
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

        self._start_date = value
        logger.info(f"APP: Changing habit start_date to '{self.start_date}' (ID {self._habit_id}).")
        self.__task_manager.update_current_task(self)
        self.__habit_repo.update(self)

    def calculate_current_streak(self):
        """Calculates the current streak of the habit.
        -> Calls the Record Analyzer to calculate the streak

        Args:
            None

        Returns:
            streak (Float): current streak"""

        logger.info(f"APP: Calculating current strike for habit '{self.start_date}' (ID {self._habit_id}).")
        return self.__record_analyzer.calculate_streak(self)

    def calculate_longest_streak(self):
        """Calculates the longest streak of the habit.
        -> Calls the Record Analyzer to calculate the longest streak

        Args:
            None

        Returns:
            longest_streak (Float): longest streak"""

        logger.info(f"APP: Calculating longest strike for habit '{self.start_date}' (ID {self._habit_id}).")
        return self.__record_analyzer.calculate_longest_streak(self)

    def complete_rate(self):
        """Calculates the completion rate of the habit.
        The completion rate is the ratio between
        the number of completed records and the total number of records (incl skipped).
        -> Calls the Record Analyzer to calculate the completion rate

        Args:
            None

        Returns:
            ratio (Float): completion rate"""

        logger.info(f"APP: Calculating completion rate for habit '{self.start_date}' (ID {self._habit_id}).")
        return self.__record_analyzer.calculate_completion_rate(self)

    def finished_ontime_rate(self):
        """Calculates the finished on-time rate of the habit.
        The finished on-time rate is the ratio between
        the number of completed records that were not overdue and the total number of records (incl skipped).

        Args:
            None

        Returns:
            ratio (Float): finished on time rate"""

        logger.info(f"APP: Calculating on-time rate for habit '{self.start_date}' (ID {self._habit_id}).")
        return self.__record_analyzer.calculate_finished_ontime_rate(self)

    def get_habit_history(self):
        """Returns a list of all completion records for a given habit.

        Args:
            None

        Returns:
            habit_history (list): List of all completion records for habit"""

        logger.info(f"APP: Request history for habit '{self.start_date}' (ID {self._habit_id}).")
        habit_history = self.__record_analyzer.habit_history(self)

        for record in habit_history:
            yield record
