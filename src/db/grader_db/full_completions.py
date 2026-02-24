# src/db/grader_db/full_completions.py
# Database operations related to full completions

import time
import json
from . import connect_grader_db, connect_grader_db_ro

PRINT_PREFIX = "DB - FULL COMPLETIONS"

class FullCompletion:
    """Represents a full completion in the database."""
    
    def __init__(self, id: int, student_id: int, assignment_id: int, slugs_completed: list[str], submission_ids: list[int], completion_timestamp: int):
        self.id = id
        self.student_id = student_id
        self.assignment_id = assignment_id
        self.slugs_completed = slugs_completed
        self.submission_ids = submission_ids
        self.completion_timestamp = completion_timestamp

    def __str__(self):
        return f"FullCompletion(id={self.id}, student_id={self.student_id}, assignment_id={self.assignment_id}, slugs_completed={self.slugs_completed}, submission_ids={self.submission_ids}, completion_timestamp={self.completion_timestamp})"
    
    def change_slugs_completed(self, new_slugs_completed: list[str]):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify completion without a valid ID.")
            return
        modify_completion(self.id, slugs_completed=new_slugs_completed)
        self.refresh_from_db()

    def change_submission_ids(self, new_submission_ids: list[int]):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify completion without a valid ID.")
            return
        modify_completion(self.id, submission_ids=new_submission_ids)
        self.refresh_from_db()

    def change_completion_timestamp(self, new_completion_timestamp: int):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify completion without a valid ID.")
            return
        modify_completion(self.id, completion_timestamp=new_completion_timestamp)
        self.refresh_from_db()

    def refresh_from_db(self):
        """Reload this completion's data from the database."""
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot refresh completion without a valid ID.")
            return
        refreshed = get_completion(self.id)
        if refreshed:
            self.student_id = refreshed.student_id
            self.assignment_id = refreshed.assignment_id
            self.slugs_completed = refreshed.slugs_completed
            self.submission_ids = refreshed.submission_ids
            self.completion_timestamp = refreshed.completion_timestamp
        else:
            print(f"[WARNING] [{PRINT_PREFIX}] Completion with ID {self.id} not found in database.")

    def delete(self):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot delete completion without a valid ID.")
            return
        delete_completion(self.id)
        
        # Turn everything into None to prevent accidental use after deletion
        self.id = None
        self.student_id = None
        self.assignment_id = None
        self.slugs_completed = None
        self.submission_ids = None
        self.completion_timestamp = None

