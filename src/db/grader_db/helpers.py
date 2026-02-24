from src.db.grader_db.students import Student, get_all_students
from src.utils import format_datetime
from . import (
    assignments,
    full_completions,
    slug_completions,
    slugs, submissions,
    get_submissions_by_student_and_slug,
    get_all_students,
    get_all_assignments,
    get_student,
    get_submissions_by_student,
    get_submissions_by_assignment,
    Student
)

# === STUDENT HELPERS ===

def get_all_assignments_in_perspective_of_student(student_id: int) -> dict[int, dict[assignments.Assignment, bool, list[slug_completions.SlugCompletion]]]:
    """Get all assignments with completion status for a specific student."""
    all_assignments = assignments.get_all_assignments(include_due=True, only_active=True)
    student_full_completions = full_completions.get_completions_by_student(student_id)
    student_slug_completions = slug_completions.get_slug_completions_by_student(student_id)

    # Organize all assignments by due date and include completion status
    assignments_by_due_date = list(sorted(all_assignments, key=lambda a: a.due_date_timestamp or float('inf')))

    assignment_map = {
        assignment.id: {
            "assignment": assignment,
            "is_completed": any(c.assignment_id == assignment.id for c in student_full_completions),
            "requirements": f"{len(assignment.slugs) if assignment.slugs else 0} problems available, {assignment.min_completed} minimum for completion",
            "progress": f"You have completed {len([sc for sc in student_slug_completions if sc.assignment_id == assignment.id])} out of {assignment.min_completed}"
        }
        for assignment in assignments_by_due_date
    }

    return assignment_map

def get_assignment_from_student_perspective(student_id: int, assignment_id: int) -> dict[assignments.Assignment, bool, list[slug_completions.SlugCompletion]] | None:
    """Get a specific assignment with completion status for a specific student."""
    assignment = assignments.get_assignment(assignment_id)
    if not assignment:
        return None

    slugs_available = slugs.get_slugs_by_assignment(assignment_id)
    student_full_completion = full_completions.get_student_completion_for_assignment(student_id, assignment_id)
    student_slug_completions = slug_completions.get_slug_completions_by_student_and_assignment(student_id, assignment_id)

    return {
        "assignment": assignment,
        "is_completed": student_full_completion is not None,
        "requirements": f"{len(slugs_available)} problems available, {assignment.min_completed} minimum for completion",
        "progress": f"You have completed {len(student_slug_completions)} out of {assignment.min_completed}",
        "slugs_available": slugs_available,
        "slugs_completed": student_slug_completions
    }

def get_submissions_for_student_slug(student_id: int, slug_name: str) -> list[dict]:
    """Get all submissions for a specific student, assignment and slug."""

    slug_submissions = get_submissions_by_student_and_slug(student_id, slug_name)

    def _dict_submission(submission: submissions.Submission) -> dict:
        return {
            "id": submission.id,
            "student_id": submission.student_id,
            "assignment_id": submission.assignment_id,
            "slug": submission.slug,
            "submission_timestamp": format_datetime(submission.submission_timestamp),
            "submitted_code": submission.submitted_code,
            "grader_output": submission.grader_output
        }
    
    if not slug_submissions:
        return []
    
    return [_dict_submission(s) for s in slug_submissions[:10]]  # Limit to last 10 submissions for this slug


# === INSTRUCTOR HELPERS ===

def get_instructor_homepage_data() -> dict:
    """Get data for the instructor homepage: A list of students and all assignments with completion stats."""
    
    all_students = get_all_students()
    all_assignments = get_all_assignments(include_due=True, only_active=False)

    def _dict_student(student: Student) -> dict:
        return {
            "id": student.id,
            "name": student.name
        }
    
    def _dict_assignment(assignment: assignments.Assignment) -> dict:
        return {
            "id": assignment.id,
            "title": assignment.title,
            "directory_name": assignment.directory_name,
            "slugs": assignment.slugs,
            "min_completed": assignment.min_completed,
            "due_date_timestamp": format_datetime(assignment.due_date_timestamp) if assignment.due_date_timestamp else None,
            "is_active": assignment.is_active
        }

    students_data = [_dict_student(s) for s in all_students]
    assignments_data = [_dict_assignment(a) for a in all_assignments]

    return {
        "students": students_data,
        "assignments": assignments_data
    }


def get_instructor_assignment_page_data(assignment_id: int) -> dict | None:
    """Get detailed data for a single assignment page: assignment info, slugs, and per-student completion."""
    assignment = assignments.get_assignment(assignment_id)
    if not assignment:
        return None

    slugs_available = slugs.get_slugs_by_assignment(assignment_id)
    all_students = get_all_students()
    assignment_full_completions = full_completions.get_completions_by_assignment(assignment_id)
    assignment_slug_completions = slug_completions.get_slug_completions_by_assignment(assignment_id)

    students_data = []
    for student in all_students:
        full_completion = next((c for c in assignment_full_completions if c.student_id == student.id), None)
        student_slug_completions = [sc for sc in assignment_slug_completions if sc.student_id == student.id]
        students_data.append({
            "id": student.id,
            "name": student.name,
            "is_completed": full_completion is not None,
            "slugs_completed": [sc.slug for sc in student_slug_completions],
            "completed_count": len(student_slug_completions)
        })

    return {
        "assignment": {
            "id": assignment.id,
            "title": assignment.title,
            "directory_name": assignment.directory_name,
            "slugs": assignment.slugs,
            "min_completed": assignment.min_completed,
            "due_date_timestamp": format_datetime(assignment.due_date_timestamp) if assignment.due_date_timestamp else None,
            "is_active": assignment.is_active
        },
        "slugs_available": [{"name": s.name} for s in slugs_available],
        "students": students_data
    }


