# src/frontend/api/student/authentication.py
# Authentication utilities for student API

from fastapi import HTTPException
from src.db.grader_db import login_tokens, get_student, Student
from .constants import AUTH_FAILED_MESSAGE, PRINT_PREFIX


def authenticate_student(student_id: int = None, student_password: str = None, student_login_token: str = None) -> Student:
    """Authenticate a student using either password or login token.
    
    Args:
        student_id: Student ID for password authentication
        student_password: Password for password authentication
        student_login_token: Login token for token-based authentication
        
    Returns:
        Student: Authenticated student object
        
    Raises:
        HTTPException: If authentication fails
    """
    if student_login_token:
        token = login_tokens.get_login_token(student_login_token)
        if not token:
            print(f"[WARNING] [{PRINT_PREFIX}] Invalid login token provided for student ID {student_id}")
            raise HTTPException(status_code=401, detail=AUTH_FAILED_MESSAGE)
        
        token_student = token.student_id
        student = get_student(token_student)
        if not student:
            print(f"[WARNING] [{PRINT_PREFIX}] No student found with ID {token_student} for valid login token")
            raise HTTPException(status_code=401, detail=AUTH_FAILED_MESSAGE)
        print(f"[INFO] [{PRINT_PREFIX}] Authenticated student ID {token_student} using login token")
        token.refresh()
        return student

    if student_password:
        student = get_student(student_id)
        if not student:
            print(f"[WARNING] [{PRINT_PREFIX}] No student found with ID {student_id} for password authentication")
            raise HTTPException(status_code=401, detail=AUTH_FAILED_MESSAGE)
        if student.verify_password(student_password):
            print(f"[INFO] [{PRINT_PREFIX}] Authenticated student ID {student_id} using password")
            return student
        else:
            print(f"[WARNING] [{PRINT_PREFIX}] Incorrect password provided for student ID {student_id}")

    raise HTTPException(status_code=401, detail=AUTH_FAILED_MESSAGE)