def create_or_update_completion(student_id: int, assignment_id: int, slugs_completed: list[str], submission_ids: list[int]) -> FullCompletion:
    """
    Create a new completion record or update existing one.
    A student can only have one completion per assignment.
    If a completion exists, it will be updated; otherwise, a new one will be created.
    """
    # Check if completion already exists
    existing = get_student_completion_for_assignment(student_id, assignment_id)
    
    if existing:
        # Update existing completion
        modify_completion(
            existing.id,
            slugs_completed=slugs_completed,
            submission_ids=submission_ids,
            completion_timestamp=int(time.time())
        )
        print(f"[INFO] [{PRINT_PREFIX}] Updated completion for student {student_id}, assignment {assignment_id}")
        return get_completion(existing.id)
    else:
        # Create new completion
        conn = connect_grader_db()
        cursor = conn.cursor()
        timestamp = int(time.time())
        cursor.execute("""
            INSERT INTO full_completions (student_id, assignment_id, slugs_completed, submission_ids, completion_timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id, assignment_id, json.dumps(slugs_completed), json.dumps(submission_ids), timestamp))
        conn.commit()
        completion_id = cursor.lastrowid
        conn.close()
        print(f"[INFO] [{PRINT_PREFIX}] Created completion for student {student_id}, assignment {assignment_id} with ID {completion_id}")
        return FullCompletion(id=completion_id, student_id=student_id, assignment_id=assignment_id, slugs_completed=slugs_completed, submission_ids=submission_ids, completion_timestamp=timestamp)

def get_completion(completion_id: int) -> FullCompletion | None:
    """Retrieve a completion record from the database by its ID."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_id, assignment_id, slugs_completed, submission_ids, completion_timestamp FROM full_completions WHERE id = ?",
        (completion_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        print(f"[INFO] [{PRINT_PREFIX}] Retrieved completion with ID {row[0]}")
        return FullCompletion(id=row[0], student_id=row[1], assignment_id=row[2], slugs_completed=json.loads(row[3]), submission_ids=json.loads(row[4]), completion_timestamp=row[5])
    return None
    
def get_completions_by_student(student_id: int) -> list[FullCompletion]:
    """Retrieve all completion records for a given student."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_id, assignment_id, slugs_completed, submission_ids, completion_timestamp FROM full_completions WHERE student_id = ?",
        (student_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Retrieved {len(rows)} completions for student {student_id}")
    return [FullCompletion(id=row[0], student_id=row[1], assignment_id=row[2], slugs_completed=json.loads(row[3]), submission_ids=json.loads(row[4]), completion_timestamp=row[5]) for row in rows]

def get_completions_by_assignment(assignment_id: int) -> list[FullCompletion]:
    """Retrieve all completion records for a given assignment."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_id, assignment_id, slugs_completed, submission_ids, completion_timestamp FROM full_completions WHERE assignment_id = ?",
        (assignment_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Retrieved {len(rows)} completions for assignment {assignment_id}")
    return [FullCompletion(id=row[0], student_id=row[1], assignment_id=row[2], slugs_completed=json.loads(row[3]), submission_ids=json.loads(row[4]), completion_timestamp=row[5]) for row in rows]

def get_student_completion_for_assignment(student_id: int, assignment_id: int) -> FullCompletion | None:
    """
    Retrieve the completion record for a given student and assignment.
    Returns None if no completion exists (since each student can only have one completion per assignment).
    """
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_id, assignment_id, slugs_completed, submission_ids, completion_timestamp FROM full_completions WHERE student_id = ? AND assignment_id = ?",
        (student_id, assignment_id)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        print(f"[INFO] [{PRINT_PREFIX}] Retrieved completion for student {student_id}, assignment {assignment_id}")
        return FullCompletion(id=row[0], student_id=row[1], assignment_id=row[2], slugs_completed=json.loads(row[3]), submission_ids=json.loads(row[4]), completion_timestamp=row[5])
    return None

def modify_completion(completion_id: int, slugs_completed: list[str] | None = None, submission_ids: list[int] | None = None, completion_timestamp: int | None = None) -> bool:
    """Modify an existing completion. Only provided fields will be updated."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    
    fields_to_update = []
    values = []
    
    if slugs_completed is not None:
        fields_to_update.append("slugs_completed = ?")
        values.append(json.dumps(slugs_completed))
    if submission_ids is not None:
        fields_to_update.append("submission_ids = ?")
        values.append(json.dumps(submission_ids))
    if completion_timestamp is not None:
        fields_to_update.append("completion_timestamp = ?")
        values.append(completion_timestamp)
    
    if not fields_to_update:
        print(f"[INFO] [{PRINT_PREFIX}] No fields to update for completion ID {completion_id}")
        return False  # Nothing to update
    
    values.append(completion_id)
    update_query = f"UPDATE full_completions SET {', '.join(fields_to_update)} WHERE id = ?"
    
    cursor.execute(update_query, tuple(values))
    conn.commit()
    conn.close()
    
    print(f"[INFO] [{PRINT_PREFIX}] Modified completion with ID {completion_id}")
    return True

def delete_completion(completion_id: int) -> bool:
    """Delete a completion from the database."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM full_completions WHERE id = ?",
        (completion_id,)
    )
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Deleted completion with ID {completion_id}")
    return True