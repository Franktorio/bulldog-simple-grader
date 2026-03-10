# main.py
# Entry point for the application

# Import logging imediately to override print function
import src.log_module  as logs
logs.initialize_logging()

PRINT_PREFIX = "MAIN"
    
from src.db.connections import init_databases, migrate_db, clear_databases
from src.db.backups import init_backup_manager
from src.frontend.api.app import start_api_server
from src.db.app_context import create_app_context
from src.db.grader_db import add_student
from src.db.grader_db.instructors import add_instructor

import os

os.makedirs("submissions", exist_ok=True) # Ensure submissions directory exists for storing student code files

def main_loop():
    while True:
        user_input = input()
        print(f"[INFO] [{PRINT_PREFIX}] Received input: {user_input}")
        check_input(user_input)


def check_input(inpt: str):
    command = inpt.split()[0].lower()
    arguments = inpt.split()[1:]

    match command:
        case "exit":
            print(f"[INFO] [{PRINT_PREFIX}] Exiting application...")
            exit(0)

        case "logs":
            if not arguments:
                print(f"[ERROR] [{PRINT_PREFIX}] 'logs' command requires an argument: 'show' or 'rotate'")
                return
            
            subcommand = arguments[0].lower()
            match subcommand:
                case "clear":
                    logs.clear_logs()

        case "data":
            if not arguments:
                print(f"[ERROR] [{PRINT_PREFIX}] 'data' command requires an argument: 'migrate', 'clear', 'seed'")
                return
            
            subcommand = arguments[0].lower()
            match subcommand:
                case "migrate":
                    db_file_name = arguments[1] if len(arguments) > 1 else None
                    if not db_file_name:
                        print(f"[ERROR] [{PRINT_PREFIX}] 'data migrate' command requires the database file name as an argument")
                        return
                    try:
                        migrate_db(db_file_name)
                    except ValueError as e:
                        print(f"[ERROR] [{PRINT_PREFIX}] Migration failed: {e}")

                case "clear":
                    try:
                        print(f"[WARNING] [{PRINT_PREFIX}] Clearing databases will delete all data. This action cannot be undone.")
                        while True:
                            confirmation = input(f"[WARNING] [{PRINT_PREFIX}] Are you sure you want to clear all databases? Type 'yes' to confirm: ")
                            if confirmation.lower() == "yes":
                                break
                            else:
                                print(f"[INFO] [{PRINT_PREFIX}] Clear databases action cancelled.")
                                return
                        clear_databases()
                    except Exception as e:
                        print(f"[ERROR] [{PRINT_PREFIX}] Failed to clear databases: {e}")
                
        case "add":
            subcommand = arguments[0].lower() if arguments else None
            match subcommand:
                case "student":
                    if len(arguments) < 4:
                        print(f"[ERROR] [{PRINT_PREFIX}] 'add student' command requires 3 arguments: id, name and password")
                        return
                    student_id = arguments[1]
                    student_name = arguments[2]
                    student_password = arguments[3]
                    add_student(student_id, student_name, student_password)

                case "instructor":
                    if len(arguments) < 4:
                        print(f"[ERROR] [{PRINT_PREFIX}] 'add instructor' command requires 3 arguments: id, name and password")
                        return
                    instructor_id = arguments[1]
                    instructor_name = arguments[2]
                    instructor_password = arguments[3]
                    add_instructor(instructor_id, instructor_name, instructor_password)

if __name__ == "__main__":

    # Create application context
    create_app_context()
    print(f"[INFO] [{PRINT_PREFIX}] Application context created successfully.")

    # Initialize databases
    init_databases()
    print(f"[INFO] [{PRINT_PREFIX}] Databases initialized successfully.")

    # Start backup manager
    init_backup_manager()
    print(f"[INFO] [{PRINT_PREFIX}] Backup manager started successfully.")

    # Start API server
    start_api_server()