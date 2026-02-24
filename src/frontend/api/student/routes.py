# src/frontend/api/student/routes.py
# Route handlers for student API]

from fastapi import APIRouter, HTTPException, Cookie, Request, Form, Depends, UploadFile
from fastapi.responses import RedirectResponse
from src.db import grader_db
from src.db.grader_db.slug_completions import SlugCompletion
from src.db.grader_db.slugs import Slug
from src.db.grader_db import login_tokens, Student, helpers, Assignment
from src.checks.orchestrator import orchestrate_checks
from src.frontend.api.paths import templates
from src.utils import format_datetime
from .authentication import authenticate_student
from .constants import (
    STUDENT_LOGIN_TEMPLATE,
    STUDENT_HOME_TEMPLATE,
    AUTH_FAILED_MESSAGE,
    COOKIE_KEY,
    COOKIE_MAX_AGE,
    PRINT_PREFIX,
    STUDENT_HOME_URL,
    STUDENT_ASSIGNMENT_TEMPLATE,
    STUDENT_SUBMIT_TEMPLATE,
    STUDENT_SUBMIT_URL
)

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
MIN_FILE_SIZE_BYTES = 1  # 1 byte

router = APIRouter(prefix="/students", tags=["students"])

def get_authenticated_student(student_login_token: str = Cookie(None)) -> Student:
    """Dependency to get authenticated student from cookie token.
    
    Raises:
        HTTPException: 401 if authentication fails
    """
    if not student_login_token:
        print(f"[INFO] [{PRINT_PREFIX}] No login token found in cookies.")
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    print(f"[INFO] [{PRINT_PREFIX}] Attempting to authenticate student with login token: {student_login_token[-5:]}...")
    try:
        student = authenticate_student(student_login_token=student_login_token)
        print(f"[INFO] [{PRINT_PREFIX}] Successfully authenticated student ID {student.id}.")
        return student
    except HTTPException:
        print(f"[INFO] [{PRINT_PREFIX}] Authentication failed for token: {student_login_token[-5:]}.")
        raise HTTPException(status_code=401, detail="Invalid authentication")

@router.get("/login", name="student_login")
def student_login(request: Request, student_login_token: str = Cookie(None)):
    """Display the login page or redirect to home if already authenticated."""
    if student_login_token:
        try:
            print(f"[INFO] [{PRINT_PREFIX}] Login token found in cookies. Attempting to authenticate student with token: {student_login_token[-5:]}...")
            student = authenticate_student(student_login_token=student_login_token)
            print(f"[INFO] [{PRINT_PREFIX}] Student ID {student.id} already logged in with valid token. Redirecting to home page.")
            return RedirectResponse(url=STUDENT_HOME_URL, status_code=303)
        except HTTPException:
            print(f"[INFO] [{PRINT_PREFIX}] Existing login token invalid. Proceeding to login page.")
    
    user_data = {
        "authenticated": False
    }
    return templates.TemplateResponse(STUDENT_LOGIN_TEMPLATE, {"request": request, "user_data": user_data})

@router.get("/home", name="student_home")
def student_home(request: Request, student: Student = Depends(get_authenticated_student)):
    """Display the student home page with assignments."""
    def _dict_assignment(assignment: Assignment) -> dict:
        return {
            "id": assignment.id,
            "title": assignment.title,
            "directory_name": assignment.directory_name,
            "slugs": assignment.slugs,
            "min_completed": assignment.min_completed,
            "due_date_timestamp": format_datetime(assignment.due_date_timestamp),
            "is_active": assignment.is_active
        }
    all_assignments_dict = helpers.get_all_assignments_in_perspective_of_student(student.id)
    assignment_data = {}
    for aid, data in all_assignments_dict.items():
        assignment_data[aid] = _dict_assignment(data["assignment"])
        assignment_data[aid]["is_completed"] = data["is_completed"]
        assignment_data[aid]["requirements"] = data["requirements"]
        assignment_data[aid]["progress"] = data["progress"]

    user_data = {
        "authenticated": True,
        "id": student.id,
        "name": student.name,
        "assignments": assignment_data,
    }
    print(f"[INFO] [{PRINT_PREFIX}] Rendering home page for student ID {student.id} with {len(assignment_data)} assignments.")
    return templates.TemplateResponse(STUDENT_HOME_TEMPLATE, {"request": request, "user_data": user_data})

