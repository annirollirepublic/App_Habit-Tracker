# In this file contains all helper functions that defined for the UI
# This includes functions for the following purposes
# - input, validation & confirmation
# - formatting
# - layout

# Import datetime for datetime handling / BUILT-IN
from datetime import datetime

# Import helper to handle conversion string to datetime and vice versa / USER-DEFINED
from source.helpers.utils_datetime_helper import string_to_dt

# Import readchar for keyboard input / BUILT-IN
from readchar import readkey, key

#========== OUTPUT METHODS ==========

def print_confirmation(message: str, success: bool = True):
    """Prints a confirmation message and waits for Enter."""
    prefix = "✓" if success else "✗"

    print(f"\n{prefix} {message}\n")
    input("Press Enter to continue...\n")


def print_error(message: str):
    """Prints an error message and waits for Enter."""
    print_confirmation(message, success=False)

#========== ESCAPE OPTION DEFINITION ==========

class EscapeOperation(Exception):
    """Raised when user input is ESC, to cancel the current operation."""
    pass

#========== USER INPUT METHODS ==========

def prompt_input(prompt: str, required: bool = True):
    """Prompts for user input with the ESC option.
    Returns None if empty and not required."""

    print(f"{prompt}: ", end="", flush=True)

    try:
        chars = []
        # loop until user enters a valid response
        while True:
            # Read single keystroke without waiting for ENTER, to fetch ESC in any case
            char = readkey()

            # ESC cancels the operation
            if char == key.ESC:
                raise EscapeOperation()

            # ENTER terminates the input collection
            elif char == key.ENTER:
                break

            # BACKSPACE removed last character
            elif char == key.BACKSPACE:
                if chars:
                    # remove last element and move cursor back again
                    chars.pop()
                    print("\b \b", end="", flush=True)

            # regular case - store and display character
            else:
                chars.append(char)
                print(char, end="", flush=True)

        # Blank line after pressing ENTER
        print()

        # Return the collected input
        if required and not chars:
            return None
        elif not required and not chars:
            return ""
        return "".join(chars).strip()

    # If user presses CTRL+C, exit the program (similar to pressing ESC)
    except KeyboardInterrupt:
        print()
        raise EscapeOperation()


def confirm(prompt: str = "Continue? (y/n): "):
    """Asks for y/n confirmation with ESC support.
    Returns True for 'y', False for 'n'."""

    print(prompt, end="", flush=True)

    try:
        # loop until user enters a valid response
        while True:
            # Read single keystroke without waiting for ENTER, to fetch ESC in any case
            char = readkey()

            # ESC cancels the operation
            if char == key.ESC:
                raise EscapeOperation()

            # Handle 'y' and 'n' upper and lowercase
            if char in ("y", "Y"):
                return True
            elif char in ("n", "N"):
                return False

            # Any other key is ignored, and we wait for the next input

    # If user presses CTRL+C, exit the program (similar to pressing ESC)
    except KeyboardInterrupt:
        print()
        raise EscapeOperation()


def get_user_shortcut_overview():
    """Reads a single shortcut from user input.
    Returns lowercase character. Re-prompts if invalid.
    """
    valid_shortcuts = "ncsedprahq"

    # Request shortcut from user and validates against valid shortcuts
    while True:
        shortcut = input("> ").strip().lower()

        if not shortcut:
            continue

        if len(shortcut) == 1 and shortcut in valid_shortcuts:
            return shortcut

        # Output error message if shortcut is not valid
        print("Invalid shortcut. Enter one of: n, c, s, e, d, p, r, a, h, q")

#========== VALIDATION METHODS ==========

def validate_habit_name(name: str):
    """Validates habit name. Returns name if valid, None otherwise."""

    # If no name is provided, return None
    if not name:
        return None

    # If name is too short, it is unlikely to make any sense
    if len(name) < 3:
        print("Error: Habit name must be at least 3 characters.")
        return None

    # If name is too long, displaying it in the overview screen will cause errors
    if len(name) > 50:
        print("Error: Habit name must not exceed 50 characters.")
        return None

    # Valid names are names that pass all the above checks
    return name


def validate_period_input(value: str):
    """Validates period input. Returns int value if valid, None otherwise."""

    # Currently only daily, weekly, bi-weekly or monthly habits are supported
    try:
        days = int(value) # Input value will be a string, must be a number
        if days not in [1, 7, 14, 30]:
            print("Error: Period must be 1, 7, 14, or 30 days.")
            return None
        return days
    except ValueError: # If not a number, error is raised
        print("Error: Please enter a valid number.")
        return None


def validate_date_string(date_str: str) -> datetime | None:
    """Parses and validates date string in YYYY-MM-DD format."""
    if not date_str:
        # If no date is provided, return today's date is the default value
        return datetime.today()
    try:
        # Conversion will fail if the date format is invalid
        return string_to_dt(date_str)
    except ValueError:
        print("Error: Invalid date format. Use YYYY-MM-DD.")
        return None

#========== FORMATTING METHODS ==========

def format_relative_date(due_date: str):
    """
    Returns (label, category) for relative date display in the start screen / overview screen.
    Categories: 'overdue', 'today', 'this_week', 'upcoming'
    This categorization only applies to active habits. Paused habits are handled separately.
    """

    # reference date is always today
    today = datetime.today().date()
    due_date = string_to_dt(due_date).date()
    delta_days = (due_date - today).days

    # Check for delta and assign label and category accordingly
    if delta_days < 0:
        abs_delta = abs(delta_days)
        label = f"{abs_delta} day{'s' if abs_delta > 1 else ''} overdue"
        category = "overdue"
    elif delta_days == 0:
        label = "today"
        category = "today"
    elif delta_days <= 7:
        label = f"in {delta_days} day{'s' if delta_days > 1 else ''}"
        category = "this_week"
    else:
        label = f"in {delta_days} days"
        category = "upcoming"

    return label, category


def print_separator(char: str = "=", length: int = 50) -> None:
    """Prints a visual separator line."""
    print(char * length)


def print_header(text: str, width: int = 50) -> None:
    """Prints a formatted header."""
    print_separator("=")
    center_text = text.center(width)
    print(center_text)
    print_separator("=")