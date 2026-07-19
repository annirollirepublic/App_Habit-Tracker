# Import overview rendering and shortcut reading / USER-DEFINED
from source.ui.overview import render_overview
from source.ui.helpers import get_user_shortcut_overview

# Import all actions / USER-DEFINED
from source.ui.actions import *

# Import OS for clearing the terminal / BUILT-IN
import os

# TODO : The must be a way to exit selected operations

# Shortcut to action mapping
SHORTCUT_MAP = {
    "n": ("New Habit", create_new_habit),
    "c": ("Complete Task", complete_task),
    "s": ("Skip Task", skip_task),
    "e": ("Edit Habit", edit_habit),
    "d": ("Delete Habit", delete_habit),
    "p": ("Pause Habit", pause_habit),
    "r": ("Reactivate Habit", reactivate_habit),
    "a": ("View Analytics", view_analytics),
    "q": ("Quit", None),
}


def clear_screen() -> None:
    """Clears the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def run() -> None:
    """Main application loop."""
    print("Welcome to Habit Tracker!\n")

    while True:
        clear_screen()
        render_overview()

        shortcut = get_user_shortcut_overview()

        # Quit
        if shortcut == "q":
            print("\nGoodbye!\n")
            break

        # Dispatch to action
        label, action_func = SHORTCUT_MAP.get(shortcut, ("Unknown", None))

        if action_func:
            clear_screen()
            action_func()
        else:
            print("Invalid shortcut.")


if __name__ == "__main__":
    run()