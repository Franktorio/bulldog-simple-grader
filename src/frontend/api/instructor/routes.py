# src/frontend/api/instructor/routes.py
# Routes for the instructor API module

import datetime
from fastapi import APIRouter, HTTPException, Cookie, Request, Form, Depends, UploadFile
from src.db.grader_db import login_tokens, instructors, helpers, add_assignment, add_student, get_assignment, modify_assignment
from src.db.grader_db.login_tokens import delete_login_token
from fastapi.responses import RedirectResponse
from src.frontend.api.paths import templates
from .authentication import authenticate_instructor
from .constants import (
    AUTH_FAILED_MESSAGE,
    COOKIE_KEY,
    COOKIE_MAX_AGE,
    PRINT_PREFIX,
    INSTRUCTOR_LOGIN_TEMPLATE,
    INSTRUCTOR_LOGIN_URL,
    INSTRUCTOR_HOME_URL,
    INSTRUCTOR_HOME_TEMPLATE,
    INSTRUCTOR_ADD_ASSIGNMENT_TEMPLATE,
    INSTRUCTOR_ADD_STUDENT_TEMPLATE,
    INSTRUCTOR_SEE_ASSIGNMENT_TEMPLATE,
    INSTRUCTOR_SEE_SUBMISSIONS_TEMPLATE,
    INSTRUCTOR_SEE_COMPLETIONS_TEMPLATE,
    INSTRUCTOR_SEE_STUDENT_TEMPLATE,
    INSTRUCTOR_SEE_STUDENT_SUBMISSIONS_TEMPLATE,
    INSTRUCTOR_SEE_STUDENT_ASSIGNMENT_SUBMISSIONS_TEMPLATE,
    INSTRUCTOR_SEE_ASSIGNMENT_URL,
    INSTRUCTOR_TOGGLE_ASSIGNMENT_ACTIVE_URL,
    INSTRUCTOR_SEE_STUDENT_URL,
)

router = APIRouter(prefix="/instructors", tags=["instructors"])


def get_authenticated_instructor(instructor_login_token: str = Cookie(None)) -> instructors.Instructor:
    """Dependency to get authenticated instructor from cookie token.

    Raises:
        HTTPException: 401 if authentication fails
    """
    if not instructor_login_token:
        print(f"[INFO] [{PRINT_PREFIX}] No login token found in cookies.")
        raise HTTPException(status_code=400, detail="Not authenticated")

    print(f"[INFO] [{PRINT_PREFIX}] Attempting to authenticate instructor with login token: {instructor_login_token[-5:]}...")
    try:
        instructor = authenticate_instructor(instructor_login_token=instructor_login_token)
        print(f"[INFO] [{PRINT_PREFIX}] Successfully authenticated instructor ID {instructor.id}.")
        return instructor
    except HTTPException:
        print(f"[INFO] [{PRINT_PREFIX}] Authentication failed for token: {instructor_login_token[-5:]}.")
        raise HTTPException(status_code=400, detail="Invalid authentication")

@router.get("/login", name="instructor_login")
def instructor_login(request: Request, instructor_login_token: str = Cookie(None)):
    """Display the login page or redirect to home if already authenticated."""
    if instructor_login_token:
        try:
            print(f"[INFO] [{PRINT_PREFIX}] Login token found in cookies. Attempting to authenticate instructor with token: {instructor_login_token[-5:]}...")
            instructor = authenticate_instructor(instructor_login_token=instructor_login_token)
            print(f"[INFO] [{PRINT_PREFIX}] Instructor ID {instructor.id} already logged in with valid token. Redirecting to home page.")
            return RedirectResponse(url=INSTRUCTOR_HOME_URL, status_code=303)
        except HTTPException:
            print(f"[INFO] [{PRINT_PREFIX}] Existing login token invalid. Proceeding to login page.")

    user_data = {
        "authenticated": False
    }
    return templates.TemplateResponse(INSTRUCTOR_LOGIN_TEMPLATE, {"request": request, "user_data": user_data})

