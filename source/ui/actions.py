# This file contains all actual actions that can be performed by the user (API)
# This includes functions for the following purposes
# - create new habits
# - complete/skip tasks
# - pause/activate habits
# - edit habit information
# - delete habits
# - view analytics

# Import Habit class for API access / USER-DEFINED
from source.app_logic.habit import Habit

# Import enums / USER-DEFINED
from source.helpers.enums import Period

# Import helpers for input, validation, and formatting / USER-DEFINED
from source.ui.helpers import *

# Import overview functions for habit selection / USER-DEFINED
from source.ui.overview import get_habit_for_action

# ==================== HABIT CREATION ====================

def create_new_habit() -> None:
    """Flow for creating a new habit.
    shortcut: n"""
    print("\n--- Create New Habit ---\n")

    try:
        # Request the user to put habit name and period
        # Input will be validated by specific functions from helpers.py
        name = prompt_input("Habit name")
        name = validate_habit_name(name)
        if not name:
            print_error("Invalid habit name.")
            return

        period_input = prompt_input("Period (1=daily, 7=weekly, 14=biweekly, 30=monthly)")
        period_days = validate_period_input(period_input)
        if not period_days:
            print_error("Invalid period.")
            return

        # Request the user to put start date (optional)
        # If not provided, start date will be set to today
        date_input = prompt_input("Start date (YYYY-MM-DD) [today]", required=False)
        start_date = validate_date_string(date_input) if date_input else None # Default to today is set in Habit Class

        # Creation summary
        print(f"\nName: {name}")
        print(f"Period: {period_days} days")
        print(f"Start date: {start_date.strftime('%Y-%m-%d') if start_date else 'today'}")

        # Confirmation prompt
        if not confirm("\nCreate this habit? (y/n): "):
            print_confirmation("Habit creation cancelled.")
            return

        if start_date:
            habit = Habit(name, Period(period_days), start_date)
        else:
            habit = Habit(name, Period(period_days))

        print_confirmation(f"Habit '{habit.habit_name}' created (ID: {habit.habit_id}).")

    # Catching escape logics (ESC/CTRL+C)
    except EscapeOperation:
        print_confirmation("Habit creation cancelled.", False)
        return

    except Exception as e:
        print_error(f"Error creating habit: {e}")


# ==================== TASK INTERACTION ====================

def complete_task() -> None:
    """Flow for completing a task.
    shortcut: c"""
    print("\n--- Complete Task ---\n")

    # Check if there are any active tasks to complete
    try:
        habit_dict = get_habit_for_action(["complete"])
        if not habit_dict:
            print_error("No active habits to complete.")
            return

    # Catching invalid input (e.g., user enters a non-numeric value)
    except ValueError:
        print_error("Invalid input. Please enter a number from the list to select a habit.")
        return

    # Catching escape logics (ESC/CTRL+C)
    except EscapeOperation:
        print_confirmation("Habit completion cancelled.", False)
        return

    # Catching unspecific exceptions
    except Exception as e:
        print_error(f"Error: {e}")
        return

    # If all checks pass, continue with habit completion
    # Load habit from database using habit_id
    try:
        habit = Habit.from_db(habit_dict["habit_id"])
    except Exception as e:
        print_error(f"Could not load habit from database: {e}")
        return

    # Confirmation prompt for habit completion
    try:
        if not confirm(f"Complete task '{habit.habit_name}'? (y/n): "):
            print_confirmation("Task completion cancelled.")
            return
    except EscapeOperation:
        print_confirmation("Habit completion cancelled.", False)

    # Complete habit
    try:
        habit.complete()
        print_confirmation(f"Task '{habit.habit_name}' completed successfully.")

    except Exception as e:
        print_error(f"Error completing task: {e}")


