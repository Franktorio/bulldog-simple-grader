# src/db/grader_db/login_tokens.py
# Database operations related to login tokens

import time
import threading
import secrets
from . import connect_grader_db, connect_grader_db_ro

PRINT_PREFIX = "DB - LOGIN_TOKENS"
TOKEN_CLEANUP_INTERVAL = 300  # Run cleanup every 5 minutes

class LoginToken:
    """Represents a login token in the database."""
    
    def __init__(self, token: str, student_id: int | None, instructor_id: int | None, expiration_timestamp: int):
        self.token = token
        self.student_id = student_id
        self.instructor_id = instructor_id
        self.expiration_timestamp = expiration_timestamp

    def __str__(self):
        return f"LoginToken(token='{self.token[:8]}...', student_id={self.student_id}, instructor_id={self.instructor_id}, expires={self.expiration_timestamp})"
    
    def is_expired(self) -> bool:
        """Check if this token has expired."""
        return time.time() >= self.expiration_timestamp
    
    def refresh(self, additional_seconds: int = 86400 * 7) -> bool: # Default additional time is 7 days
        """Refresh this token's expiration time."""
        if self.is_expired():
            print(f"[WARNING] [{PRINT_PREFIX}] Cannot refresh expired token for student ID {self.student_id}")
            return False
        new_expiration_timestamp = int(time.time() + additional_seconds)
        if refresh_token(self.token, additional_seconds):
            self.expiration_timestamp = new_expiration_timestamp
            print(f"[INFO] [{PRINT_PREFIX}] Refreshed token for student ID {self.student_id}")
            return True
        else:
            print(f"[ERROR] [{PRINT_PREFIX}] Failed to refresh token for student ID {self.student_id}")
            return False
    
    def delete(self):
        """Delete this token from the database."""
        delete_login_token(self.token)
        self.token = None
        self.student_id = None
        self.expiration_timestamp = None

def generate_token() -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(32)

def add_login_token(student_id: int = None, instructor_id: int = None, expiration_seconds: int = 86400 * 7) -> str:
    """
    Add a new login token for a student or instructor (dual-mode).
    Args:
        student_id: The ID of the student (optional)
        instructor_id: The ID of the instructor (optional)
        expiration_seconds: Time in seconds until token expires (default: 7 days)
    Returns:
        The generated token string
    """
    if (student_id is None and instructor_id is None) or (student_id is not None and instructor_id is not None):
        raise ValueError("Must provide exactly one of student_id or instructor_id")
    token = generate_token()
    expiration_timestamp = int(time.time() + expiration_seconds)
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO login_tokens (token, student_id, instructor_id, expiration_timestamp) VALUES (?, ?, ?, ?)",
        (token, student_id, instructor_id, expiration_timestamp)
    )
    conn.commit()
    conn.close()
    if student_id is not None:
        print(f"[INFO] [{PRINT_PREFIX}] Added login token for student ID {student_id}")
    else:
        print(f"[INFO] [{PRINT_PREFIX}] Added login token for instructor ID {instructor_id}")
    return token

def get_login_token(token: str) -> LoginToken | None:
    """Retrieve a login token by token string."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT token, student_id, instructor_id, expiration_timestamp FROM login_tokens WHERE token = ?",
        (token,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        login_token = LoginToken(token=row[0], student_id=row[1], instructor_id=row[2], expiration_timestamp=row[3])
        if login_token.is_expired():
            who = f"student ID {row[1]}" if row[1] is not None else f"instructor ID {row[2]}"
            print(f"[WARNING] [{PRINT_PREFIX}] Token has expired for {who}")
            delete_login_token(token)  # Clean up expired token
            return None
        who = f"student ID {row[1]}" if row[1] is not None else f"instructor ID {row[2]}"
        print(f"[INFO] [{PRINT_PREFIX}] Retrieved valid login token for {who}")
        return login_token
    return None

def get_tokens_by_student(student_id: int) -> list[LoginToken]:
    """Retrieve all login tokens for a specific student."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT token, student_id, instructor_id, expiration_timestamp FROM login_tokens WHERE student_id = ?",
        (student_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Retrieved {len(rows)} login tokens for student ID {student_id}")
    return [LoginToken(token=row[0], student_id=row[1], instructor_id=row[2], expiration_timestamp=row[3]) for row in rows]

def get_tokens_by_instructor(instructor_id: int) -> list[LoginToken]:
    """Retrieve all login tokens for a specific instructor."""
    conn = connect_grader_db_ro()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT token, student_id, instructor_id, expiration_timestamp FROM login_tokens WHERE instructor_id = ?",
        (instructor_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Retrieved {len(rows)} login tokens for instructor ID {instructor_id}")
    return [LoginToken(token=row[0], student_id=row[1], instructor_id=row[2], expiration_timestamp=row[3]) for row in rows]

def delete_login_token(token: str) -> bool:
    """Delete a login token from the database."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM login_tokens WHERE token = ?",
        (token,)
    )
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Deleted login token")
    return True

def delete_all_student_tokens(student_id: int) -> int:
    """Delete all login tokens for a specific student."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM login_tokens WHERE student_id = ?",
        (student_id,)
    )
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Deleted {deleted_count} login tokens for student ID {student_id}")
    return deleted_count

def delete_all_instructor_tokens(instructor_id: int) -> int:
    """Delete all login tokens for a specific instructor."""
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM login_tokens WHERE instructor_id = ?",
        (instructor_id,)
    )
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"[INFO] [{PRINT_PREFIX}] Deleted {deleted_count} login tokens for instructor ID {instructor_id}")
    return deleted_count


def refresh_token(token: str, additional_seconds: int = 86400 * 7) -> bool:
    """Refresh a login token's expiration time."""
    new_expiration_timestamp = int(time.time() + additional_seconds)
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE login_tokens SET expiration_timestamp = ? WHERE token = ?",
        (new_expiration_timestamp, token)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    if updated:
        print(f"[INFO] [{PRINT_PREFIX}] Refreshed login token expiration")
    else:
        print(f"[WARNING] [{PRINT_PREFIX}] Failed to refresh login token (not found)")
    return updated

def delete_expired_tokens() -> int:
    """Delete all expired login tokens from the database."""
    current_time = int(time.time())
    conn = connect_grader_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM login_tokens WHERE expiration_timestamp <= ?",
        (current_time,)
    )
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    if deleted_count > 0:
        print(f"[INFO] [{PRINT_PREFIX}] Deleted {deleted_count} expired login tokens")
    return deleted_count

def _cleanup_loop():
    """Background thread function that periodically removes expired tokens."""
    while True:
        try:
            time.sleep(TOKEN_CLEANUP_INTERVAL)
            delete_expired_tokens()
        except Exception as e:
            print(f"[ERROR] [{PRINT_PREFIX}] Error in cleanup loop: {e}")

# Start the cleanup thread when module is imported
_cleanup_thread = threading.Thread(target=_cleanup_loop, daemon=True, name="TokenCleanupThread")
_cleanup_thread.start()
print(f"[INFO] [{PRINT_PREFIX}] Token cleanup thread started")
