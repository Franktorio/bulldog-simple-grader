# This script handles adding users (students or instructors) to the database.
# It provides a command-line interface for creating new user accounts.

# On home directory of the project, run:
# python -m automations.scripts.add_user instructor <id> <Name> <Password>
# python -m automations.scripts.add_user student <id> <Name> <Password>
# OR
# python3 -m automations.scripts.add_user instructor <id> <Name> <Password>
# python3 -m automations.scripts.add_user student <id> <Name> <Password>

from src.log_module import initialize_logging
initialize_logging() # Initialize logging to capture script output

if __name__ == "__main__": # Main entry point enforcement, ensures the script is run directly and not imported on accident.
    from src.db import connections
    from src.db.grader_db import add_instructor, add_student

    # Get arguments for user type, id, name, and password
    import sys
    if len(sys.argv) < 5:
        print("Usage: python -m automations.scripts.add_user <user_type> <id> <Name> <Password>")
        print("    user_type: 'instructor' or 'student'")
        print("    id: numeric ID for the user")
        print("    Name: display name for the user")
        print("    Password: password for the user")
        print("\nExamples:")
        print("-> python -m automations.scripts.add_user instructor 1001 'Dr. Smith' 'secure123'")
        print("-> python -m automations.scripts.add_user student 2001 'John Doe' 'student123'")
        exit(1)
    
    user_type = sys.argv[1].lower()
    user_id_str = sys.argv[2]
    user_name = sys.argv[3]
    user_password = sys.argv[4]

    # Validate user type
    if user_type not in ['instructor', 'student']:
        print(f"[ERROR] [SCRIPT ADD USER] Invalid user type: '{user_type}'. Must be 'instructor' or 'student'.")
        exit(1)

    # Validate user ID is numeric
    try:
        user_id = int(user_id_str)
    except ValueError:
        print(f"[ERROR] [SCRIPT ADD USER] Invalid user ID: '{user_id_str}'. Must be a numeric value.")
        exit(1)

    # Initialize databases
    connections.init_databases()

    # Add the user
    try:
        if user_type == 'instructor':
            add_instructor(instructor_id=user_id, name=user_name, password=user_password)
            print(f"[INFO] [SCRIPT ADD USER] Instructor '{user_name}' with ID {user_id} added successfully.")
        else:  # student
            add_student(student_id=user_id, name=user_name, password=user_password)
            print(f"[INFO] [SCRIPT ADD USER] Student '{user_name}' with ID {user_id} added successfully.")
        exit(0)
    except Exception as e:
        print(f"[ERROR] [SCRIPT ADD USER] Failed to add {user_type} '{user_name}' with ID {user_id}: {e}")
        exit(1)
