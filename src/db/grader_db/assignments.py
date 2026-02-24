# src/db/grader_db/assignments.py
# Database operations related to assignments

import json
import time
from . import connect_grader_db, connect_grader_db_ro

PRINT_PREFIX = "DB - ASSIGNMENTS"

class Assignment:
    """Represents an assignment in the database."""
    
    def __init__(self, id: int, title: str, directory_name: str, slugs: str, min_completed: int, due_date_timestamp: int | None, is_active: int):
        self.id: int = id
        self.title: str = title
        self.directory_name: str = directory_name
        self.slugs: list[str] = json.loads(slugs)
        self.min_completed: int = min_completed
        self.due_date_timestamp: int | None = due_date_timestamp
        self.is_active: bool = bool(is_active)

    def __str__(self):
        return f"Assignment(id={self.id}, title='{self.title}', directory_name='{self.directory_name}', slugs='{self.slugs}', min_completed={self.min_completed}, due_date_timestamp={self.due_date_timestamp}, is_active={self.is_active})"
    
    def change_title(self, new_title: str):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify assignment without a valid ID.")
            return
        modify_assignment(self.id, title=new_title)
        self.refresh_from_db()

    def change_directory_name(self, new_directory_name: str):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify assignment without a valid ID.")
            return
        modify_assignment(self.id, directory_name=new_directory_name)
        self.refresh_from_db()

    def change_slugs(self, new_slugs: list[str]):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify assignment without a valid ID.")
            return
        modify_assignment(self.id, slugs=new_slugs)
        self.refresh_from_db()

    def change_min_completed(self, new_min_completed: int):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify assignment without a valid ID.")
            return
        modify_assignment(self.id, min_completed=new_min_completed)
        self.refresh_from_db()

    def change_due_date_timestamp(self, new_due_date_timestamp: int | None):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify assignment without a valid ID.")
            return
        modify_assignment(self.id, due_date_timestamp=new_due_date_timestamp)
        self.refresh_from_db()

    def change_is_active(self, new_is_active: bool):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify assignment without a valid ID.")
            return
        modify_assignment(self.id, is_active=new_is_active)
        self.refresh_from_db()

    def delete(self):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot delete assignment without a valid ID.")
            return
        delete_assignment(self.id)

        # Turn everything into None to prevent accidental use after deletion
        self.id = None
        self.title = None
        self.directory_name = None
        self.slugs = None
        self.min_completed = None
        self.due_date_timestamp = None
        self.is_active = None

    def refresh_from_db(self):
        """Refresh the assignment data from the database."""
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot refresh assignment without a valid ID.")
            return
        refreshed = get_assignment(self.id)
        if refreshed:
            self.title = refreshed.title
            self.directory_name = refreshed.directory_name
            self.slugs = refreshed.slugs
            self.min_completed = refreshed.min_completed
            self.due_date_timestamp = refreshed.due_date_timestamp
            self.is_active = refreshed.is_active
        else:
            print(f"[WARNING] [{PRINT_PREFIX}] Assignment with ID {self.id} not found in database.")

def add_assignment(title: str, directory_name: str, slugs: list[str], min_completed: int, due_date_timestamp: int | None = None, is_active: bool = True) -> int:
    """Add a new assignment to the database."""
    conn = connect_grader_db()
    cursor = conn.cursor()

    title = title.replace(" ", "_").lower()
    directory_name = directory_name.replace(" ", "_").lower()

    cursor.execute(
        "INSERT INTO assignments (title, directory_name, slugs, min_completed, due_date_timestamp, is_active) VALUES (?, ?, ?, ?, ?, ?)",
        (title, directory_name, json.dumps(slugs), min_completed, due_date_timestamp, int(is_active))
    )
    assignment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Added assignment '{title}' with ID {assignment_id}")
    return assignment_id

def get_assignment(assignment_id: int) -> Assignment | None:
    """Retrieve an assignment by ID."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, directory_name, slugs, min_completed, due_date_timestamp, is_active FROM assignments WHERE id = ?",
        (assignment_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        print(f"[INFO] [{PRINT_PREFIX}] Retrieved assignment '{row[1]}' with ID {row[0]}")
        return Assignment(id=row[0], title=row[1], directory_name=row[2], slugs=row[3], min_completed=row[4], due_date_timestamp=row[5], is_active=row[6])
    return None

def get_all_assignments(include_due: bool = True, only_active: bool = False) -> list[Assignment]:
    """
    Retrieve all assignments, optionally filtering out those that are past due or inactive.
    
    Args:
        include_due: If False, filter out assignments past their due date
        only_active: If True, only return assignments where is_active=1
    """

    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    if not include_due:
        current_timestamp = int(time.time())
        conditions.append("(due_date_timestamp > ? OR due_date_timestamp IS NULL)")
        params.append(current_timestamp)
    
    if only_active:
        conditions.append("is_active = 1")
    
    where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    
    cursor.execute(
        f"SELECT id, title, directory_name, slugs, min_completed, due_date_timestamp, is_active FROM assignments{where_clause}",
        tuple(params)
    )
    rows = cursor.fetchall()
    conn.close()
    assignments = [Assignment(id=row[0], title=row[1], directory_name=row[2], slugs=row[3], min_completed=row[4], due_date_timestamp=row[5], is_active=row[6]) for row in rows]
    print(f"[INFO] [{PRINT_PREFIX}] Retrieved {len(assignments)} assignments (include_due={include_due}, only_active={only_active})")
    return assignments

def modify_assignment(assignment_id: int, title: str | None = None, directory_name: str | None = None, slugs: list[str] | None = None, min_completed: int | None = None, due_date_timestamp: int | None = None, is_active: bool | None = None) -> bool:
    """Modify an existing assignment. Only provided fields will be updated."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    
    fields_to_update = []
    values = []
    
    if title is not None:
        fields_to_update.append("title = ?")
        values.append(title)
    if directory_name is not None:
        fields_to_update.append("directory_name = ?")
        values.append(directory_name)
    if slugs is not None:
        fields_to_update.append("slugs = ?")
        values.append(json.dumps(slugs))
    if min_completed is not None:
        fields_to_update.append("min_completed = ?")
        values.append(min_completed)
    if due_date_timestamp is not None:
        fields_to_update.append("due_date_timestamp = ?")
        values.append(due_date_timestamp)
    if is_active is not None:
        fields_to_update.append("is_active = ?")
        values.append(int(is_active))
    
    if not fields_to_update:
        print(f"[INFO] [{PRINT_PREFIX}] No fields to update for assignment ID {assignment_id}")
        return False  # Nothing to update
    
    values.append(assignment_id)
    update_query = f"UPDATE assignments SET {', '.join(fields_to_update)} WHERE id = ?"
    
    cursor.execute(update_query, tuple(values))
    conn.commit()
    conn.close()
    
    print(f"[INFO] [{PRINT_PREFIX}] Modified assignment with ID {assignment_id}")
    return True

def delete_assignment(assignment_id: int) -> bool:
    """Delete an assignment from the database."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM assignments WHERE id = ?",
        (assignment_id,)
    )
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Deleted assignment with ID {assignment_id}")
    return True