def skip_task() -> None:
    """Flow for skipping a task.
    shortcut: s"""
    print("\n--- Skip Task ---\n")

    # Check if there are any active tasks to skip
    try:
        habit_dict = get_habit_for_action(["skip"])
        if not habit_dict:
            print_error("No active habits to skip.")
            return

    # Catching invalid input (e.g., user enters a non-numeric value)
    except ValueError:
        print_error("Invalid input. Please enter a number from the list to select a habit.")
        return

    # Catching escape logics (ESC/CTRL+C)
    except EscapeOperation:
        print_confirmation("Habit skipping cancelled.", False)
        return

    # Catching unspecific exceptions
    except Exception as e:
        print_error(f"Error: {e}")
        return

    # If all checks pass, continue with habit skipping
    # Load habit from database using habit_id
    try:
        habit = Habit.from_db(habit_dict["habit_id"])
    except Exception as e:
        print_error(f"Could not load habit from database: {e}")
        return

    # Confirmation prompt for habit skipping
    try:
        if not confirm(f"Skip task '{habit.habit_name}'? (y/n): "):
            print_confirmation("Task skip cancelled.")
            return
    except EscapeOperation:
        print_confirmation("Habit skipping cancelled.", False)
        return

    # Skip habit
    try:
        habit.skip()
        print_confirmation(f"Task '{habit.habit_name}' skipped. Streak broken.")

    except Exception as e:
        print_error(f"Error skipping task: {e}")


# ==================== HABIT MANAGEMENT ====================

def pause_habit() -> None:
    """Flow for pausing a habit.
    shortcut: p"""
    print("\n--- Pause Habit ---\n")

    # Check if there are any active habits to pause
    try:
        habit_dict = get_habit_for_action(["pause"])
        if not habit_dict:
            print_error("No active habits to pause.")
            return

    # Catching invalid input (e.g., user enters a non-numeric value)
    except ValueError:
        print_error("Invalid input. Please enter a number from the list to select a habit.")
        return

    # Catching escape logics (ESC/CTRL+C)
    except EscapeOperation:
        print_confirmation("Habit pausing cancelled.", False)
        return

    # Catching unspecific exceptions
    except Exception as e:
        print_error(f"Error: {e}")
        return

    # If all checks pass, continue with habit pausing
    # Load habit from database using habit_id
    try:
        habit = Habit.from_db(habit_dict["habit_id"])
    except Exception as e:
        print_error(f"Could not load habit from database: {e}")
        return

    # Confirmation prompt for habit pausing
    try:
        if not confirm(f"Pause habit '{habit.habit_name}'? (y/n): "):
            print_confirmation("Habit pause cancelled.")
            return
    except EscapeOperation:
        print_confirmation("Habit pausing cancelled.", False)
        return

    # Pause habit
    try:
        habit.pause()
        print_confirmation(f"Habit '{habit.habit_name}' paused.")

    except Exception as e:
        print_error(f"Error pausing habit: {e}")


def reactivate_habit() -> None:
    """Flow for reactivating a habit (shortcut: r)."""
    print("\n--- Reactivate Habit ---\n")

    # Check if there are any paused habits to reactivate
    try:
        habit_dict = get_habit_for_action(["reactivate"])
        if not habit_dict:
            print_error("No paused habits to reactivate.")
            return

    # Catching invalid input (e.g., user enters a non-numeric value)
    except ValueError:
        print_error("Invalid input. Please enter a number from the list to select a habit.")
        return

    # Catching escape logics (ESC/CTRL+C)
    except EscapeOperation:
        print_confirmation("Habit reactivation cancelled.", False)
        return

    # Catching unspecific exceptions
    except Exception as e:
        print_error(f"Error: {e}")
        return

    # If all checks pass, continue with habit reactivation
    # Load habit from database using habit_id
    try:
        habit = Habit.from_db(habit_dict["habit_id"])
    except Exception as e:
        print_error(f"Could not load habit from database: {e}")
        return

    # Confirmation prompt for habit reactivation
    try:
        if not confirm(f"Reactivate habit '{habit.habit_name}'? (y/n): "):
            print_confirmation("Habit reactivation cancelled.")
            return
    except EscapeOperation:
        print_confirmation("Habit reactivation cancelled.", False)
        return

    # Reactivate habit
    try:
        habit.reactivate()
        print_confirmation(f"Habit '{habit.habit_name}' reactivated.")

    except Exception as e:
        print_error(f"Error reactivating habit: {e}")


