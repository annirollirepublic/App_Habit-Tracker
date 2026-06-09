# Import enum for the enumeration classes / BUILT-IN
from enum import Enum

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