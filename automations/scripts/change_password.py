# This script handles changing passwords for users (students or instructors) in the database.
# It provides a command-line interface for changing passwords for existing user accounts.

# On home directory of the project, run:
# python -m automations.scripts.change_password instructor <id> <NewPassword>
# python -m automations.scripts.change_password student <id> <NewPassword>
# OR
# python3 -m automations.scripts.change_password instructor <id> <NewPassword>
# python3 -m automations.scripts.change_password student <id> <NewPassword>

from src.log_module import initialize_logging
initialize_logging() # Initialize logging to capture script output

if __name__ == "__main__": # Main entry point enforcement, ensures the script is run directly and not imported on accident.
    from src.db import connections
    from src.db.grader_db import change_instructor_password, change_student_password

    # Get arguments for user type, id, and new password
    import sys
    if len(sys.argv) < 4:
        print("Usage: python -m automations.scripts.change_password <user_type> <id> <NewPassword>")
        print("    user_type: 'instructor' or 'student'")
        print("    id: numeric ID for the user")
        print("    NewPassword: new password for the user")
        print("\nExamples:")
        print("-> python -m automations.scripts.change_password instructor 1001 'newsecure123'")
        print("-> python -m automations.scripts.change_password student 2001 'newstudent123'")
        exit(1)
    
    user_type = sys.argv[1].lower()
    user_id_str = sys.argv[2]
    new_password = sys.argv[3]

    # Validate user type
    if user_type not in ['instructor', 'student']:
        print(f"[ERROR] [SCRIPT CHANGE PASSWORD] Invalid user type: '{user_type}'. Must be 'instructor' or 'student'.")
        exit(1)

    # Validate user ID is numeric
    try:
        user_id = int(user_id_str)
    except ValueError:
        print(f"[ERROR] [SCRIPT CHANGE PASSWORD] Invalid user ID: '{user_id_str}'. Must be a numeric value.")
        exit(1)

    # Initialize databases
    connections.init_databases()

    # Change the password
    try:
        if user_type == 'instructor':
            change_instructor_password(instructor_id=user_id, new_password=new_password, from_script=True)
            print(f"[INFO] [SCRIPT CHANGE PASSWORD] Password for instructor with ID {user_id} changed successfully.")
        else:  # student
            change_student_password(student_id=user_id, new_password=new_password, from_script=True)
            print(f"[INFO] [SCRIPT CHANGE PASSWORD] Password for student with ID {user_id} changed successfully.")
        exit(0)
    except Exception as e:
        print(f"[ERROR] [SCRIPT CHANGE PASSWORD] Failed to change password for {user_type} with ID {user_id}: {e}")
        exit(1)