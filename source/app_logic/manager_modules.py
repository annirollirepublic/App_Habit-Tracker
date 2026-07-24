# Import datetime module / BUILT-IN
from datetime import timedelta, datetime

# Import datetime helper / USER-DEFINED
from source.helpers.utils_datetime_helper import string_to_dt

# Import task class / USER-DEFINED
from source.app_logic.task import Task

# Import logging for activity screening and debugging / BUILT-IN
import logging

# Import enumeration classes / USER-DEFINED
from source.helpers.enums import CompletionStatus

# Import repository modules / USER-DEFINED
from source.repository.repository_modules import TaskRepository, CompletionRecordRepository, HabitRepository

# Set logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


#========== SERVICES CLASSES ==========

class TaskManager:
    """
    Service class responsible for task lifecycle management.

    TaskManager coordinates task-related business logic between Habit,
    TaskRepository, and CompletionRecordRepository. It creates initial tasks,
    completes or skips current tasks, generates follow-up tasks, updates tasks
    after habit changes, and removes tasks when habits are paused or deleted.

    The manager keeps the currently active Task object in memory and ensures
    that task changes are mirrored in the database.

    Args:
        task_repo (TaskRepository): Repository used to persist and retrieve current tasks.
        record_repo (CompletionRecordRepository): Repository used to store historical completion records.

    Attributes:
        task (Task | None): The currently active task managed by this instance.

    Notes:
        This class is an internal coordination layer and is normally accessed
        through Habit methods such as complete(), skip(), pause(), reactivate(),
        delete(), or property setters.
    """

    def __init__(self, task_repo: TaskRepository, record_repo: CompletionRecordRepository):
        """Initiates the TaskManager object and creates connection to the repository interfaces of tasks and completion records.
        """

        # Ensure connections to necessary repositories
        self.__task_repo = task_repo
        self.__record_repo = record_repo

        # Corresponding Task will be initialized later
        self.task = None

    def __create_new_task(self, habit):
        """Private method to handle the deletion of an old task creation of a new one with updated due_date
        -> Calls the Task repository to get the old task by ID of the corresponding habit
        -> Calculates next due_date with the last due_date and the periodicity from the habit
        -> Calls the Task repository to delete the old task datapoint by ID
        -> Calls the Task repository to create a new task datapoint for the habit with the new due_date

        Args:
            habit(Habit): Habit for which the task should be deleted and created

        Returns:
            Task: Task with new due_date"""

        logger.info(f"Creating new task for habit {habit.habit_name} (ID {habit.habit_id})")

        # Get relevant information on referenced "old" task from repository
        ref_task = self.__task_repo.find_by_habit_id(habit.habit_id)
        if isinstance(ref_task, list):
            next_due_date = string_to_dt(ref_task[0]["due_date"]) + timedelta(days=habit.period.value)
        else:
            next_due_date = string_to_dt(ref_task["due_date"]) + timedelta(days=habit.period.value)

        # Create new task, delete old task
        self.__task_repo.delete(self.task)

        new_task = Task(habit_id=habit.habit_id,
                         habit_name=habit.habit_name,
                         due_date=next_due_date,
                         completion_status=CompletionStatus.PENDING)

        self.task = new_task

        self.__task_repo.create(self.task)

        return self.task

    def create_first_task(self, habit):
        """Creates a new task for the given habit or instantiates an existing task from table.
        -> Calls task repository interface to check whether corresponding task in database exists
            if no: due_date is calculated (start_date + period) and new Task object is created
            if yes, task object is instantiated from the task table

        Args:
            habit (Habit): Habit object for which a Task object should be created

        Returns:
            Task: The created Task object will be returned
        """

        logger.info(f"Creating first task for habit {habit.habit_name} (ID {habit.habit_id})")

        # Check whether task to habit already exists
        # There should be only one task per habit
        ref_task = self.__task_repo.find_by_habit_id(habit.habit_id)

        # If no task exists, create a new one
        if not ref_task:
            # Calculate the due_date and make a new entry
            due_date = habit.start_date #datetime format

            initial_task = Task(habit_id=habit.habit_id,
                                habit_name=habit.habit_name,
                                due_date=due_date,
                                completion_status=CompletionStatus.PENDING)

            self.task = initial_task

            self.__task_repo.create(self.task)
            return self.task

        # If a task exists, instantiate it
        else:
            if isinstance(ref_task, list):
                existing_task = ref_task[0]
            else:
                existing_task = ref_task

            # Instantiate object from task table
            loaded_task = Task(habit_id=existing_task["habit_id"],
                                habit_name=existing_task["habit_name"],
                                due_date=string_to_dt(existing_task["due_date"]), #conversion back to datetime format
                                completion_status=CompletionStatus.PENDING)

            self.task = loaded_task

            return self.task

    def complete_current_task(self, habit):
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
                           habit.period.value,
                           self.task.due_date,
                           self.task.is_overdue,
                           datetime.today(),
                           CompletionStatus.COMPLETED.value)
        self.__record_repo.create(completion_data)

        # Create new task, delete old task
        new_task = self.__create_new_task(habit)

        self.task = new_task

        return self.task

    def skip_current_task(self, habit):
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
                           habit.period.value,
                           self.task.due_date,
                           self.task.is_overdue,
                           datetime.today(),
                           CompletionStatus.SKIPPED.value)
        self.__record_repo.create(completion_data)

        # Create new task, delete old task
        new_task = self.__create_new_task(habit)

        self.task = new_task

        return self.task

    def delete_current_task(self, data=None):
        """Processes the deletion of tasks by ID
        -> Calls Task repository to remove the task from table by ID
        """

        self.__task_repo.delete(self.task)

    def update_current_task(self, habit):
        """Processes the update of a task, according to changes in the habit
        - Request the habit table to get the current values of the habit
        - Request the record table to get the last record of the habit for re-calculation
        - Call the task repository to get the corresponding task entry
        - Re-calculate task attributes according to changes in the habit
        - Call the task repository to change the task entry attributes according to changes in the habit

        Args:
            habit (Habit): Habit object for which the task should be updated

        Returns:
              Task: The newly created Task object will be returned

        Notes:
            The calculation for the new due_date will be executed also if start_date and periodicity has not changed.
            If there is no change the result will be new_due_date == old_due_date
        """

        # Get current values from habit table (before update) for reference
        habit_repo = HabitRepository()
        old_habit_data = habit_repo.find_by_habit_id(habit.habit_id)

        # Handle case where no habit data exists
        if not old_habit_data:
            logger.warning(f"No habit data found for ID {habit.habit_id}. Cannot update task.")
            return self.task

        old_habit_data = old_habit_data[0] if isinstance(old_habit_data, list) else old_habit_data

        # Get last record from record table for reference
        record_repo = CompletionRecordRepository()
        records = record_repo.find_by_habit_id(habit.habit_id)

        # Sort records by completion date in descending order
        records_sorted = sorted(records, key=lambda x: string_to_dt(x['completion_date']), reverse=True)
        last_record = records_sorted[0] if records_sorted else None
        last_record_date = string_to_dt(last_record["completion_date"]) if last_record else None

        # Get current task from task table
        ref_task = self.__task_repo.find_by_habit_id(habit.habit_id)

        # Handle case where no task exists
        if not ref_task:
            logger.warning(f"No task found for habit ID {habit.habit_id}. Skipping task update.")
            return self.task

        ref_task = ref_task[0] if isinstance(ref_task, list) else ref_task

        # Parse old habit data and get relevant attributes for re-calculation
        old_start_date = string_to_dt(old_habit_data["start_date"])
        old_period = int(old_habit_data["period"])
        old_due_date = string_to_dt(ref_task["due_date"])

        # Check whether time-relevant attributes have changed
        start_date_changed = old_start_date != habit.start_date
        period_changed = old_period != habit.period.value

        # Handle case where start_date or period has changed
        if start_date_changed or period_changed:
            # Calculate new due_date
            # new due_date should be terminated after last record date
            new_due_date = habit.start_date
            if last_record_date:
                while new_due_date <= last_record_date:
                    new_due_date += timedelta(days=habit.period.value)
            else:
                while new_due_date <= old_due_date:
                    new_due_date += timedelta(days=habit.period.value)
        else:
            # Keep existing due_date if neither start_date nor period changed
            new_due_date = old_due_date

        # Only update task if due_date actually changed
        if new_due_date != old_due_date or habit.habit_name != old_habit_data["habit_name"]:
            updated_task = Task(
                habit_id=habit.habit_id,
                habit_name=habit.habit_name,
                due_date=new_due_date,
                completion_status=CompletionStatus.PENDING
            )

            self.task = updated_task
            self.__task_repo.update(self.task)

            # Update historical data (habit_name only)
            updated_record_data = (habit.habit_name, habit.habit_id)
            self.__record_repo.update(updated_record_data)

        return self.task