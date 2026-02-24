# src/db/grader_db/submissions.py
# Database operations related to submissions

from . import connect_grader_db, connect_grader_db_ro
import json

PRINT_PREFIX = "DB - SUBMISSIONS"

class Submission:
    """Represents a submission in the database. Grader output is stored as a JSON string in the database but represented as a dictionary in this class."""
    
    def __init__(self, id: int, student_id: int, assignment_id: int, slug: str, submission_timestamp: int, submitted_code: str, grader_output: str):
        self.id = id
        self.student_id = student_id
        self.assignment_id = assignment_id
        self.slug = slug
        self.submission_timestamp = submission_timestamp
        self.submitted_code = submitted_code
        self.grader_output = json.loads(grader_output)

    def __str__(self):
        output_preview = str(self.grader_output)[:50] if self.grader_output else ''
        code_preview = str(self.submitted_code)[:30] if self.submitted_code else ''
        return f"Submission(id={self.id}, student_id={self.student_id}, assignment_id={self.assignment_id}, slug='{self.slug}', submission_timestamp={self.submission_timestamp}, submitted_code='{code_preview}...', grader_output='{output_preview}...')"
    
    def change_student_id(self, new_student_id: int):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify submission without a valid ID.")
            return
        modify_submission(self.id, student_id=new_student_id)
        self.refresh_from_db()

    def change_assignment_id(self, new_assignment_id: int):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify submission without a valid ID.")
            return
        modify_submission(self.id, assignment_id=new_assignment_id)
        self.refresh_from_db()

    def change_slug(self, new_slug: str):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify submission without a valid ID.")
            return
        modify_submission(self.id, slug=new_slug)
        self.refresh_from_db()

    def change_submission_timestamp(self, new_submission_timestamp: int):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify submission without a valid ID.")
            return
        modify_submission(self.id, submission_timestamp=new_submission_timestamp)
        self.refresh_from_db()

    def change_grader_output(self, new_grader_output: dict):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify submission without a valid ID.")
            return
        modify_submission(self.id, grader_output=new_grader_output)
        self.refresh_from_db()

    def refresh_from_db(self):
        """Reload this submission's data from the database."""
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot refresh submission without a valid ID.")
            return
        refreshed = get_submission(self.id)
        if refreshed:
            self.student_id = refreshed.student_id
            self.assignment_id = refreshed.assignment_id
            self.slug = refreshed.slug
            self.submission_timestamp = refreshed.submission_timestamp
            self.submitted_code = refreshed.submitted_code
            self.grader_output = refreshed.grader_output
        else:
            print(f"[WARNING] [{PRINT_PREFIX}] Submission with ID {self.id} not found in database.")

    def delete(self):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot delete submission without a valid ID.")
            return
        delete_submission(self.id)
        
        # Turn everything into None to prevent accidental use after deletion
        self.id = None
        self.student_id = None
        self.assignment_id = None
        self.slug = None
        self.submission_timestamp = None
        self.submitted_code = None
        self.grader_output = None

