from datetime import datetime, timedelta
#import traceback and logging for activity screening and debugging
import traceback
import logging
from enum import Enum
logging.basicConfig(level=logging.INFO, filename="habit-tracker.log", filemode="w", format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#import enum for the enumeration classes
#import repository modules
from repository_modules import *

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

    def __init__(self, habit_name: str, period: Period, start_date: datetime = datetime.now()):
        """Initiates the Habit object and creates connection to the TaskManager, as well as the repository interfaces
        With initiation of a habit a corresponding Task is directly instantiated by the corresponding TaskManager."""

        ## ATTRIBUTE ASSIGNMENT

        # User input variables
        self._habit_name = habit_name
        self._period = period
        self._start_date = start_date

        # Automatic variables
        self._status: Status = Status.ACTIVE

        # Initialize calculated values
        self._habit_id = None
        self._streak = None

        ## REPOSITORY CONNECTIONS

        # Connect to habit repository interface
        self.__habit_repo = HabitRepository(self)
        self.__task_repo = TaskRepository(self)
        self.__record_repo = CompletionRecordRepository(self)

        # Create habit entry
        self._habit_id = self.__habit_repo.get_largest_id() + 1
        self.__habit_repo.create()

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
        self.__habit_repo.update()
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
        self.__habit_repo.update()
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

        self.__habit_repo.delete(self._habit_id)
        self.__task_manager.delete_current_task(self)
        #self.__record_repo.delete(self._habit_id)

    @habit_name.setter
    def habit_name(self, value: str):
        self._habit_name = value
        self.__habit_repo.update()
        self.__task_repo.update()

    @period.setter
    def period(self, value: Period):
        self._period = value
        self.__habit_repo.update()
        self.__task_repo.update()

    @start_date.setter
    def start_date(self, value: datetime):
        self._start_date = value
        self.__habit_repo.update()
        self.__task_repo.update()

    # INTERACTION

class Task:
    """
    ...
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
        next_due_date = ref_task[0]["due_date"] + timedelta(days=habit.period.value)

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
            due_date = habit.start_date + timedelta(days=habit.period.value)

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
                                due_date=existing_task["due_date"],
                                completion_status=CompletionStatus(existing_task["completion_status"]))

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
                           datetime.today(),
                           CompletionStatus.COMPLETED)
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
                           datetime.today(),
                           CompletionStatus.SKIPPED)
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