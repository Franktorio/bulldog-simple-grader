# src\logging.py
# Overrides the built-in print function to log messages to a file with timestamps.
# Also implements automatic log rotation at midnight, keeping logs for 7 days. (UTC)

import builtins
import shutil
import os
import datetime
import threading
from typing import Any
from config.config import OPERATING_MODE

DEBUG_ENABLED = OPERATING_MODE == 'development'

LOG_NAME = "app_logs"

PRINT_PREFIX = "LOG MANAGER"

TO_SKIP = [
    "self._context.run(self._callback, *self._args)", # Spammy debug logs that are not useful
    "TypeError: 'NoneType' object is not callable", # Recurring error that clutters logs
    "Traceback (most recent call last):" # Recurring error that spams logs
]

# Reference to the original print function
original_print = builtins.print

os.makedirs("logs", exist_ok=True)
os.makedirs("logs/rotated_logs", exist_ok=True)

# Create and/or open the bot logs file in append mode
bot_logs = open(f"logs/{LOG_NAME}.log", "a")

log_queue: list[str] = [] # Hold messages when logs are closed for rotation

log_lock = threading.Lock()

startup_rotation = False # Will be set to True after application startup, which will trigger log rotation regardless of time

def logging_print(*args: Any, **kwargs: Any) -> None:
    """Custom print function for logging purposes."""
    global DEBUG_ENABLED
    original_print(*args, **kwargs)  # Print to console
    # Skip logging debug messages if debug is disabled
    for arg in args:
        if not DEBUG_ENABLED and "[DEBUG]" in str(arg):
            return
        for skip_str in TO_SKIP:
            if skip_str in str(arg):
                return

    text_output = ""
    for arg in args:
        text_output += str(arg) + " "
    
    bot_log = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {text_output}\n"
    with log_lock:
        bot_logs.write(bot_log)
        bot_logs.flush() # Force write to file
    
def _rotate_log():
    """Rotate the log file by closing the current one and opening a new one."""
    global bot_logs
    bot_logs = open(f"logs/{LOG_NAME}.log", "a")

def auto_rotate_log():
    """
    Automatically rotate the log file at midnight every day.
    
    Stores up to 7 days of logs by renaming old log files.
    1. bot_logs.log -> bot_logs_YYYYMMDD.log
    2. bot_logs_YYYYMMDD.log (7 days old) is deleted
    3. New bot_logs.log is created
    4. bot_logs.log is renamed to bot_logs_YYYYMMDD.log
    5. New bot_logs.log is created
    6. Repeat daily at midnight

    """
    global bot_logs, startup_rotation

    while True:
        now = datetime.datetime.now()
        next_midnight = (now + datetime.timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Wait until midnight
        sleep_duration = (next_midnight - now).total_seconds()
        log_queue.append(f"[INFO] [{PRINT_PREFIX}] Next log rotation scheduled in {sleep_duration} seconds.")
        if startup_rotation:
            threading.Event().wait(sleep_duration)
        else:
            # On first run, rotate immediately after startup
            startup_rotation = True
            log_queue.append(f"[INFO] [{PRINT_PREFIX}] Performing initial log rotation after startup.")
            
        log_queue.append(f"[INFO] [{PRINT_PREFIX}] Rotating log file.")

        # Rotate the log file
        now = datetime.datetime.now()
        with log_lock:
            bot_logs.close()

            date_suffix = now.strftime("%Y-%m-%d")
            
            # Create directory for today's logs
            today_log_dir = f"logs/rotated_logs/{date_suffix}"
            os.makedirs(today_log_dir, exist_ok=True)

            # Add _x+1 if file already exists to avoid overwriting
            file_number = 1 # Start with 1

            base_rotated_log_path = f"{today_log_dir}/{LOG_NAME}_{file_number}.log"
            rotated_log_path = base_rotated_log_path

            while os.path.exists(rotated_log_path):
                file_number += 1
                rotated_log_path = f"{today_log_dir}/{LOG_NAME}_{file_number}.log"

            try:
                os.rename(f"logs/{LOG_NAME}.log", rotated_log_path)
                log_queue.append(f"[INFO] [{PRINT_PREFIX}] Log file rotated to {rotated_log_path}")
            except FileNotFoundError:
                log_queue.append(f"[WARNING] [{PRINT_PREFIX}] No log file to rotate.")
                pass

            # Delete log directories older than 7 days
            for i in range(8, 30): # Tries to delete up to 30 day old logs, but usually only 7 days will exist (incase app was down for a while)
                old_date_suffix = (now - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                old_log_dir = f"logs/rotated_logs/{old_date_suffix}"
                if os.path.exists(old_log_dir):
                    try:
                        shutil.rmtree(old_log_dir)
                        log_queue.append(f"[INFO] [{PRINT_PREFIX}] Deleted old log directory: {old_log_dir}")
                    except Exception as e:
                        log_queue.append(f"[ERROR] [{PRINT_PREFIX}] Failed to delete old log directory {old_log_dir}: {e}")
        
            # Reopen new active log
            _rotate_log()
        for log_msg in log_queue:
            print(log_msg)
        log_queue.clear()
        
        print(f"[INFO] [{PRINT_PREFIX}] Log rotation complete.")
        for _ in range(5):
            print("#"*70)

def initialize_logging():
    # Override the built-in print function (monkey patching)
    builtins.print = logging_print

    # Start the auto log rotation in a separate daemon thread
    log_rotation_thread = threading.Thread(target=auto_rotate_log, daemon=True, name="LogRotationThread")
    log_rotation_thread.start()

def clear_logs():
    """Deletes all the logs in the active log file and rotated logs."""
    global bot_logs
    with log_lock:
        bot_logs.close()
        open(f"logs/{LOG_NAME}.log", "w").close() # Clear active log file
        bot_logs = open(f"logs/{LOG_NAME}.log", "a") # Reopen active log file

    # Clear rotated logs
    import shutil
    rotated_logs_dir = "logs/rotated_logs"
    for item in os.listdir(rotated_logs_dir):
        item_path = os.path.join(rotated_logs_dir, item)
        if os.path.isdir(item_path):
            try:
                shutil.rmtree(item_path)
                print(f"[INFO] [{PRINT_PREFIX}] Deleted rotated log directory: {item_path}")
            except Exception as e:
                print(f"[ERROR] [{PRINT_PREFIX}] Failed to delete rotated log directory {item_path}: {e}")

    for _ in range(5):
        print("#"*70)
    print(f"[WARNING] [{PRINT_PREFIX}] All logs cleared.")