def get_instructor_assignment_submissions(assignment_id: int) -> dict | None:
    """Get all submissions for a given assignment for the instructor view."""
    assignment = assignments.get_assignment(assignment_id)
    if not assignment:
        return None

    all_students = get_all_students()
    student_map = {s.id: s.name for s in all_students}
    raw_submissions = get_submissions_by_assignment(assignment_id)

    submissions_data = []
    for sub in raw_submissions:
        submissions_data.append({
            "id": sub.id,
            "student_id": sub.student_id,
            "student_name": student_map.get(sub.student_id, f"Student {sub.student_id}"),
            "slug": sub.slug,
            "submission_timestamp": format_datetime(sub.submission_timestamp),
            "grader_output": sub.grader_output
        })

    return {
        "assignment": {
            "id": assignment.id,
            "title": assignment.title,
            "is_active": assignment.is_active
        },
        "submissions": submissions_data
    }


def get_instructor_assignment_completions(assignment_id: int) -> dict | None:
    """Get all full completions for a given assignment for the instructor view."""
    assignment = assignments.get_assignment(assignment_id)
    if not assignment:
        return None

    all_students = get_all_students()
    student_map = {s.id: s.name for s in all_students}
    raw_completions = full_completions.get_completions_by_assignment(assignment_id)

    completions_data = []
    for c in raw_completions:
        completions_data.append({
            "id": c.id,
            "student_id": c.student_id,
            "student_name": student_map.get(c.student_id, f"Student {c.student_id}"),
            "slugs_completed": c.slugs_completed,
            "completion_timestamp": format_datetime(c.completion_timestamp)
        })

    completed_student_ids = {c.student_id for c in raw_completions}
    not_completed = [
        {"id": s.id, "name": s.name}
        for s in all_students
        if s.id not in completed_student_ids
    ]

    return {
        "assignment": {
            "id": assignment.id,
            "title": assignment.title,
            "min_completed": assignment.min_completed,
            "is_active": assignment.is_active
        },
        "completions": completions_data,
        "not_completed": not_completed
    }


def get_instructor_student_page_data(student_id: int) -> dict | None:
    """Get detailed data for a single student page: student info and per-assignment progress."""
    student = get_student(student_id)
    if not student:
        return None

    all_assignments_list = get_all_assignments(include_due=True, only_active=False)
    student_full_completions = full_completions.get_completions_by_student(student_id)
    student_slug_completions_list = slug_completions.get_slug_completions_by_student(student_id)

    assignments_data = []
    for assignment in all_assignments_list:
        full_completion = next((c for c in student_full_completions if c.assignment_id == assignment.id), None)
        this_slug_completions = [sc for sc in student_slug_completions_list if sc.assignment_id == assignment.id]
        assignments_data.append({
            "id": assignment.id,
            "title": assignment.title,
            "is_active": assignment.is_active,
            "due_date_timestamp": format_datetime(assignment.due_date_timestamp) if assignment.due_date_timestamp else None,
            "min_completed": assignment.min_completed,
            "total_slugs": len(assignment.slugs) if assignment.slugs else 0,
            "is_completed": full_completion is not None,
            "slugs_completed": [sc.slug for sc in this_slug_completions],
            "completed_count": len(this_slug_completions)
        })

    return {
        "student": {
            "id": student.id,
            "name": student.name
        },
        "assignments": assignments_data
    }


def get_instructor_student_submissions(student_id: int) -> dict | None:
    """Get all submissions by a student for the instructor view."""
    student = get_student(student_id)
    if not student:
        return None

    raw_submissions = get_submissions_by_student(student_id)

    submissions_data = []
    for sub in raw_submissions:
        submissions_data.append({
            "id": sub.id,
            "assignment_id": sub.assignment_id,
            "slug": sub.slug,
            "submission_timestamp": format_datetime(sub.submission_timestamp),
            "grader_output": sub.grader_output,
            "submitted_code": sub.submitted_code
        })

    return {
        "student": {
            "id": student.id,
            "name": student.name
        },
        "submissions": submissions_data
    }


def get_instructor_student_assignment_submissions(student_id: int, assignment_id: int) -> dict | None:
    """Get submissions by a student filtered to a specific assignment."""
    student = get_student(student_id)
    if not student:
        return None
    assignment = assignments.get_assignment(assignment_id)
    if not assignment:
        return None

    raw_submissions = submissions.get_submissions_by_student_and_assignment(student_id, assignment_id)

    submissions_data = []
    for sub in raw_submissions:
        submissions_data.append({
            "id": sub.id,
            "assignment_id": sub.assignment_id,
            "slug": sub.slug,
            "submission_timestamp": format_datetime(sub.submission_timestamp),
            "grader_output": sub.grader_output,
            "submitted_code": sub.submitted_code
        })

    return {
        "student": {
            "id": student.id,
            "name": student.name
        },
        "assignment": {
            "id": assignment.id,
            "title": assignment.title
        },
        "submissions": submissions_data
    }
