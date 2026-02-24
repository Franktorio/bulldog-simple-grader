"""
Grader-database module that houses all database-related functionality for this specific database.
1. Schema
2. Insertion
3. Queries
4. Updates
"""

from ..connections import connect_db
from .schema import DB_FILE_NAME, SCHEMA # Schema is imported because its used on the db init process

def connect_grader_db():
    """Connect to the grader database."""
    return connect_db(DB_FILE_NAME)

def connect_grader_db_ro():
    """Connect to the grader database in read-only mode."""
    return connect_db(DB_FILE_NAME, read_only=True)

from .students import Student, add_student, get_student, get_all_students, modify_student, delete_student, set_password, verify_password, change_password
from .assignments import Assignment, add_assignment, get_all_assignments, get_assignment, modify_assignment, delete_assignment, get_all_assignments
from .slugs import Slug, add_slug, get_slug, get_slugs_by_assignment, modify_slug, delete_slug
from .submissions import Submission, add_submission, get_submission, get_submissions_by_student, get_submissions_by_assignment, modify_submission, delete_submission, get_submissions_by_student_and_slug
from .slug_completions import SlugCompletion, add_slug_completion, get_slug_completion, get_slug_completions_by_student, get_slug_completions_by_assignment, get_slug_completions_by_student_and_assignment, modify_slug_completion, delete_slug_completion
from .full_completions import FullCompletion, create_or_update_completion, get_completion as get_full_completion, get_completions_by_student as get_full_completions_by_student, get_completions_by_assignment as get_full_completions_by_assignment, get_student_completion_for_assignment, modify_completion as modify_full_completion, delete_completion as delete_full_completion
from .login_tokens import LoginToken, add_login_token, get_login_token, get_tokens_by_student, delete_login_token, delete_all_student_tokens, delete_expired_tokens
from .instructors import Instructor, add_instructor, get_instructor, get_all_instructors, modify_instructor, delete_instructor

__all__ = [
    # Connection functions
    'connect_grader_db',
    'connect_grader_db_ro',
    
    # Students
    'Student',
    'add_student',
    'get_student',
    'get_all_students',
    'modify_student',
    'delete_student',
    'set_password',
    'verify_password',
    'change_password',
    
    # Assignments
    'Assignment',
    'add_assignment',
    'get_assignment',
    'modify_assignment',
    'delete_assignment',
    'get_all_assignments',
    
    # Slugs
    'Slug',
    'add_slug',
    'get_slug',
    'get_slugs_by_assignment',
    'modify_slug',
    'delete_slug',
    
    # Submissions
    'Submission',
    'add_submission',
    'get_submission',
    'get_submissions_by_student',
    'get_submissions_by_assignment',
    'modify_submission',
    'delete_submission',
    
    # Slug Completions
    'SlugCompletion',
    'add_slug_completion',
    'get_slug_completion',
    'get_slug_completions_by_student',
    'get_slug_completions_by_assignment',
    'get_slug_completions_by_student_and_assignment',
    'modify_slug_completion',
    'delete_slug_completion',
    
    # Full Completions
    'FullCompletion',
    'create_or_update_completion',
    'get_full_completion',
    'get_full_completions_by_student',
    'get_full_completions_by_assignment',
    'get_student_completion_for_assignment',
    'modify_full_completion',
    'delete_full_completion',
    
    # Login Tokens
    'LoginToken',
    'add_login_token',
    'get_login_token',
    'get_tokens_by_student',
    'delete_login_token',
    'delete_all_student_tokens',
    'delete_expired_tokens',

    # Instructors
    'Instructor',
    'add_instructor',
    'get_instructor',
    'get_all_instructors',
    'modify_instructor',
    'delete_instructor'
]
