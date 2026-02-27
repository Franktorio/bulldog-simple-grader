# src/db/grader_db/students.py
# Database operations related to students

import bcrypt
from . import connect_grader_db, connect_grader_db_ro

PRINT_PREFIX = "DB - STUDENTS"

class Student:
    """Represents a student in the database."""
    
    def __init__(self, id: int, name: str, hash_password: str = None):
        self.id = id
        self.name = name
        self.hash_password = hash_password

    def __str__(self):
        return f"Student(id={self.id}, name='{self.name}')"
    
    def change_name(self, new_name: str):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot modify student without a valid ID.")
            return
        modify_student(self.id, name=new_name)
        self.refresh_from_db()

    def refresh_from_db(self):
        """Reload this student's data from the database."""
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot refresh student without a valid ID.")
            return
        refreshed = get_student(self.id)
        if refreshed:
            self.name = refreshed.name
            self.hash_password = refreshed.hash_password
        else:
            print(f"[WARNING] [{PRINT_PREFIX}] Student with ID {self.id} not found in database.")

    def delete(self):
        if not self.id:
            print(f"[ERROR] [{PRINT_PREFIX}] Cannot delete student without a valid ID.")
            return
        delete_student(self.id)
        
        # Turn everything into None to prevent accidental use after deletion
        self.id = None
        self.name = None
        self.hash_password = None
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against this student's stored hash."""
        if not self.hash_password:
            print(f"[ERROR] [{PRINT_PREFIX}] No password set for student ID {self.id}")
            return False
        return verify_password(self.id, password)
    
    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change this student's password after verifying the old password."""
        return change_password(self.id, old_password, new_password)
    
    def set_password(self, password: str) -> bool:
        """Set/update this student's password (without verification)."""
        result = set_password(self.id, password)
        if result:
            self.refresh_from_db()
        return result

def add_student(student_id: int, name: str, password: str = None) -> int:
    """Add a new student to the database."""
    hash_password = None
    if password:
        hash_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    conn = connect_grader_db()
    cursor = conn.cursor()
    student = get_student(student_id)
    if student:
        print(f"[ERROR] [{PRINT_PREFIX}] Student with ID {student_id} already exists.")
        conn.close()
        return student_id
    cursor.execute(
        "INSERT INTO students (id, name, hash_password) VALUES (?, ?, ?)",
        (student_id, name, hash_password)
    )
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Added student '{name}' with ID {student_id}")
    return student_id

def get_student(student_id: int) -> Student | None:
    """Retrieve a student by ID."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, hash_password FROM students WHERE id = ?",
        (student_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        print(f"[INFO] [{PRINT_PREFIX}] Retrieved student '{row[1]}' with ID {row[0]}")
        return Student(id=row[0], name=row[1], hash_password=row[2])
    return None

def get_all_students() -> list[Student]:
    """Retrieve all students from the database."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, hash_password FROM students")
    rows = cursor.fetchall()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Retrieved {len(rows)} students")
    return [Student(id=row[0], name=row[1], hash_password=row[2]) for row in rows]

def modify_student(student_id: int, name: str | None = None) -> bool:
    """Modify an existing student. Only provided fields will be updated."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    
    fields_to_update = []
    values = []
    
    if name is not None:
        fields_to_update.append("name = ?")
        values.append(name)
    
    if not fields_to_update:
        print(f"[INFO] [{PRINT_PREFIX}] No fields to update for student ID {student_id}")
        return False  # Nothing to update
    
    values.append(student_id)
    update_query = f"UPDATE students SET {', '.join(fields_to_update)} WHERE id = ?"
    
    cursor.execute(update_query, tuple(values))
    conn.commit()
    conn.close()
    
    print(f"[INFO] [{PRINT_PREFIX}] Modified student with ID {student_id}")
    return True

def delete_student(student_id: int) -> bool:
    """Delete a student from the database."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM students WHERE id = ?",
        (student_id,)
    )
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Deleted student with ID {student_id}")
    return True

def set_password(student_id: int, password: str) -> bool:
    """Set or update a student's password."""
    if not password:
        print(f"[ERROR] [{PRINT_PREFIX}] Cannot set empty password for student ID {student_id}")
        return False
    
    hash_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE students SET hash_password = ? WHERE id = ?",
        (hash_password, student_id)
    )
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Set password for student ID {student_id}")
    return True

def verify_password(student_id: int, password: str) -> bool:
    """Verify a password against the stored hash for a student."""
    student = get_student(student_id)
    if not student:
        print(f"[ERROR] [{PRINT_PREFIX}] Student ID {student_id} not found")
        return False
    
    if not student.hash_password:
        print(f"[ERROR] [{PRINT_PREFIX}] No password set for student ID {student_id}")
        return False
    
    is_valid = bcrypt.checkpw(password.encode('utf-8'), student.hash_password.encode('utf-8'))
    if is_valid:
        print(f"[INFO] [{PRINT_PREFIX}] Password verified for student ID {student_id}")
    else:
        print(f"[WARNING] [{PRINT_PREFIX}] Invalid password for student ID {student_id}")
    return is_valid

def change_password(student_id: int, old_password: str | None, new_password: str, from_script: bool = False) -> bool:
    """Change a student's password after verifying the old password."""
    if not verify_password(student_id, old_password) and not from_script:
        print(f"[ERROR] [{PRINT_PREFIX}] Cannot change password - old password incorrect for student ID {student_id}")
        return False
    
    return set_password(student_id, new_password)