def edit_habit() -> None:
    """Flow for editing a habit (shortcut: e)."""
    print("\n--- Edit Habit ---\n")

    # Check if there are any habits to edit (paused and active)
    try:
        habit_dict = get_habit_for_action(["edit"])
        if not habit_dict:
            print_error("No habits available for editing.")
            return

    # Catching invalid input (e.g., user enters a non-numeric value)
    except ValueError:
        print_error("Invalid input. Please enter a number from the list to select a habit.")
        return

    # Catching escape logics (ESC/CTRL+C)
    except EscapeOperation:
        print_confirmation("Habit edit cancelled.", False)
        return

    # Catching unspecific exceptions
    except Exception as e:
        print_error(f"Error: {e}")
        return

    # If all checks pass, continue with habit editing
    # Load habit from database using habit_id
    try:
        habit = Habit.from_db(habit_dict["habit_id"])
    except Exception as e:
        print_error(f"Could not load habit from database: {e}")
        return

    # Display current values and prompt for editing
    print(f"\nCurrent values:")
    print(f"  Name: {habit.habit_name}")
    print(f"  Period: {habit.period.value} days")
    print(f"  Start date: {habit.start_date.strftime('%Y-%m-%d')}")

    print("\nWhat to edit?")
    print("  [1] Name")
    print("  [2] Period")
    print("  [3] Start date")

    # Request user input to select which value to edit
    try:
        choice = prompt_input("\nEnter choice (1-3)")

        # Handle invalid input
        if choice not in ["1", "2", "3"]:
            print_error("Invalid input. Please enter a number from the list to select a value.")
            return

        # Handle valid input based on user choice
        if choice == "1":
            new_name = prompt_input("New habit name")
            new_name = validate_habit_name(new_name)
            if not new_name:
                print_error("Invalid habit name.")
                return
            habit.habit_name = new_name
            print_confirmation(f"Habit renamed to '{new_name}'.")

        elif choice == "2":
            new_period_input = prompt_input("New period (1,7,14,30)")
            new_period_days = validate_period_input(new_period_input)
            if not new_period_days:
                print_error("Invalid period.")
                return
            habit.period = Period(new_period_days)
            print_confirmation(f"Habit period changed to {new_period_days} days.")

        elif choice == "3":
            new_date_input = prompt_input("New start date (YYYY-MM-DD)")
            new_date = validate_date_string(new_date_input)
            if not new_date:
                print_error("Invalid date.")
                return
            habit.start_date = new_date
            print_confirmation(f"Habit start date changed to {new_date.strftime('%Y-%m-%d')}.")

    # Catching escape logics (ESC/CTRL+C)
    except EscapeOperation:
        print_confirmation("\nHabit edit cancelled.", False)
        return

    # Catching unspecific exceptions
    except Exception as e:
        print_error(f"Error editing habit: {e}")


