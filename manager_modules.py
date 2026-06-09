# Import datetime module / BUILT-IN
from datetime import timedelta
# Import datetime helper / USER-DEFINED
from utils_datetime_helper import *

# Import task class / USER-DEFINED
from task import Task

# Set logger
import logging
logger = logging.getLogger(__name__)

# Import enumeration classes / USER-DEFINED
from enums import *

# Import repository modules / USER-DEFINED
from repository_modules import *

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

        self.__task_repo = task_repo
        self.__record_repo = record_repo
        self.task = None

    def __create_new_task(self, habit):
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

        logger.info(f"Creating new task for habit {habit.habit_name} (ID {habit.habit_id})")

        # Get relevant information on referenced task from repository
        ref_task = self.__task_repo.find_by_habit_id(habit.habit_id)
        next_due_date = string_to_dt(ref_task[0]["due_date"]) + timedelta(days=habit.period.value)

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

        ref_task = self.__task_repo.find_by_habit_id(habit.habit_id)

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

        else:
            existing_task = ref_task[0]

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
                           dt_to_string(self.task.due_date),
                           self.task.is_overdue,
                           dt_to_string(datetime.today()),
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
                           dt_to_string(self.task.due_date),
                           self.task.is_overdue,
                           dt_to_string(datetime.today()),
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

        old_due_date = string_to_dt(ref_task[0]["due_date"]) #conversion from string to datetime format
        new_due_date = habit.start_date + timedelta(days=habit.period.value)
        while new_due_date <= old_due_date:
            new_due_date += timedelta(days=habit.period.value)

        updated_task = Task(habit_id=habit.habit_id,
                         habit_name=habit.habit_name,
                         due_date=new_due_date,
                         completion_status=CompletionStatus.PENDING)

        self.task = updated_task

        self.__task_repo.update(self.task)

        updated_record_data = (habit.habit_name,
                           habit.period.value,
                           dt_to_string(self.task.due_date),
                           self.task.is_overdue,
                           dt_to_string(datetime.today()),
                           CompletionStatus.COMPLETED.value,
                           habit.habit_id)

        self.__record_repo.update(updated_record_data)

        return self.task