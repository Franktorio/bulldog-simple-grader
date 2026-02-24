# src/db/grader_db/schema.py
# Schema definition for the grader database

DB_FILE_NAME = "grader.db"

SCHEMA = {
    "students": """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            hash_password TEXT NOT NULL
        )
    """,

    "instructors": """
        CREATE TABLE IF NOT EXISTS instructors (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            hash_password TEXT NOT NULL
        )
    """,

    "login_tokens": """
        CREATE TABLE IF NOT EXISTS login_tokens (
            token TEXT PRIMARY KEY,
            student_id INTEGER,
            instructor_id INTEGER,
            expiration_timestamp INTEGER NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(instructor_id) REFERENCES instructors(id)
        )
    """, # A token can either be for a student or an instructor, so one of the two foreign keys will be NULL.

    "assignments": """
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            directory_name TEXT NOT NULL,
            slugs TEXT NOT NULL,
            min_completed INTEGER NOT NULL,
            due_date_timestamp INTEGER,
            is_active INTEGER NOT NULL DEFAULT 1
        )
    """,
    # Slugs is a stringified list of string slugs associated with the assignment, for example:
    # Data assignment might have todolist.py, organizer.py, summary.py as slugs (three parts to complete)
    # So min_completed could allow for only 1 of the three slugs to be completed to pass the assignment
    # The grader will check each slug and as soon as min_completed is reached, the assignment is marked complete.

    "slugs": """
        CREATE TABLE IF NOT EXISTS slugs (
            name TEXT PRIMARY KEY,
            assignment_id INTEGER NOT NULL,
            FOREIGN KEY(assignment_id) REFERENCES assignments(id)
        )
    """,

    "submissions": """
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            assignment_id INTEGER NOT NULL,
            slug TEXT NOT NULL,
            submission_timestamp INTEGER NOT NULL,
            submitted_code TEXT NOT NULL,
            grader_output TEXT NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(assignment_id) REFERENCES assignments(id)
        )
    """,
    # Slug is a reference to a specific part of an assignment that needs to be completed.


    "slug_completions": """
        CREATE TABLE IF NOT EXISTS slug_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            assignment_id INTEGER NOT NULL,
            slug TEXT NOT NULL,
            submission_id INTEGER NOT NULL,
            completion_timestamp INTEGER NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(assignment_id) REFERENCES assignments(id),
            FOREIGN KEY(submission_id) REFERENCES submissions(id),
            UNIQUE(student_id, assignment_id, slug)
        )
    """,

    # Table to store a high-level record of full assignment completions, not just individual slugs.
    "full_completions": """
        CREATE TABLE IF NOT EXISTS full_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slugs_completed TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            assignment_id INTEGER NOT NULL,
            submission_ids TEXT NOT NULL,
            completion_timestamp INTEGER NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(assignment_id) REFERENCES assignments(id)
        )
    """
}