def delete_habit() -> None:
    """Flow for deleting a habit (shortcut: d)."""
    print("\n--- Delete Habit ---\n")

    # Check if there are any habits to delete
    try:
        habit_dict = get_habit_for_action(["delete"])
        if not habit_dict:
            print_error("No habits available for deletion.")
            return

    # Catching invalid input (e.g., user enters a non-numeric value)
    except ValueError:
        print_error("Invalid input. Please enter a number from the list to select a habit.")
        return

    # Catching escape logics (ESC/CTRL+C)
    except EscapeOperation:
        print_confirmation("Habit deletion cancelled.", False)
        return

    # Catching unspecific exceptions
    except Exception as e:
        print_error(f"Error: {e}")
        return

    # If all checks pass, continue with habit deletion
    # Load habit from database using habit_id
    try:
        habit = Habit.from_db(habit_dict["habit_id"])
    except Exception as e:
        print_error(f"Could not load habit from database: {e}")
        return

    # Confirmation prompt before deleting
    try:
        print(f"\n⚠ WARNING: This will DELETE '{habit.habit_name}' and all associated data!")
        if not confirm("Are you sure? (y/n): "):
            print_confirmation("Habit deletion cancelled.")
            return
    except EscapeOperation:
        print_confirmation("Habit deletion cancelled.", False)
        return

    # Delete habit
    try:
        habit.delete()
        print_confirmation(f"Habit '{habit.habit_name}' deleted.")

    # Catching unspecific exceptions
    except Exception as e:
        print_error(f"Error deleting habit: {e}")


def view_analytics() -> None:
    """Flow for viewing analytics (shortcut: a)."""
    print("\n--- Habit Analytics ---\n")

    # Check if there are any habits to view analytics for
    try:
        habit_dict = get_habit_for_action(["analytics"])
        if not habit_dict:
            print_error("No habits available for analytics.")
            return

    # Catching invalid input (e.g., user enters a non-numeric value)
    except ValueError:
        print_error("Invalid input. Please enter a number from the list to select a habit.")
        return

    # Catching escape logics (ESC/CTRL+C)
    except EscapeOperation:
        print_confirmation("Habit analysis cancelled.", False)
        return

    # Catching unspecific exceptions
    except Exception as e:
        print_error(f"Error: {e}")
        return

    # If all checks pass, continue with habit analytics
    # Load habit from database using habit_id
    try:
        habit = Habit.from_db(habit_dict["habit_id"])
    except Exception as e:
        print_error(f"Could not load habit from database: {e}")
        return

    # Calculate and display analytics
    try:
        current_streak = habit.calculate_current_streak()
        longest_streak = habit.calculate_longest_streak()
        completion_rate = habit.complete_rate()
        on_time_rate = habit.finished_ontime_rate()
        print(f"\n--- Analytics: {habit.habit_name} ---\n")
        print(f"  Current streak:    {current_streak} days")
        print(f"  Longest streak:    {longest_streak} days")
        print(f"  Completion rate:   {completion_rate*100:.1f}%")
        print(f"  On-time rate:      {on_time_rate*100:.1f}%")

        print("\nPress Enter to continue...")
        input()

    # Catching unspecific exceptions
    except Exception as e:
        print_error(f"Error calculating analytics: {e}")


def view_history() -> None:
    """Flow for viewing history (shortcut: h)."""
    print("\n--- Habit History ---\n")

    # Check if there are any habits to view history for
    try:
        habit_dict = get_habit_for_action(["history"])
        if not habit_dict:
            print_error("No habits available for history.")
            return

    # Catching invalid input (e.g., user enters a non-numeric value)
    except ValueError:
        print_error("Invalid input. Please enter a number from the list to select a habit.")
        return

    # Catching escape logics (ESC/CTRL+C)
    except EscapeOperation:
        print_confirmation("Habit history cancelled.", False)
        return

    # Catching unspecific exceptions
    except Exception as e:
        print_error(f"Error: {e}")
        return

    # If all checks pass, continue with habit history
    # Load habit from database using habit_id
    try:
        habit = Habit.from_db(habit_dict["habit_id"])
    except Exception as e:
        print_error(f"Could not load habit from database: {e}")
        return

    # Display habit history
    try:
        print(f"\n--- History: {habit.habit_name} ---\n")

        for item in habit.get_habit_history():
            print(item)

        print("\nPress Enter to continue...")
        input()

    # Catching unspecific exceptions
    except Exception as e:
        print_error(f"Error loading history: {e}")
