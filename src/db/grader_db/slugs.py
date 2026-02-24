# src/db/grader_db/slugs.py
# Database operations related to slugs

from . import connect_grader_db, connect_grader_db_ro

PRINT_PREFIX = "DB - SLUGS"

class Slug:
    """Represents a slug in the database."""
    
    def __init__(self, name: str, assignment_id: int):
        self.name = name
        self.assignment_id = assignment_id

    def __str__(self):
        return f"Slug(name='{self.name}', assignment_id={self.assignment_id})"
    
    def change_assignment_id(self, new_assignment_id: int):
        if not self.name:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify slug without a valid name.")
            return
        modify_slug(self.name, assignment_id=new_assignment_id)
        self.refresh_from_db()

    def refresh_from_db(self):
        """Reload this slug's data from the database."""
        if not self.name:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot refresh slug without a valid name.")
            return
        refreshed = get_slug(self.name)
        if refreshed:
            self.assignment_id = refreshed.assignment_id
        else:
            print(f"[WARNING] [{PRINT_PREFIX}] Slug '{self.name}' not found in database.")

    def delete(self):
        if not self.name:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot delete slug without a valid name.")
            return
        delete_slug(self.name)
        
        # Turn everything into None to prevent accidental use after deletion
        self.name = None
        self.assignment_id = None

def add_slug(name: str, assignment_id: int) -> str:
    """Add a new slug to the database."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO slugs (name, assignment_id) VALUES (?, ?)",
        (name, assignment_id)
    )
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Added slug '{name}' for assignment ID {assignment_id}")
    return name

def get_slug(name: str) -> Slug | None:
    """Retrieve a slug by name."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, assignment_id FROM slugs WHERE name = ?",
        (name,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        print(f"[INFO] [{PRINT_PREFIX}] Retrieved slug '{row[0]}' for assignment ID {row[1]}")
        return Slug(name=row[0], assignment_id=row[1])
    return None

def get_slugs_by_assignment(assignment_id: int) -> list[Slug]:
    """Retrieve all slugs for a given assignment."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, assignment_id FROM slugs WHERE assignment_id = ?",
        (assignment_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Retrieved {len(rows)} slugs for assignment ID {assignment_id}")
    return [Slug(name=row[0], assignment_id=row[1]) for row in rows]

def modify_slug(name: str, assignment_id: int | None = None) -> bool:
    """Modify an existing slug. Only provided fields will be updated."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    
    fields_to_update = []
    values = []
    
    if assignment_id is not None:
        fields_to_update.append("assignment_id = ?")
        values.append(assignment_id)
    
    if not fields_to_update:
        print(f"[INFO] [{PRINT_PREFIX}] No fields to update for slug '{name}'")
        return False  # Nothing to update
    
    values.append(name)
    update_query = f"UPDATE slugs SET {', '.join(fields_to_update)} WHERE name = ?"
    
    cursor.execute(update_query, tuple(values))
    conn.commit()
    conn.close()
    
    print(f"[INFO] [{PRINT_PREFIX}] Modified slug '{name}'")
    return True

def delete_slug(name: str) -> bool:
    """Delete a slug from the database."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM slugs WHERE name = ?",
        (name,)
    )
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Deleted slug '{name}'")
    return True
