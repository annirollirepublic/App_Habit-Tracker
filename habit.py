# Imported via other imported modules:
# utils_datetime_helper, enums, repository_modules

# Set logger
import logging
logger = logging.getLogger(__name__)

# Import manager modules / USER-DEFINED
from manager_modules import *

# Import analyzer modules / USER-DEFINED
from analyzer_modules import *

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

        logger.info(f" Creating Habit '{self.habit_name}' (ID {self._habit_id}).")

        ## REPOSITORY CONNECTION

        # Connect to habit repository interface
        self.__habit_repo = HabitRepository()

        # Check whether input is duplicate - Creation will be blocked if is duplicate
        if self.__habit_repo.duplicate_naming(self) > 0:
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

    def __save_habit(self) -> None:

        try:
            # Create habit entry
            self._habit_id = self.__habit_repo.get_largest_id() + 1
            self.__habit_repo.create(self)

            # Create interfaces to other repositories (to hand over to task manager)
            self.__task_repo = TaskRepository()
            self.__record_repo = CompletionRecordRepository()

            ## TASK MANAGER (for further task related methods)

            # Initiate Task Manager
            self.__task_manager = TaskManager(self.__task_repo, self.__record_repo)
            # Create the first task entry
            self.__task_manager.create_first_task(self)

            # Initiate Record Analyzer
            self.__record_analyzer = RecordAnalyzer(self.__record_repo)

            logger.info(f" Habit '{self.habit_name}' (ID {self._habit_id}) created successfully.")

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

        logger.info(f" Completing current task for Habit '{self.habit_name}' (ID {self._habit_id}).")
        self.__task_manager.complete_current_task(self)

    def skip(self):
        """Call for the skipping of the corresponding task
        -> calls TaskManager for complex business logics

        Returns:
            None
        """

        logger.info(f" Skipping current task for Habit '{self.habit_name}' (ID {self._habit_id}).")
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
        logger.info(f" Pausing Habit '{self.habit_name}' (ID {self._habit_id}).")
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
        logger.info(f" Reactivating Habit '{self.habit_name}' (ID {self._habit_id}).")
        self.__habit_repo.update(self)
        # Create the first task entry
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

        logger.info(f" Deleting Habit '{self.habit_name}' (ID {self._habit_id}).")
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
        logger.info(f" Changing habit name to '{self.habit_name}' (ID {self._habit_id}).")
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
        logger.info(f" Changing habit period to '{self.period.value}' days (ID {self._habit_id}).")
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

        self._start_date = string_to_dt(value)
        logger.info(f" Changing habit start_date to '{self.start_date}' (ID {self._habit_id}).")
        self.__habit_repo.update(self)
        self.__task_manager.update_current_task(self)

    def calculate_current_streak(self):

        self.__record_analyzer.calculate_streak(self)