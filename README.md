## Application Name
Habit Tracker

## Description
This is a terminal-based habit tracking application to create and monitor routines.
It was developed as part of a project for the module **Object Oriented and Functional Programming with Python (DLBDSOOFPP01)** at **International University (IU)**

## Use Cases
- **Create New Habits**: Users can create habits with user-defined naming, period and start date.
- **Manage Habits**: After habit creation, users can still tailor them to suit their needs > edit information, pause and reactivate habits
- **Task Checkoff**: Users can finish a task either by completing or skipping it, automatic next task generation
- **Analytics**: Users can view streaks, completion rates, and on-time performance
- **History**: Users can access all past records with information on the completion status and whether it was overdue

## Installation 
Clone repository
```
git clone https://github.com/yourusername/habit-tracker.git
cd habit-tracker
```
Create virtual environment (recommended)
```
python -m venv venv

source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```
Install dependencies
```
pip install -r requirements.txt
```

## Usage
Navigate to the downloaded folder in your terminal and run the application with
```
python -m source.ui.app
```
The start menu displays the status of all open tasks and paused habits. This view is the starting point for all operations.
```
==================================================
                  TASK OVERVIEW                   
==================================================

OVERDUE
  [1] Read Book                      — 1 day overdue

TODAY
  [1] Morning Run                    — today

THIS WEEK
  [1] Weekly Review                  — in 1 day

UPCOMING
  [1] Bi-weekly Gym                  — in 10 days

PAUSED
  [1] Monthly Budget                 — original start_date 2026-01-01
```
Use displayed shortcuts to fulfill operations within the application. Use ```shortcut + Enter```
```
[n] New habit      # Create a new habit
[c] Complete       # Check-off tasks that user has successfully completed (streak increases)
[s] Skip           # Check-off tasks that user has wants to skip once (breaks streak)
[e] Edit           # Edit habit information: name, start_date, period
[d] Delete         # Delete habit, as well as all corresponding tasks and records
[p] Pause          # Temporarily disable habits without losing history
[r] Reactivate     # Ractivate habits that have been paused
[a] Analytics      # Show analytics - streaks, completion rates, and on-time performance
[h] History        # Access all past records with information on the completion status and whether it was overdue
[q] Quit           # Quit application
```
The habits for the operation, will be filtered in accordance to the selected use case. 
To select a habit, the user also applies the shortcut navigation.
```
====================== EXAMPLE ==========================

--- Edit Habit ---

Available Habits:
  [1] Morning Run (active)
  [2] Weekly Review (active)
  [3] Bi-weekly Gym (active)
  [4] Monthly Budget (paused)
  [5] Read Book (active)

Enter habit number: 
```

The user can cancel any operation at any point by pressing ```ESC``` or ```Ctrl + C```.
By cancelling the operation, the user will be re-directed to the main menu.

## Structure
```
App_Habit-Tracker/
├── source/
│   ├── app_logic/        # Business logic (Habit, TaskManager, RecordAnalyzer)
│   ├── helpers/          # Utilities (enums, exceptions, datetime helpers)
│   ├── repository/       # Repository implementations (database access)
│   ├── ui/               # Terminal user interface
│   └── config.py         # Configuration (logging, database path)
├── tests/
│   ├── unittests/        # Unit tests with mocked dependencies
│   └── integration/      # Integration tests with real database
├── README.md
├── requirements.txt
├── habit-tracker.log     # Log file for debugging
└── habit-tracker.db      # SQLite database (auto-created on first run)
```

## Tech Stack
- **Language**: Python 3.11+
- **Database**: SQLite (local file persistence)
- **Testing**: pytest (unit + integration tests)
- **Architecture**: Repository Pattern, Layered Architecture, Dependency Injection

## Requirements
__to be added__
