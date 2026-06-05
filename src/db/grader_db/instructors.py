# src/db/grader_db/instructors.py
# Database operations related to instructors

import bcrypt
from . import connect_grader_db, connect_grader_db_ro

PRINT_PREFIX = "DB - INSTRUCTORS"

class Instructor:
    """Represents an instructor in the database."""
    
    def __init__(self, id: int, name: str, hash_password: str = None):
        self.id = id
        self.name = name
        self.hash_password = hash_password

    def __str__(self):
        return f"Instructor(id={self.id}, name='{self.name}')"
    
    def change_name(self, new_name: str):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify instructor without a valid ID.")
            return
        modify_instructor(self.id, name=new_name)
        self.refresh_from_db()

    def refresh_from_db(self):
        """Reload this instructor's data from the database."""
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot refresh instructor without a valid ID.")
            return
        refreshed = get_instructor(self.id)
        if refreshed:
            self.name = refreshed.name
            self.hash_password = refreshed.hash_password
        else:
            print(f"[WARNING] [{PRINT_PREFIX}] Instructor with ID {self.id} not found in database.")

    def delete(self):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot delete instructor without a valid ID.")
            return
        delete_instructor(self.id)
        
        # Turn everything into None to prevent accidental use after deletion
        self.id = None
        self.name = None
        self.hash_password = None
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against this instructor's stored hash."""
        if not self.hash_password:
            print(f"[ERROR] [{PRINT_PREFIX}] No password set for instructor ID {self.id}")
            return False
        return verify_password(self.id, password)
    
    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change this instructor's password after verifying the old password."""
        return change_password(self.id, old_password, new_password)
    
    def set_password(self, password: str) -> bool:
        """Set/update this instructor's password (without verification)."""
        result = set_password(self.id, password)
        if result:
            self.refresh_from_db()
        return result

def add_instructor(instructor_id: int, name: str, password: str = None) -> int:
    """Add a new instructor to the database."""
    hash_password = None
    if password:
        hash_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO instructors (id, name, hash_password) VALUES (?, ?, ?)",
        (instructor_id, name, hash_password)
    )
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Added instructor '{name}' with ID {instructor_id}")
    return instructor_id

def get_instructor(instructor_id: int) -> Instructor | None:
    """Retrieve an instructor by ID."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, hash_password FROM instructors WHERE id = ?",
        (instructor_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        print(f"[INFO] [{PRINT_PREFIX}] Retrieved instructor '{row[1]}' with ID {row[0]}")
        return Instructor(id=row[0], name=row[1], hash_password=row[2])
    return None

def get_all_instructors() -> list[Instructor]:
    """Retrieve all instructors from the database."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, hash_password FROM instructors")
    rows = cursor.fetchall()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Retrieved {len(rows)} instructors")
    return [Instructor(id=row[0], name=row[1], hash_password=row[2]) for row in rows]

def modify_instructor(instructor_id: int, name: str | None = None) -> bool:
    """Modify an existing instructor. Only provided fields will be updated."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    
    fields_to_update = []
    values = []
    
    if name is not None:
        fields_to_update.append("name = ?")
        values.append(name)
    
    if not fields_to_update:
        print(f"[INFO] [{PRINT_PREFIX}] No fields to update for instructor ID {instructor_id}")
        return False  # Nothing to update
    
    values.append(instructor_id)
    update_query = f"UPDATE instructors SET {', '.join(fields_to_update)} WHERE id = ?"
    
    cursor.execute(update_query, tuple(values))
    conn.commit()
    conn.close()
    
    print(f"[INFO] [{PRINT_PREFIX}] Modified instructor with ID {instructor_id}")
    return True

def delete_instructor(instructor_id: int) -> bool:
    """Delete an instructor from the database."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM instructors WHERE id = ?",
        (instructor_id,)
    )
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Deleted instructor with ID {instructor_id}")
    return True

def set_password(instructor_id: int, password: str) -> bool:
    """Set or update an instructor's password."""
    if not password:
        print(f"[ERROR] [{PRINT_PREFIX}] Cannot set empty password for instructor ID {instructor_id}")
        return False
    
    hash_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE instructors SET hash_password = ? WHERE id = ?",
        (hash_password, instructor_id)
    )
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Set password for instructor ID {instructor_id}")
    return True

def verify_password(instructor_id: int, password: str) -> bool:
    """Verify a password against the stored hash for an instructor."""
    instructor = get_instructor(instructor_id)
    if not instructor:
        print(f"[ERROR] [{PRINT_PREFIX}] Instructor ID {instructor_id} not found")
        return False
    
    if not instructor.hash_password:
        print(f"[ERROR] [{PRINT_PREFIX}] No password set for instructor ID {instructor_id}")
        return False
    
    is_valid = bcrypt.checkpw(password.encode('utf-8'), instructor.hash_password.encode('utf-8'))
    if is_valid:
        print(f"[INFO] [{PRINT_PREFIX}] Password verified for instructor ID {instructor_id}")
    else:
        print(f"[WARNING] [{PRINT_PREFIX}] Invalid password for instructor ID {instructor_id}")
    return is_valid

def change_password(instructor_id: int, old_password: str = None, new_password: str = "UnsetPassword", from_script: bool = False) -> bool:
    """Change an instructor's password after verifying the old password."""
    if not from_script and not verify_password(instructor_id, old_password):
        print(f"[ERROR] [{PRINT_PREFIX}] Cannot change password - old password incorrect for instructor ID {instructor_id}")
        return False
    
    return set_password(instructor_id, new_password)
