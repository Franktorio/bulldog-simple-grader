# src/db/grader_db/completions.py
# Database operations related to completions

from . import connect_grader_db, connect_grader_db_ro

PRINT_PREFIX = "DB - COMPLETIONS"

class Completion:
    """Represents a completion in the database."""
    
    def __init__(self, id: int, student_id: int, assignment_id: int, submission_id: int, completion_timestamp: int):
        self.id = id
        self.student_id = student_id
        self.assignment_id = assignment_id
        self.submission_id = submission_id
        self.completion_timestamp = completion_timestamp

    def __str__(self):
        return f"Completion(id={self.id}, student_id={self.student_id}, assignment_id={self.assignment_id}, submission_id={self.submission_id}, completion_timestamp={self.completion_timestamp})"
    
    def change_student_id(self, new_student_id: int):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify completion without a valid ID.")
            return
        modify_completion(self.id, student_id=new_student_id)
        self.refresh_from_db()

    def change_assignment_id(self, new_assignment_id: int):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify completion without a valid ID.")
            return
        modify_completion(self.id, assignment_id=new_assignment_id)
        self.refresh_from_db()

    def change_submission_id(self, new_submission_id: int):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify completion without a valid ID.")
            return
        modify_completion(self.id, submission_id=new_submission_id)
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
            self.submission_id = refreshed.submission_id
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
        self.submission_id = None
        self.completion_timestamp = None

def add_completion(student_id: int, assignment_id: int, submission_id: int, completion_timestamp: int) -> int:
    """Add a new completion to the database."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO completions (student_id, assignment_id, submission_id, completion_timestamp) VALUES (?, ?, ?, ?)",
        (student_id, assignment_id, submission_id, completion_timestamp)
    )
    completion_id = cursor.lastrowid
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Added completion for student {student_id}, assignment {assignment_id} with ID {completion_id}")
    return completion_id

def get_completion(completion_id: int) -> Completion | None:
    """Retrieve a completion by ID."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_id, assignment_id, submission_id, completion_timestamp FROM completions WHERE id = ?",
        (completion_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        print(f"[INFO] [{PRINT_PREFIX}] Retrieved completion with ID {row[0]}")
        return Completion(id=row[0], student_id=row[1], assignment_id=row[2], submission_id=row[3], completion_timestamp=row[4])
    return None

def get_completions_by_student(student_id: int) -> list[Completion]:
    """Retrieve all completions for a given student."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_id, assignment_id, submission_id, completion_timestamp FROM completions WHERE student_id = ?",
        (student_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Retrieved {len(rows)} completions for student {student_id}")
    return [Completion(id=row[0], student_id=row[1], assignment_id=row[2], submission_id=row[3], completion_timestamp=row[4]) for row in rows]

def get_completions_by_assignment(assignment_id: int) -> list[Completion]:
    """Retrieve all completions for a given assignment."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_id, assignment_id, submission_id, completion_timestamp FROM completions WHERE assignment_id = ?",
        (assignment_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Retrieved {len(rows)} completions for assignment {assignment_id}")
    return [Completion(id=row[0], student_id=row[1], assignment_id=row[2], submission_id=row[3], completion_timestamp=row[4]) for row in rows]

def get_student_completions_for_assignment(student_id: int, assignment_id: int) -> Completion | None:
    """Retrieve the completion record for a given student and assignment."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_id, assignment_id, submission_id, completion_timestamp FROM completions WHERE student_id = ? AND assignment_id = ?",
        (student_id, assignment_id)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        print(f"[INFO] [{PRINT_PREFIX}] Retrieved completion for student {student_id} and assignment {assignment_id} with ID {row[0]}")
        return Completion(id=row[0], student_id=row[1], assignment_id=row[2], submission_id=row[3], completion_timestamp=row[4])
    return None

def modify_completion(completion_id: int, student_id: int | None = None, assignment_id: int | None = None, submission_id: int | None = None, completion_timestamp: int | None = None) -> bool:
    """Modify an existing completion. Only provided fields will be updated."""
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
    if submission_id is not None:
        fields_to_update.append("submission_id = ?")
        values.append(submission_id)
    if completion_timestamp is not None:
        fields_to_update.append("completion_timestamp = ?")
        values.append(completion_timestamp)
    
    if not fields_to_update:
        print(f"[INFO] [{PRINT_PREFIX}] No fields to update for completion ID {completion_id}")
        return False  # Nothing to update
    
    values.append(completion_id)
    update_query = f"UPDATE completions SET {', '.join(fields_to_update)} WHERE id = ?"
    
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
        "DELETE FROM completions WHERE id = ?",
        (completion_id,)
    )
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Deleted completion with ID {completion_id}")
    return True
