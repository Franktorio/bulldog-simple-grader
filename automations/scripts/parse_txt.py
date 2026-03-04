# This script handles parsing txt files to add multiple users (students or instructors) to the database in bulk.
# It provides a command-line interface for processing txt files containing user information.

# On home directory of the project, run:
# python -m automations.scripts.parse_txt instructor file.txt
# python -m automations.scripts.parse_txt student file.txt
# OR
# python3 -m automations.scripts.parse_txt instructor file.txt
# python3 -m automations.scripts.parse_txt student file.txt

# The file should be placed on the working directory

# Format for txt (one user per line)
# Everything except the last token is the name; the last token is the numeric ID. For example:
# Frank Middlename Lastname 100123

from src.log_module import initialize_logging
initialize_logging()  # Initialize logging to capture script output


if __name__ == "__main__":  # Main entry point enforcement
    from src.db import connections
    from src.db.grader_db import add_instructor, add_student

    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m automations.scripts.parse_txt <user_type> <file>")
        print("    user_type: 'instructor' or 'student'")
        print("    file: path to txt file, one user per line (Name... ID)")
        print("\nExamples:")
        print("-> python -m automations.scripts.parse_txt instructor instructors.txt")
        print("-> python -m automations.scripts.parse_txt student students.txt")
        exit(1)

    user_type = sys.argv[1].lower()
    file_path = sys.argv[2]

    # Validate user type
    if user_type not in ['instructor', 'student']:
        print(f"[ERROR] [SCRIPT PARSE TXT] Invalid user type: '{user_type}'. Must be 'instructor' or 'student'.")
        exit(1)

    # Read and parse the file
    try:
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[ERROR] [SCRIPT PARSE TXT] File not found: '{file_path}'.")
        exit(1)
    except Exception as e:
        print(f"[ERROR] [SCRIPT PARSE TXT] Could not read file '{file_path}': {e}")
        exit(1)

    if not lines:
        print(f"[ERROR] [SCRIPT PARSE TXT] File '{file_path}' is empty.")
        exit(1)

    # Initialize databases
    connections.init_databases()

    added = 0
    failed = 0

    for line_number, line in enumerate(lines, start=1):
        student_line = line.split()

        if len(student_line) < 2:
            print(f"[WARN] [SCRIPT PARSE TXT] Line {line_number} skipped (expected 'Name... ID'): '{line}'")
            failed += 1
            continue

        user_id_str = student_line[-1]
        user_name = ' '.join(student_line[:-1])

        try:
            user_id = int(user_id_str)
        except ValueError:
            print(f"[WARN] [SCRIPT PARSE TXT] Line {line_number} skipped because ID '{user_id_str}' is not numeric: '{line}'")
            failed += 1
            continue

        try:
            if user_type == 'instructor':
                add_instructor(instructor_id=user_id, name=user_name, password=str(user_id))
                print(f"[INFO] [SCRIPT PARSE TXT] Added instructor '{user_name}' (ID {user_id}).")
            else:
                add_student(student_id=user_id, name=user_name, password=str(user_id))
                print(f"[INFO] [SCRIPT PARSE TXT] Added student '{user_name}' (ID {user_id}).")
            added += 1
        except Exception as e:
            print(f"[ERROR] [SCRIPT PARSE TXT] Failed to add {user_type} '{user_name}' (ID {user_id}) on line {line_number}: {e}")
            failed += 1

    print(f"\n[INFO] [SCRIPT PARSE TXT] Done. {added} added, {failed} failed.")
    exit(0 if failed == 0 else 1)