@router.get("/home", name="instructor_home")
def instructor_home(request: Request, instructor: instructors.Instructor = Depends(get_authenticated_instructor)):
    """Display the instructor home page."""
    user_data = {
        "authenticated": True,
        "id": instructor.id,
        "name": instructor.name,
        **helpers.get_instructor_homepage_data()
    }
    return templates.TemplateResponse(INSTRUCTOR_HOME_TEMPLATE, {"request": request, "user_data": user_data})

@router.post("/login", name="instructor_login_post")
def instructor_login_post(request: Request, instructor_id: str = Form(...), instructor_password: str = Form(...), instructor_login_token: str = Cookie(None)):
    """Handle instructor login form submission."""
    try:
        if instructor_login_token:
            print(f"[INFO] [{PRINT_PREFIX}] Login token found in cookies. Attempting to authenticate instructor with token: {instructor_login_token[-5:]}...")
            instructor = authenticate_instructor(instructor_login_token=instructor_login_token)
            print(f"[INFO] [{PRINT_PREFIX}] Instructor ID {instructor.id} already logged in with valid token. Redirecting to home page.")
            return RedirectResponse(url=INSTRUCTOR_HOME_URL, status_code=303)
    except HTTPException:
        print(f"[INFO] [{PRINT_PREFIX}] Existing login token invalid. Proceeding with ID/password authentication.")

    try:
        print(f"[INFO] [{PRINT_PREFIX}] Received login attempt for instructor ID: {instructor_id}")
        instructor = authenticate_instructor(instructor_id=instructor_id, instructor_password=instructor_password)
        new_token = login_tokens.add_login_token(instructor_id=instructor.id)
        response = RedirectResponse(url=INSTRUCTOR_HOME_URL, status_code=303)
        response.set_cookie(key=COOKIE_KEY, value=new_token, httponly=True, max_age=COOKIE_MAX_AGE)
        print(f"[INFO] [{PRINT_PREFIX}] Login successful for instructor ID: {instructor_id}. Redirecting to home page.")
        return response
    except HTTPException:
        print(f"[INFO] [{PRINT_PREFIX}] Authentication failed for instructor ID: {instructor_id}. Returning to login page.")
        return templates.TemplateResponse(
            INSTRUCTOR_LOGIN_TEMPLATE,
            {
                "request": request,
                "error": AUTH_FAILED_MESSAGE,
                "user_data": {"authenticated": False}
            }
        )


@router.post("/logout", name="instructor_logout_post")
def instructor_logout_post(instructor_login_token: str = Cookie(None)):
    """Handle instructor logout by removing token from database and clearing cookie."""
    if instructor_login_token:
        success = delete_login_token(instructor_login_token)
        if success:
            print(f"[INFO] [{PRINT_PREFIX}] Successfully logged out instructor with token: {instructor_login_token[-5:]}")
        else:
            print(f"[WARNING] [{PRINT_PREFIX}] Failed to delete login token during logout: {instructor_login_token[-5:]}")
    else:
        print(f"[INFO] [{PRINT_PREFIX}] No login token found in cookies during logout attempt.")
    
    response = RedirectResponse(url=INSTRUCTOR_LOGIN_URL, status_code=303)
    response.delete_cookie(key=COOKIE_KEY)
    return response


# === ASSIGNMENT ROUTES ===

@router.get("/assignments/{assignment_id}", name="instructor_see_assignment")
def instructor_see_assignment(request: Request, assignment_id: int, instructor: instructors.Instructor = Depends(get_authenticated_instructor)):
    """Display detail page for a specific assignment."""
    data = helpers.get_instructor_assignment_page_data(assignment_id)
    if not data:
        print(f"[WARNING] [{PRINT_PREFIX}] Assignment ID {assignment_id} not found.")
        raise HTTPException(status_code=404, detail="Assignment not found")
    user_data = {
        "authenticated": True,
        "id": instructor.id,
        "name": instructor.name,
        **data
    }
    return templates.TemplateResponse(INSTRUCTOR_SEE_ASSIGNMENT_TEMPLATE, {"request": request, "user_data": user_data})


