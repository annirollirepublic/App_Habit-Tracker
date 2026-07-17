# Import Logging for Bug Fixing / BUILT-IN
import logging

# Set logging configuration
logging.basicConfig(level=logging.INFO,
                    filename="../habit-tracker.log",
                    filemode="w",
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Set global database
global_db_path = "../habit-tracker-data.db"
