# In this file contains all functions that are required to set up the overview screen
# This includes functions for the following purposes
# - collect necessary information
# - render information
# - render shortcuts

# Import datetime for datetime handling / BUILT-IN

# Import repository modules for data access / USER-DEFINED
from source.repository.repository_modules import HabitRepository, TaskRepository
from source.ui.helpers import *

#========== COLLECT INFORMATION ==========

def get_active_tasks() -> list[dict]:
    """
        Retrieves all active tasks from the database.

        Returns a list of all tasks in dictionary format, including the computed due_date category.
    """

    task_repo = TaskRepository()
    habit_repo = HabitRepository()
    all_tasks = task_repo.browse_all()
    all_habits = habit_repo.browse_all()

    active_habit_ids = {habit["habit_id"] for habit in all_habits if habit["status"] == "Active"}

    displayed_tasks = []
    for task in all_tasks:
        displayed_task = {}
        if task["habit_id"] in active_habit_ids:

            due_date = task["due_date"]

            label, category = format_relative_date(due_date)

            displayed_task["habit_name"] = task["habit_name"]
            displayed_task["habit_id"] = task["habit_id"]
            displayed_task["due_date"] = due_date
            displayed_task["label"] = label
            displayed_task["category"] = category

            displayed_tasks.append(displayed_task)

    return displayed_tasks

def get_paused_habits() -> list[dict]:
    """
        Retrieves all paused habits from the database.

        Returns a list of all paused habits in dictionary format. Not within tasks because paused habits have no active task.
    """

    habit_repo = HabitRepository()
    all_habits = habit_repo.browse_all()

    paused_habits = []
    for habit in all_habits:
        if habit["status"] == "Paused":
            paused_habit = {}

            paused_habit["habit_name"] = habit["habit_name"]
            paused_habit["habit_id"] = habit["habit_id"]
            paused_habit["period"] = habit["period"]
            paused_habit["start_date"] = habit["start_date"]
            paused_habit["status"] = habit["status"]

            paused_habits.append(paused_habit)

    return paused_habits

def get_active_habits() -> list[dict]:
    """
        Retrieves all active habits from the database.

        Returns a list of all active habits in dictionary format.
    """

    habit_repo = HabitRepository()
    all_habits = habit_repo.browse_all()

    active_habits = []
    for habit in all_habits:
        if habit["status"] == "Active":
            active_habit = {}

            active_habit["habit_name"] = habit["habit_name"]
            active_habit["habit_id"] = habit["habit_id"]
            active_habit["period"] = habit["period"]
            active_habit["start_date"] = habit["start_date"]
            active_habit["status"] = habit["status"]

            active_habits.append(active_habit)

    return active_habits

def categorize_tasks(tasks: list[dict]) -> dict:
    """
    Groups tasks by their category (overdue, today, this_week, upcoming).

    Returns a dict with keys: 'overdue', 'today', 'this_week', 'upcoming'
    Each value is a list of tasks belonging to that category.
    """
    categories = {
        "overdue": [],
        "today": [],
        "this_week": [],
        "upcoming": [],
    }

    for task in tasks:
        category = task.get("category")
        if category in categories:
            categories[category].append(task)

    return categories

#========== RENDER INFORMATION ==========

def render_overview() -> None:
    """
    Main function to render the complete Task Overview screen.

    Fetches all active tasks and paused habits, categorizes them, and displays them.
    """
    # Fetch data
    active_tasks = get_active_tasks()
    paused_habits = get_paused_habits()
    categorized = categorize_tasks(active_tasks)

    # Render header
    print_header("TASK OVERVIEW")

    # Define sections: (title, tasks)
    task_sections = [
        ("OVERDUE", categorized["overdue"]),
        ("TODAY", categorized["today"]),
        ("THIS WEEK", categorized["this_week"]),
        ("UPCOMING", categorized["upcoming"])]

    # Render active task sections
    for title, tasks in task_sections:
        # if no items in category
        if not tasks:
            continue  # Skip empty sections

        # else - if items in category exist
        print(f"\n{title}")
        for index, task in enumerate(tasks, 1):
            name = task["habit_name"]
            label = task["label"]
            print(f"  [{index}] {name:<30} — {label}")

    # Render paused section (different layout)
    if paused_habits:
        print("\nPAUSED")
        for index, habit in enumerate(paused_habits, 1):
            name = habit["habit_name"]
            label = habit["start_date"]
            print(f"  [{index}] {name:<30}")

    # Render shortcut legend
    render_shortcut_legend()

def get_habit_for_action(actions: list[str]) -> dict | None:
    """
    Presents a numbered list of relevant habits and returns a selection.

    Args:
        actions: List of action types ('complete', 'skip', 'edit', etc.)
                 Determines which habits to show (active/paused/all)

    Returns:
        Selected habit dict, or None if canceled/invalid
    """
    # Determine which habits are relevant for this action
    if "complete" in actions or "skip" in actions:
        # Only active tasks
        items = get_active_tasks()
    elif actions == ["reactivate"]:
        # Only paused habits
        items = get_paused_habits()
    elif actions == ["pause"]:
        # Only paused habits
        items = get_active_habits()
    else:
        # All habits for edit/delete/analytics/history
        habit_repo = HabitRepository()
        items = habit_repo.browse_all()

    if not items:
        print("No habits available for this action.")
        return None

    # Display numbered list
    print("\nAvailable Habits:")
    for index, item in enumerate(items, 1):
        name = item["habit_name"]

        # Add status/label info
        additional_info = ""
        # if there is a category, use that, else use status
        if item.get("category"):
            additional_info = f" ({item['category']})"
        elif item.get("status"):
            additional_info = f" ({item['status'].lower()})"

        print(f"  [{index}] {name}{additional_info}")

    # Get selection
    user_selection = prompt_input("\nEnter habit number", True)
    try:
        index = int(user_selection) - 1
        # Check if index is within bounds
        if 0 <= index < len(items):
            return items[index]
        print("Error: Invalid selection.")
        return None

    except KeyboardInterrupt:
        print()
        raise EscapeOperation()

    except Exception:
        raise

#========== RENDER SHORTCUTS ==========

def render_shortcut_legend() -> None:
    """Prints the shortcut legend at the bottom of the overview screen."""
    print()
    print_separator("-")
    print("  [n] New habit   [c] Complete   [s] Skip")
    print("  [e] Edit        [d] Delete      [p] Pause")
    print("  [r] Reactivate  [a] Analytics   [h] History")
    print("  [q] Quit")
    print_separator("-")