@router.post("/assignments/{assignment_id}/toggle-active", name="instructor_toggle_assignment_active")
def instructor_toggle_assignment_active(request: Request, assignment_id: int, instructor: instructors.Instructor = Depends(get_authenticated_instructor)):
    """Toggle the is_active status of a specific assignment."""
    assignment = get_assignment(assignment_id)
    if not assignment:
        print(f"[WARNING] [{PRINT_PREFIX}] Assignment ID {assignment_id} not found for toggle-active.")
        raise HTTPException(status_code=404, detail="Assignment not found")
    modify_assignment(assignment_id, is_active=not assignment.is_active)
    print(f"[INFO] [{PRINT_PREFIX}] Instructor {instructor.id} toggled assignment {assignment_id} active status to {not assignment.is_active}.")
    return RedirectResponse(url=INSTRUCTOR_SEE_ASSIGNMENT_URL.format(assignment_id=assignment_id), status_code=303)


@router.get("/assignments/{assignment_id}/submissions", name="instructor_see_submissions")
def instructor_see_submissions(request: Request, assignment_id: int, instructor: instructors.Instructor = Depends(get_authenticated_instructor)):
    """Display all submissions for a specific assignment."""
    data = helpers.get_instructor_assignment_submissions(assignment_id)
    if not data:
        print(f"[WARNING] [{PRINT_PREFIX}] Assignment ID {assignment_id} not found for submissions view.")
        raise HTTPException(status_code=404, detail="Assignment not found")
    user_data = {
        "authenticated": True,
        "id": instructor.id,
        "name": instructor.name,
        **data
    }
    return templates.TemplateResponse(INSTRUCTOR_SEE_SUBMISSIONS_TEMPLATE, {"request": request, "user_data": user_data})


@router.get("/assignments/{assignment_id}/completions", name="instructor_see_completions")
def instructor_see_completions(request: Request, assignment_id: int, instructor: instructors.Instructor = Depends(get_authenticated_instructor)):
    """Display all completions for a specific assignment."""
    data = helpers.get_instructor_assignment_completions(assignment_id)
    if not data:
        print(f"[WARNING] [{PRINT_PREFIX}] Assignment ID {assignment_id} not found for completions view.")
        raise HTTPException(status_code=404, detail="Assignment not found")
    user_data = {
        "authenticated": True,
        "id": instructor.id,
        "name": instructor.name,
        **data
    }
    return templates.TemplateResponse(INSTRUCTOR_SEE_COMPLETIONS_TEMPLATE, {"request": request, "user_data": user_data})


@router.get("/add-assignment", name="instructor_add_assignment")
def instructor_add_assignment(request: Request, instructor: instructors.Instructor = Depends(get_authenticated_instructor)):
    """Display the add assignment form."""
    user_data = {
        "authenticated": True,
        "id": instructor.id,
        "name": instructor.name,
    }
    return templates.TemplateResponse(INSTRUCTOR_ADD_ASSIGNMENT_TEMPLATE, {"request": request, "user_data": user_data})


@router.post("/add-assignment", name="instructor_add_assignment_post")
def instructor_add_assignment_post(
    request: Request,
    title: str = Form(...),
    directory_name: str = Form(...),
    slugs: str = Form(...),
    min_completed: int = Form(...),
    due_date: str = Form(""),
    is_active: str = Form("off"),
    instructor: instructors.Instructor = Depends(get_authenticated_instructor)
):
    """Handle the add assignment form submission."""
    slug_list = [s.strip() for s in slugs.split(",") if s.strip()]
    due_date_timestamp = None
    if due_date:
        try:
            dt = datetime.datetime.fromisoformat(due_date)
            due_date_timestamp = int(dt.timestamp())
        except Exception:
            due_date_timestamp = None
    active = (is_active == "on")

    try:
        assignment_id = add_assignment(
            title=title,
            directory_name=directory_name,
            slugs=slug_list,
            min_completed=min_completed,
            due_date_timestamp=due_date_timestamp,
            is_active=active
        )
        print(f"[INFO] [{PRINT_PREFIX}] Instructor {instructor.id} created assignment '{title}' with ID {assignment_id}.")
        return RedirectResponse(url=INSTRUCTOR_SEE_ASSIGNMENT_URL.format(assignment_id=assignment_id), status_code=303)
    except Exception as e:
        print(f"[ERROR] [{PRINT_PREFIX}] Failed to create assignment: {e}")
        return templates.TemplateResponse(
            INSTRUCTOR_ADD_ASSIGNMENT_TEMPLATE,
            {
                "request": request,
                "error": "Failed to create assignment. Please check your inputs.",
                "user_data": {"authenticated": True, "id": instructor.id, "name": instructor.name}
            }
        )