@router.get("/assignments/{assignment_id}", name="student_assignment_detail")
def student_assignment_detail(request: Request, assignment_id: int, student: Student = Depends(get_authenticated_student)):
    """Display the detail page for a specific assignment."""
    assignment_detail = helpers.get_assignment_from_student_perspective(student.id, assignment_id)
    if not assignment_detail:
        print(f"[WARNING] [{PRINT_PREFIX}] Assignment ID {assignment_id} not found for student ID {student.id}.")
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    def _dict_assignment(assignment: Assignment) -> dict:
        return {
            "id": assignment.id,
            "title": assignment.title,
            "directory_name": assignment.directory_name,
            "slugs": assignment.slugs,
            "min_completed": assignment.min_completed,
            "due_date_timestamp": format_datetime(assignment.due_date_timestamp),
            "is_active": assignment.is_active
        }
    
    def _dict_slug(slug: Slug | SlugCompletion) -> dict:
        return {
            "name": slug.slug if isinstance(slug, SlugCompletion) else slug.name,
        }
    
    data = {
        "authenticated": True,
        "assignment": _dict_assignment(assignment_detail["assignment"]),
        "is_completed": assignment_detail["is_completed"],
        "requirements": assignment_detail["requirements"],
        "progress": assignment_detail["progress"],
        "slugs_available": [_dict_slug(s) for s in assignment_detail["slugs_available"]],
        "slugs_completed": [_dict_slug(s)["name"] for s in assignment_detail["slugs_completed"]]
    }
    print(f"[INFO] [{PRINT_PREFIX}] Rendering assignment detail page for student ID {student.id} and assignment ID {assignment_id}.")
    return templates.TemplateResponse(STUDENT_ASSIGNMENT_TEMPLATE, {"request": request, "user_data": data})

@router.get("/assignments/{assignment_id}/{slug_name}", name="student_submit_problem")
def student_submit_problem(request: Request, assignment_id: int, slug_name: str, student: Student = Depends(get_authenticated_student)):
    """Handle submission of a problem by a student."""

    submissions = helpers.get_submissions_for_student_slug(student.id, slug_name)
    completions = grader_db.slug_completions.get_slug_completions_by_student_and_assignment(student.id, assignment_id)

    completion_status = any(c.slug == slug_name for c in completions)

    submissions.reverse()

    return templates.TemplateResponse(STUDENT_SUBMIT_TEMPLATE, {"request": request, "user_data": {
        "authenticated": True,
        "assignment_id": assignment_id,
        "slug_name": slug_name,
        "submissions": submissions,
        "completed": completion_status
    }})

@router.post("/assignments/{assignment_id}/{slug_name}", name="student_submit_problem_post")
async def student_submit_problem_post(request: Request, assignment_id: int, slug_name: str, submission_file: UploadFile = Form(...), student: Student = Depends(get_authenticated_student)):
    """Handle submission of a problem by a student."""
    filename = submission_file.filename
    try:
        submitted_code = submission_file.file.read().decode("utf-8")
    except Exception as e:
        return RedirectResponse(url=STUDENT_SUBMIT_URL.format(assignment_id=assignment_id, slug_name=slug_name), status_code=303)
    
    if len(submitted_code.encode("utf-8", errors="ignore")) > MAX_FILE_SIZE_BYTES:
        print(f"[WARNING] [{PRINT_PREFIX}] Uploaded file '{filename}' exceeds maximum size limit of {MAX_FILE_SIZE_BYTES} bytes. Rejecting submission.")
        return RedirectResponse(url=STUDENT_SUBMIT_URL.format(assignment_id=assignment_id, slug_name=slug_name), status_code=303)
    if len(submitted_code.encode("utf-8", errors="ignore")) < MIN_FILE_SIZE_BYTES:
        print(f"[WARNING] [{PRINT_PREFIX}] Uploaded file '{filename}' is smaller than minimum size limit of {MIN_FILE_SIZE_BYTES} bytes. Rejecting submission.")
        return RedirectResponse(url=STUDENT_SUBMIT_URL.format(assignment_id=assignment_id, slug_name=slug_name), status_code=303)

    await orchestrate_checks(student.id, assignment_id, slug_name, {filename: submitted_code})

    return RedirectResponse(url=STUDENT_SUBMIT_URL.format(assignment_id=assignment_id, slug_name=slug_name), status_code=303)

    

@router.post("/login", name="student_login_post")
def student_login_post(request: Request, student_id: str = Form(...), student_password: str = Form(...), student_login_token: str = Cookie(None)):
    """Handle student login form submission."""
    try:
        if student_login_token:
            print(f"[INFO] [{PRINT_PREFIX}] Login token found in cookies. Attempting to authenticate student with token: {student_login_token[-5:]}...")
            student = authenticate_student(student_login_token=student_login_token)
            print(f"[INFO] [{PRINT_PREFIX}] Student ID {student.id} already logged in with valid token. Redirecting to home page.")
            return RedirectResponse(url=STUDENT_HOME_URL, status_code=303)
    except HTTPException:
        print(f"[INFO] [{PRINT_PREFIX}] Existing login token invalid. Proceeding with ID/password authentication.")
    
    try:
        print(f"[INFO] [{PRINT_PREFIX}] Received login attempt for student ID: {student_id}")
        student = authenticate_student(student_id=student_id, student_password=student_password)
        new_token = login_tokens.add_login_token(student.id)
        response = RedirectResponse(url=STUDENT_HOME_URL, status_code=303)
        response.set_cookie(key=COOKIE_KEY, value=new_token, httponly=True, max_age=COOKIE_MAX_AGE)
        print(f"[INFO] [{PRINT_PREFIX}] Login successful for student ID: {student_id}. Redirecting to home page.")
        return response
    except HTTPException:
        print(f"[INFO] [{PRINT_PREFIX}] Authentication failed for student ID: {student_id}. Returning to login page.")
        return templates.TemplateResponse(STUDENT_LOGIN_TEMPLATE, {
            "request": request, 
            "error": AUTH_FAILED_MESSAGE,
            "user_data": {"authenticated": False}
            })


