# Import enumeration classes / USER-DEFINED
from source.helpers.enums import CompletionStatus

# Import datetime module / BUILT-IN
from datetime import date, datetime

# Import datetime helper / USER-DEFINED

# Set logger
import logging
logger = logging.getLogger(__name__)

# TODO : Possible Implementation of Task as @dataclass, to get rid of the __init__ and equality, when task properties are equal
# For now no practical use of dataclasses, since the Task objects are never compared

class Task:
    """
    Value object representing one actionable task for a habit.

    A task stores the currently due occurrence of a habit. It contains the
    habit reference, due date, and completion status. Task instances are
    created and managed by TaskManager and persisted through TaskRepository.

    The class does not directly communicate with the database. Its only
    business logic is the dynamic calculation of whether the task is overdue.

    Args:
        habit_id (int): Unique identifier of the related habit.
        habit_name (str): Name of the related habit.
        due_date (datetime): Date and time when the task is due.
        completion_status (CompletionStatus): Current completion state of the task.

    Attributes:
        habit_name (str): Name of the related habit.
        habit_id (int): Unique identifier of the related habit.
        due_date (datetime): Due date of the task.
        completion_status (CompletionStatus): Current completion state.

    Properties:
        is_overdue (bool): True if the task due date is earlier than today, otherwise False.
    """

    def __init__(self, habit_id: int, habit_name: str, due_date: datetime, completion_status: CompletionStatus):
        self.habit_name = habit_name
        self.habit_id = habit_id
        self.due_date = due_date
        self.completion_status = completion_status

        logger.info(f" Creating Task for Habit '{self.habit_name}' (ID {self.habit_id}).")

    @property
    #overdue as a dynamic property, since it is recalculated every day
    def is_overdue(self):
        logger.info(f"Calculating whether Task is overdue for Habit '{self.habit_name}' (ID {self.habit_id}).")
        return self.due_date.date() < date.today()