def add_submission(student_id: int, assignment_id: int, slug: str, submission_timestamp: int, submitted_code: str, grader_output: dict) -> int:
    """Add a new submission to the database."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO submissions (student_id, assignment_id, slug, submission_timestamp, submitted_code, grader_output) VALUES (?, ?, ?, ?, ?, ?)",
        (student_id, assignment_id, slug, submission_timestamp, submitted_code, json.dumps(grader_output))
    )
    submission_id = cursor.lastrowid
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Added submission for student {student_id}, assignment {assignment_id}, slug '{slug}' with ID {submission_id}")
    return submission_id

def get_submission(submission_id: int) -> Submission | None:
    """Retrieve a submission by ID."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_id, assignment_id, slug, submission_timestamp, submitted_code, grader_output FROM submissions WHERE id = ?",
        (submission_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        print(f"[INFO] [{PRINT_PREFIX}] Retrieved submission with ID {row[0]}")
        return Submission(id=row[0], student_id=row[1], assignment_id=row[2], slug=row[3], submission_timestamp=row[4], submitted_code=row[5], grader_output=row[6])
    return None

def get_submissions_by_student(student_id: int) -> list[Submission]:
    """Retrieve all submissions for a given student."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_id, assignment_id, slug, submission_timestamp, submitted_code, grader_output FROM submissions WHERE student_id = ?",
        (student_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Retrieved {len(rows)} submissions for student {student_id}")
    return [Submission(id=row[0], student_id=row[1], assignment_id=row[2], slug=row[3], submission_timestamp=row[4], submitted_code=row[5], grader_output=row[6]) for row in rows]

def get_submissions_by_assignment(assignment_id: int) -> list[Submission]:
    """Retrieve all submissions for a given assignment."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_id, assignment_id, slug, submission_timestamp, submitted_code, grader_output FROM submissions WHERE assignment_id = ?",
        (assignment_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Retrieved {len(rows)} submissions for assignment {assignment_id}")
    return [Submission(id=row[0], student_id=row[1], assignment_id=row[2], slug=row[3], submission_timestamp=row[4], submitted_code=row[5], grader_output=row[6]) for row in rows]

def modify_submission(submission_id: int, student_id: int | None = None, assignment_id: int | None = None, slug: str | None = None, submission_timestamp: int | None = None, submitted_code: str | None = None, grader_output: dict | None = None) -> bool:
    """Modify an existing submission. Only provided fields will be updated."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    
    fields_to_update = []
    values = []
    
    if student_id is not None:
        fields_to_update.append("student_id = ?")
        values.append(student_id)
    if assignment_id is not None:
        fields_to_update.append("assignment_id = ?")
        values.append(assignment_id)
    if slug is not None:
        fields_to_update.append("slug = ?")
        values.append(slug)
    if submission_timestamp is not None:
        fields_to_update.append("submission_timestamp = ?")
        values.append(submission_timestamp)
    if submitted_code is not None:
        fields_to_update.append("submitted_code = ?")
        values.append(submitted_code)
    if grader_output is not None:
        fields_to_update.append("grader_output = ?")
        values.append(json.dumps(grader_output))
    
    if not fields_to_update:
        print(f"[INFO] [{PRINT_PREFIX}] No fields to update for submission ID {submission_id}")
        return False  # Nothing to update
    
    values.append(submission_id)
    update_query = f"UPDATE submissions SET {', '.join(fields_to_update)} WHERE id = ?"
    
    cursor.execute(update_query, tuple(values))
    conn.commit()
    conn.close()
    
    print(f"[INFO] [{PRINT_PREFIX}] Modified submission with ID {submission_id}")
    return True

def delete_submission(submission_id: int) -> bool:
    """Delete a submission from the database."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM submissions WHERE id = ?",
        (submission_id,)
    )
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Deleted submission with ID {submission_id}")
    return True

def get_submissions_by_student_and_assignment(student_id: int, assignment_id: int) -> list[Submission]:
    """Retrieve all submissions for a given student and assignment."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_id, assignment_id, slug, submission_timestamp, submitted_code, grader_output FROM submissions WHERE student_id = ? AND assignment_id = ?",
        (student_id, assignment_id)
    )
    rows = cursor.fetchall()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Retrieved {len(rows)} submissions for student {student_id} and assignment {assignment_id}")
    return [Submission(id=row[0], student_id=row[1], assignment_id=row[2], slug=row[3], submission_timestamp=row[4], submitted_code=row[5], grader_output=row[6]) for row in rows]

def get_submissions_by_student_and_slug(student_id: int, slug: str) -> list[Submission]:
    """Retrieve submissions for a given student and slug."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_id, assignment_id, slug, submission_timestamp, submitted_code, grader_output FROM submissions WHERE student_id = ? AND slug = ?",
        (student_id, slug)
    )
    rows = cursor.fetchall()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Retrieved {len(rows)} submissions for student {student_id} and slug '{slug}'")
    if rows:
        return [Submission(id=row[0], student_id=row[1], assignment_id=row[2], slug=row[3], submission_timestamp=row[4], submitted_code=row[5], grader_output=row[6]) for row in rows]
    return []