# === STUDENT ROUTES ===

@router.get("/students/{student_id}", name="instructor_see_student")
def instructor_see_student(request: Request, student_id: int, instructor: instructors.Instructor = Depends(get_authenticated_instructor)):
    """Display detail page for a specific student."""
    data = helpers.get_instructor_student_page_data(student_id)
    if not data:
        print(f"[WARNING] [{PRINT_PREFIX}] Student ID {student_id} not found.")
        raise HTTPException(status_code=404, detail="Student not found")
    user_data = {
        "authenticated": True,
        "id": instructor.id,
        "name": instructor.name,
        **data
    }
    return templates.TemplateResponse(INSTRUCTOR_SEE_STUDENT_TEMPLATE, {"request": request, "user_data": user_data})


@router.get("/students/{student_id}/submissions", name="instructor_see_student_submissions")
def instructor_see_student_submissions(request: Request, student_id: int, instructor: instructors.Instructor = Depends(get_authenticated_instructor)):
    """Display all submissions by a specific student."""
    data = helpers.get_instructor_student_submissions(student_id)
    if not data:
        print(f"[WARNING] [{PRINT_PREFIX}] Student ID {student_id} not found for submissions view.")
        raise HTTPException(status_code=404, detail="Student not found")
    user_data = {
        "authenticated": True,
        "id": instructor.id,
        "name": instructor.name,
        **data
    }
    return templates.TemplateResponse(INSTRUCTOR_SEE_STUDENT_SUBMISSIONS_TEMPLATE, {"request": request, "user_data": user_data})


@router.get("/students/{student_id}/assignments/{assignment_id}/submissions", name="instructor_see_student_assignment_submissions")
def instructor_see_student_assignment_submissions(request: Request, student_id: int, assignment_id: int, instructor: instructors.Instructor = Depends(get_authenticated_instructor)):
    """Display submissions by a specific student for a specific assignment."""
    data = helpers.get_instructor_student_assignment_submissions(student_id, assignment_id)
    if not data:
        print(f"[WARNING] [{PRINT_PREFIX}] Student ID {student_id} or assignment ID {assignment_id} not found.")
        raise HTTPException(status_code=404, detail="Student or assignment not found")
    user_data = {
        "authenticated": True,
        "id": instructor.id,
        "name": instructor.name,
        **data
    }
    return templates.TemplateResponse(INSTRUCTOR_SEE_STUDENT_ASSIGNMENT_SUBMISSIONS_TEMPLATE, {"request": request, "user_data": user_data})


@router.get("/add-student", name="instructor_add_student")
def instructor_add_student(request: Request, instructor: instructors.Instructor = Depends(get_authenticated_instructor)):
    """Display the add student form."""
    user_data = {
        "authenticated": True,
        "id": instructor.id,
        "name": instructor.name,
    }
    return templates.TemplateResponse(INSTRUCTOR_ADD_STUDENT_TEMPLATE, {"request": request, "user_data": user_data})


@router.post("/add-student", name="instructor_add_student_post")
def instructor_add_student_post(
    request: Request,
    student_id: int = Form(...),
    student_name: str = Form(...),
    password: str = Form(...),
    instructor: instructors.Instructor = Depends(get_authenticated_instructor)
):
    """Handle the add student form submission."""
    try:
        add_student(student_id=student_id, name=student_name, password=password)
        print(f"[INFO] [{PRINT_PREFIX}] Instructor {instructor.id} added student '{student_name}' with ID {student_id}.")
        return RedirectResponse(url=INSTRUCTOR_SEE_STUDENT_URL.format(student_id=student_id), status_code=303)
    except Exception as e:
        print(f"[ERROR] [{PRINT_PREFIX}] Failed to add student: {e}")
        return templates.TemplateResponse(
            INSTRUCTOR_ADD_STUDENT_TEMPLATE,
            {
                "request": request,
                "error": "Failed to add student. The student ID may already be taken.",
                "user_data": {"authenticated": True, "id": instructor.id, "name": instructor.name}
            }
        )
