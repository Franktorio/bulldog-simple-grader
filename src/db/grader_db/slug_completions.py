# src/db/grader_db/slug_completions.py
# Database operations related to slug completions

from . import connect_grader_db, connect_grader_db_ro

PRINT_PREFIX = "DB - SLUG_COMPLETIONS"

class SlugCompletion:
    """Represents a slug completion in the database."""
    
    def __init__(self, id: int, student_id: int, assignment_id: int, slug: str, submission_id: int, completion_timestamp: int):
        self.id = id
        self.student_id = student_id
        self.assignment_id = assignment_id
        self.slug = slug
        self.submission_id = submission_id
        self.completion_timestamp = completion_timestamp

    def __str__(self):
        return f"SlugCompletion(id={self.id}, student_id={self.student_id}, assignment_id={self.assignment_id}, slug={self.slug}, submission_id={self.submission_id}, completion_timestamp={self.completion_timestamp})"
    

    def change_student_id(self, new_student_id: int):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify slug completion without a valid ID.")
            return
        modify_slug_completion(self.id, student_id=new_student_id)
        self.refresh_from_db()

    def change_assignment_id(self, new_assignment_id: int):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify slug completion without a valid ID.")
            return
        modify_slug_completion(self.id, assignment_id=new_assignment_id)
        self.refresh_from_db()

    def change_slug(self, new_slug: str):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify slug completion without a valid ID.")
            return
        modify_slug_completion(self.id, slug=new_slug)
        self.refresh_from_db()

    def change_submission_id(self, new_submission_id: int):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify slug completion without a valid ID.")
            return
        modify_slug_completion(self.id, submission_id=new_submission_id)
        self.refresh_from_db()

    def change_completion_timestamp(self, new_completion_timestamp: int):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify slug completion without a valid ID.")
            return
        modify_slug_completion(self.id, completion_timestamp=new_completion_timestamp)
        self.refresh_from_db()

    def refresh_from_db(self):
        """Reload this slug completion's data from the database."""
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot refresh slug completion without a valid ID.")
            return
        refreshed = get_slug_completion(self.id)
        if refreshed:
            self.student_id = refreshed.student_id
            self.assignment_id = refreshed.assignment_id
            self.slug = refreshed.slug
            self.submission_id = refreshed.submission_id
            self.completion_timestamp = refreshed.completion_timestamp
        else:
            print(f"[WARNING] [{PRINT_PREFIX}] Slug completion with ID {self.id} not found in database.")

    def delete(self):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot delete slug completion without a valid ID.")
            return
        delete_slug_completion(self.id)
        
        # Turn everything into None to prevent accidental use after deletion
        self.id = None
        self.student_id = None
        self.assignment_id = None
        self.slug = None
        self.submission_id = None
        self.completion_timestamp = None

def add_slug_completion(student_id: int, assignment_id: int, slug: str, submission_id: int, completion_timestamp: int) -> int | None:
    """
    Add a new slug completion to the database.
    Returns the slug completion ID if successful, None if a duplicate exists (enforces one per student per assignment per slug).
    """
    conn = connect_grader_db()
    cursor = conn.cursor()
    
    # Check if this slug completion already exists for this student and assignment
    cursor.execute(
        "SELECT id FROM slug_completions WHERE student_id = ? AND assignment_id = ? AND slug = ?",
        (student_id, assignment_id, slug)
    )
    existing = cursor.fetchone()
    
    if existing:
        print(f"[WARNING] [{PRINT_PREFIX}] Slug completion already exists for student {student_id}, assignment {assignment_id}, slug '{slug}'")
        conn.close()
        return None
    
    cursor.execute(
        "INSERT INTO slug_completions (student_id, assignment_id, slug, submission_id, completion_timestamp) VALUES (?, ?, ?, ?, ?)",
        (student_id, assignment_id, slug, submission_id, completion_timestamp)
    )
    slug_completion_id = cursor.lastrowid
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Added slug completion for student {student_id}, assignment {assignment_id}, slug '{slug}' with ID {slug_completion_id}")
    return slug_completion_id

def get_slug_completion(slug_completion_id: int) -> SlugCompletion | None:
    """Retrieve a slug completion by ID."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_id, assignment_id, slug, submission_id, completion_timestamp FROM slug_completions WHERE id = ?",
        (slug_completion_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        print(f"[INFO] [{PRINT_PREFIX}] Retrieved slug completion with ID {row[0]}")
        return SlugCompletion(id=row[0], student_id=row[1], assignment_id=row[2], slug=row[3], submission_id=row[4], completion_timestamp=row[5])
    return None

def get_slug_completions_by_student(student_id: int) -> list[SlugCompletion]:
    """Retrieve all slug completions for a given student."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_id, assignment_id, slug, submission_id, completion_timestamp FROM slug_completions WHERE student_id = ?",
        (student_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Retrieved {len(rows)} slug completions for student {student_id}")
    return [SlugCompletion(id=row[0], student_id=row[1], assignment_id=row[2], slug=row[3], submission_id=row[4], completion_timestamp=row[5]) for row in rows]

def get_slug_completions_by_assignment(assignment_id: int) -> list[SlugCompletion]:
    """Retrieve all slug completions for a given assignment."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_id, assignment_id, slug, submission_id, completion_timestamp FROM slug_completions WHERE assignment_id = ?",
        (assignment_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Retrieved {len(rows)} slug completions for assignment {assignment_id}")
    return [SlugCompletion(id=row[0], student_id=row[1], assignment_id=row[2], slug=row[3], submission_id=row[4], completion_timestamp=row[5]) for row in rows]

def get_slug_completions_by_student_and_assignment(student_id: int, assignment_id: int) -> list[SlugCompletion]:
    """Retrieve all slug completions for a given student and assignment."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_id, assignment_id, slug, submission_id, completion_timestamp FROM slug_completions WHERE student_id = ? AND assignment_id = ?",
        (student_id, assignment_id)
    )
    rows = cursor.fetchall()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Retrieved {len(rows)} slug completions for student {student_id}, assignment {assignment_id}")
    return [SlugCompletion(id=row[0], student_id=row[1], assignment_id=row[2], slug=row[3], submission_id=row[4], completion_timestamp=row[5]) for row in rows]

def modify_slug_completion(slug_completion_id: int, student_id: int | None = None, assignment_id: int | None = None, slug: str | None = None, submission_id: int | None = None, completion_timestamp: int | None = None) -> bool:
    """Modify an existing slug completion. Only provided fields will be updated."""
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
    if submission_id is not None:
        fields_to_update.append("submission_id = ?")
        values.append(submission_id)
    if completion_timestamp is not None:
        fields_to_update.append("completion_timestamp = ?")
        values.append(completion_timestamp)
    
    if not fields_to_update:
        print(f"[INFO] [{PRINT_PREFIX}] No fields to update for slug completion ID {slug_completion_id}")
        return False  # Nothing to update
    
    values.append(slug_completion_id)
    update_query = f"UPDATE slug_completions SET {', '.join(fields_to_update)} WHERE id = ?"
    
    cursor.execute(update_query, tuple(values))
    conn.commit()
    conn.close()
    
    print(f"[INFO] [{PRINT_PREFIX}] Modified slug completion with ID {slug_completion_id}")
    return True

def delete_slug_completion(slug_completion_id: int) -> bool:
    """Delete a slug completion from the database."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM slug_completions WHERE id = ?",
        (slug_completion_id,)
    )
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Deleted slug completion with ID {slug_completion_id}")
    return True
