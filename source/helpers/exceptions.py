class AppError(Exception):
    # Base class for exceptions in this application
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class DatabaseConnectionError(AppError):
    # Raised exception when database connection fails
    def __init__(self, reason: str, original_error: Exception | None = None):
        super().__init__(reason,
                         {"reason": reason, "error_type": type(original_error).__name__ if original_error else None})
        self.original_exception = original_error

class DatabaseSchemeError(AppError):
    # Raised exception when database scheme is not set up correctly
    def __init__(self, reason: str, original_error: Exception | None = None):
        super().__init__(reason,
                         {"reason": reason, "error_type": type(original_error).__name__ if original_error else None})
        self.original_exception = original_error

class DatabaseUpdateError(AppError):
    # Raised exception when database update fails
    def __init__(self, reason: str, original_error: Exception | None = None):
        super().__init__(reason,
                         {"reason": reason, "error_type": type(original_error).__name__ if original_error else None})
        self.original_exception = original_error

class DatabaseFetchDataError(AppError):
    # Raised exception when database fetch fails
    def __init__(self, reason: str, original_error: Exception | None = None):
        super().__init__(reason,
                         {"reason": reason, "error_type": type(original_error).__name__ if original_error else None})
        self.original_exception = original_error

class DuplicateHabitError(AppError):
    # Raised exception when a habit with the same name already exists
    def __init__(self, habit_name: str):
        reason = f"Habit \"{habit_name}\" already exists in database."
        super().__init__(reason)

class CreationFromDatabaseError(AppError):
    # Raised exception when a habit cannot be created from the database
    def __init__(self, reason: str, original_error: Exception | None = None):
        super().__init__(reason,
                         {"reason": reason, "error_type": type(original_error).__name__ if original_error else None})
        self.original_exception = original_error