# src/frontend/api/instructor/constants.py
# Constants for the instructor API module

# Template names

# Authentication constants
AUTH_FAILED_MESSAGE = "Invalid ID or password"
COOKIE_KEY = "instructor_login_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 1 week expiration

# Logging prefix
PRINT_PREFIX = "API - INSTRUCTORS"

# Template names
INSTRUCTOR_LOGIN_TEMPLATE = "instructor-login.html"
INSTRUCTOR_HOME_TEMPLATE = "instructor-home.html"
INSTRUCTOR_ADD_ASSIGNMENT_TEMPLATE = "instructor-add-assignment.html"
INSTRUCTOR_ADD_STUDENT_TEMPLATE = "instructor-add-student.html"
INSTRUCTOR_SEE_ASSIGNMENT_TEMPLATE = "instructor-see-assignment.html"
INSTRUCTOR_SEE_SUBMISSIONS_TEMPLATE = "instructor-see-submissions.html"
INSTRUCTOR_SEE_COMPLETIONS_TEMPLATE = "instructor-see-completions.html"
INSTRUCTOR_SEE_STUDENT_TEMPLATE = "instructor-see-student.html"
INSTRUCTOR_SEE_STUDENT_SUBMISSIONS_TEMPLATE = "instructor-see-student-submissions.html"
INSTRUCTOR_SEE_STUDENT_ASSIGNMENT_SUBMISSIONS_TEMPLATE = "instructor-see-student-assignment-submissions.html"

# Redirect URLs
INSTRUCTOR_LOGIN_URL = "/instructors/login"
INSTRUCTOR_HOME_URL = "/instructors/home"
INSTRUCTOR_ADD_ASSIGNMENT_URL = "/instructors/add-assignment"
INSTRUCTOR_ADD_STUDENT_URL = "/instructors/add-student"
INSTRUCTOR_SEE_ASSIGNMENT_URL = "/instructors/assignments/{assignment_id}"
INSTRUCTOR_TOGGLE_ASSIGNMENT_ACTIVE_URL = "/instructors/assignments/{assignment_id}/toggle-active"
INSTRUCTOR_SEE_SUBMISSIONS_URL = "/instructors/assignments/{assignment_id}/submissions"
INSTRUCTOR_SEE_COMPLETIONS_URL = "/instructors/assignments/{assignment_id}/completions"
INSTRUCTOR_SEE_STUDENT_URL = "/instructors/students/{student_id}"
INSTRUCTOR_SEE_STUDENT_SUBMISSIONS_URL = "/instructors/students/{student_id}/submissions"