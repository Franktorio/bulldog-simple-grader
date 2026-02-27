# src/frontend/api/instructor/authentication.py
# Authentication utilities for instructor API

from fastapi import HTTPException
from src.db.grader_db import get_login_token, get_instructor, Instructor
from .constants import AUTH_FAILED_MESSAGE, PRINT_PREFIX


def authenticate_instructor(instructor_id: int = None, instructor_password: str = None, instructor_login_token: str = None) -> Instructor:
    """Authenticate an instructor using either password or login token.
    
    Args:
        instructor_id: Instructor ID for password authentication
        instructor_password: Password for password authentication
        instructor_login_token: Login token for token-based authentication
        
    Returns:
        Student: Authenticated student object
        
    Raises:
        HTTPException: If authentication fails
    """
    if instructor_login_token:
        token = get_login_token(instructor_login_token)
        if not token:
            print(f"[WARNING] [{PRINT_PREFIX}] Invalid login token provided for instructor ID {instructor_id}")
            raise HTTPException(status_code=400, detail=AUTH_FAILED_MESSAGE)
        
        token_instructor = token.instructor_id
        instructor = get_instructor(token_instructor)
        if not instructor:
            print(f"[WARNING] [{PRINT_PREFIX}] No instructor found with ID {token_instructor} for valid login token")
            raise HTTPException(status_code=400, detail=AUTH_FAILED_MESSAGE)
        print(f"[INFO] [{PRINT_PREFIX}] Authenticated instructor ID {token_instructor} using login token")
        token.refresh()
        return instructor

    if instructor_password:
        instructor = get_instructor(instructor_id)
        if not instructor:
            print(f"[WARNING] [{PRINT_PREFIX}] No instructor found with ID {instructor_id} for password authentication")
            raise HTTPException(status_code=400, detail=AUTH_FAILED_MESSAGE)
        if instructor.verify_password(instructor_password):
            print(f"[INFO] [{PRINT_PREFIX}] Authenticated instructor ID {instructor_id} using password")
            return instructor
        else:
            print(f"[WARNING] [{PRINT_PREFIX}] Incorrect password provided for instructor ID {instructor_id}")

    raise HTTPException(status_code=400, detail=AUTH_FAILED_MESSAGE)
