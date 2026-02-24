# src/frontend/api/student/constants.py
# Constants for the student API module

# Template names
STUDENT_LOGIN_TEMPLATE = "student-login.html"
STUDENT_HOME_TEMPLATE = "student-home.html"
STUDENT_ASSIGNMENT_TEMPLATE = "student-assignment.html"
STUDENT_SUBMIT_TEMPLATE = "student-submit.html"

# Authentication constants
AUTH_FAILED_MESSAGE = "Invalid ID or password"
COOKIE_KEY = "student_login_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 1 week expiration

# Logging prefix
PRINT_PREFIX = "API - STUDENTS"

# Redirect URLs
STUDENT_LOGIN_URL = "/students/login"
STUDENT_HOME_URL = "/students/home"
STUDENT_ASSIGNMENT_URL = "/students/assignments/{assignment_id}"
STUDENT_SUBMIT_URL = "/students/assignments/{assignment_id}/{slug_name}"
