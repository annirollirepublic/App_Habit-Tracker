class AppError(Exception):
    """
    Base class for exceptions in this application
    """
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class DatabaseConnectionError(AppError):
    def __init__(self, reason: str, original_error: Exception | None = None):
        message = f"Error when trying to connect to database: {reason}"
        super().__init__(message, {"reason": reason})
        self.original_exception = original_error

class DatabaseUpdateError(AppError):
    def __init__(self, reason: str, original_error: Exception | None = None):
        message = f"Error when trying to update database: {reason}"
        super().__init__(message, {"reason": reason})
        self.original_exception = original_error

class DatabaseFetchDataError(AppError):
    def __init__(self, reason: str, original_error: Exception | None = None):
        message = f"Error when trying to fetch data from database: {reason}"
        super().__init__(message, {"reason": reason})
        self.original_exception = original_error

class DuplicateHabitError(AppError):
    def __init__(self, habit_name: str):
        super().__init__(f"Habit \"{habit_name}\" already exists in database.")