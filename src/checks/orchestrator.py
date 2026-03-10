# src/checks/orchestrator.py

import time
import os
import random
import importlib
from src.db.grader_db.assignments import Assignment
from src.db.grader_db import (
    students,
    assignments,
    submissions,
    slug_completions,
    full_completions,
)
from src.grader.grader import Grader
from src.utils import in_executor
from src.checks import RaisedError

PRINT_PREFIX = "ORCHESTRATOR"

TEMPORARY_DOWNLOAD_DIR = "/tmp/grader_downloads"
os.makedirs(TEMPORARY_DOWNLOAD_DIR, exist_ok=True)

@in_executor
def save_to_tmp(filename: str, content: bytes | str) -> str:
    print(f"[INFO] [{PRINT_PREFIX}] Saving '{filename}' to temp dir.")
    """Save content to a temporary file with a random suffix.
    
    Args:
        filename: Base filename for the temporary file
        content: Content to write to the file, may be bytes or string
        
    Returns:
        Path to the created temporary file
    """
    random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
    temp_filename = f"{filename}_{random_suffix}"
    temp_filepath = os.path.join(TEMPORARY_DOWNLOAD_DIR, temp_filename)
    if isinstance(content, str):
        content = content.encode('utf-8')
    with open(temp_filepath, 'wb') as temp_file:
        temp_file.write(content)
    return temp_filepath


def validate_student_and_assignment(student_id: int, assignment_id: int):
    print(f"[INFO] [{PRINT_PREFIX}] Checking student {student_id} and assignment {assignment_id}.")
    """Validate that student and assignment exist in the database.
    
    Args:
        student_id: ID of the student
        assignment_id: ID of the assignment
        
    Returns:
        Tuple of (student, assignment) if both exist, (None, None) otherwise
    """
    student = students.get_student(student_id)
    if not student:
        print(f"[ERROR] [{PRINT_PREFIX}] Student with ID {student_id} does not exist.")
        return None, None
    assignment = assignments.get_assignment(assignment_id)
    if not assignment:
        print(f"[ERROR] [{PRINT_PREFIX}] Assignment with ID {assignment_id} does not exist.")
        return None, None
    return student, assignment


def create_submission_record(student_id: int, assignment_id: int, slug: str, timestamp: int, submitted_code: str = "") -> submissions.Submission | None:
    print(f"[INFO] [{PRINT_PREFIX}] Creating submission for student {student_id}, assignment {assignment_id}, slug '{slug}'.")
    """Create a new submission record in the database.
    
    Args:
        student_id: ID of the student
        assignment_id: ID of the assignment
        slug: Slug identifier for the assignment part
        timestamp: Submission timestamp
        
    Returns:
        Submission object if successful, None otherwise
    """
    submission_id = submissions.add_submission(
        student_id=student_id,
        assignment_id=assignment_id,
        slug=slug,
        submission_timestamp=timestamp,
        submitted_code=submitted_code,
        grader_output={}
    )
    submission = submissions.get_submission(submission_id)
    
    submission = submissions.get_submission(submission.id)
    if not submission:
        print(f"[ERROR] [{PRINT_PREFIX}] Failed to create submission for student {student_id} and assignment {assignment_id}.")
        return None
    
    return submission


async def setup_grader(student_id: int, assignment__name: str, submitted_files: dict[str, str], timestamp: int, timeout: int):
    print(f"[INFO] [{PRINT_PREFIX}] Setting up grader for student {student_id}, assignment '{assignment__name}'.")
    """Create a grader instance, jail, and place submitted files.
    
    Args:
        student_id: ID of the student
        assignment__name: Name of the assignment
        submitted_files: Dictionary mapping filenames to file contents
        timestamp: Random seed for grader
        timeout: Timeout in seconds for grader execution
        
    Returns:
        Configured Grader instance
    """
    grader = Grader(student_id=student_id, assignment=assignment__name, random_seed=timestamp, timeout=timeout)
    await grader.create_jail()
    
    for filename, content in submitted_files.items():
        temp_filepath = await save_to_tmp(filename, content)
        await grader.place_file_in_jail(source_path=temp_filepath, dest_filename=filename, remove_source=True)
    
    return grader


def load_evaluation_module(assignment: Assignment, slug: str):
    print(f"[INFO] [{PRINT_PREFIX}] Loading evaluation module for assignment '{assignment.directory_name}', slug '{slug}'.")
    """Load and validate the evaluation module for an assignment.
    
    Args:
        assignment: Assignment object containing directory_name
        slug: Which part of the assignment to load
    Returns:
        Evaluation module if valid, None otherwise
    """
    try:
        evaluation_module = importlib.import_module(f"evaluations.{assignment.directory_name}.{slug}")
    except ImportError as e:
        print(f"[ERROR] [{PRINT_PREFIX}] Failed to import evaluation module for '{assignment.directory_name}': {e}")
        return None
    if not hasattr(evaluation_module, 'set_grader'):
        print(f"[ERROR] [{PRINT_PREFIX}] Evaluation module for '{assignment.directory_name}' does not have a set_grader function.")
        return None
    if not hasattr(evaluation_module, 'ALL_TESTS'):
        print(f"[ERROR] [{PRINT_PREFIX}] Evaluation module for '{assignment.directory_name}' does not have an ALL_TESTS list.")
        return None
    return evaluation_module


async def run_tests(ALL_TESTS: list[callable], student_id: int, assignment_id: int):
    print(f"[INFO] [{PRINT_PREFIX}] Running tests for student {student_id}, assignment {assignment_id}.")
    """Execute all tests and collect results.
    
    Args:
        ALL_TESTS: List of test functions to execute
        student_id: ID of the student being graded
        assignment_id: ID of the assignment being graded
        
    Returns:
        Tuple of (results dict, passed_count)
    """
    results = {}
    passed_count = 0
    
    for i, test in enumerate(ALL_TESTS):
        test_name = test.__name__ if hasattr(test, '__name__') else f"test_{i}"
        print(f"[DEBUG] [{PRINT_PREFIX}] Running {test_name} for student {student_id} on assignment {assignment_id}...")
        
        try:
            # Run as await regardless of whether it's a coroutine or not, doesn't affect non-async functions
            result = await test()
            
            results[test_name] = {
                "passed": True if result is True else False,
            }
            if isinstance(result, RaisedError):
                if result.message:
                    results[test_name]["message"] = result.message
                if result.hint:
                    results[test_name]["hint"] = result.hint
                if result.instructions:
                    results[test_name]["instructions"] = result.instructions
                if result.expected_output:
                    results[test_name]["expected_output"] = result.expected_output
                if result.actual_output:
                    results[test_name]["actual_output"] = result.actual_output
                if result.traceback:
                    results[test_name]["traceback"] = result.traceback
                print(f"[ERROR] [{PRINT_PREFIX}] {test_name} FAILED: {result.message}")
            else:
                passed_count += 1
                print(f"[INFO] [{PRINT_PREFIX}] {test_name} PASSED")
        except RaisedError as e:
            results[test_name] = f"FAILED: {e.message}"
            print(f"[ERROR] [{PRINT_PREFIX}] {test_name} FAILED: {e.message}")
        except Exception as e:
            results[test_name] = f"FAILED with uncaught exception: {str(e)}"
            print(f"[ERROR] [{PRINT_PREFIX}] {test_name} FAILED with uncaught exception: {e}")
    
    return results, passed_count


async def compile_grader_output(assignment, student_id: int, slug: str, passed_count: int, total_tests: int, results: dict, grader: Grader) -> dict:
    print(f"[INFO] [{PRINT_PREFIX}] Compiling grader output for student {student_id}, assignment '{assignment.title}', slug '{slug}'.")
    """Compile test results and program output into a formatted report.
    
    Args:
        assignment: Assignment object
        student_id: ID of the student
        slug: Slug identifier
        passed_count: Number of tests passed
        total_tests: Total number of tests
        results: Dictionary of test results
        grader: Grader instance for retrieving output
        
    Returns:
        Formatted grader output string
    """
    grader_output_lines = {
        "assignment": assignment.title,
        "assignment_id": assignment.id,
        "student_id": student_id,
        "slug": slug,
        "tests": results,
        "passed": passed_count,
        "total": total_tests,
        "all_passed": passed_count == total_tests
    }

    output = await grader.get_output()

    grader_output_lines["program_output"] = output or "No output captured."

    return grader_output_lines


def handle_slug_completion(student_id: int, assignment_id: int, slug: str, submission_id: int, timestamp: int, assignment):
    print(f"[INFO] [{PRINT_PREFIX}] Handling slug completion for student {student_id}, assignment {assignment_id}, slug '{slug}'.")
    """Record slug completion and check for full assignment completion.
    
    Args:
        student_id: ID of the student
        assignment_id: ID of the assignment
        slug: Slug that was completed
        submission_id: ID of the submission
        timestamp: Completion timestamp
        assignment: Assignment object with min_completed threshold
    """
    completion_id = slug_completions.add_slug_completion(
        student_id=student_id,
        assignment_id=assignment_id,
        slug=slug,
        submission_id=submission_id,
        completion_timestamp=timestamp
    )
    
    if completion_id:
        print(f"[INFO] [{PRINT_PREFIX}] Student {student_id} completed slug '{slug}' for assignment {assignment_id}")
    else:
        print(f"[INFO] [{PRINT_PREFIX}] Student {student_id} re-submitted already completed slug '{slug}' for assignment {assignment_id}")
    
    slug_completions_for_assignment = slug_completions.get_slug_completions_by_student_and_assignment(student_id, assignment_id)
    if len(slug_completions_for_assignment) >= assignment.min_completed:
        full_completions.create_or_update_completion(
            student_id=student_id,
            assignment_id=assignment_id,
            slugs_completed=[sc.slug for sc in slug_completions_for_assignment],
            submission_ids=[sc.submission_id for sc in slug_completions_for_assignment],
        )
        print(f"[INFO] [{PRINT_PREFIX}] Student {student_id} completed assignment {assignment_id} (total unique slugs: {len(slug_completions_for_assignment)})")

async def orchestrate_checks(student_id: int, assignment_id: int, slug: str, submitted_files: dict[str, str], timeout: int = 10) -> bool:
    print(f"[INFO] [{PRINT_PREFIX}] Orchestrating checks for student {student_id}, assignment {assignment_id}, slug '{slug}'.")
    """Orchestrate the execution of checks for a student submission.
    
    Args:
        student_id: ID of the student
        assignment_id: ID of the assignment
        slug: Slug identifier for the assignment part
        submitted_files: Dictionary mapping filenames to file contents
        timeout: Timeout in seconds for grader execution (default: 10)
        
    Returns:
        True if grading completed successfully, False otherwise
    """
    now = int(time.time())
    
    student, assignment = validate_student_and_assignment(student_id, assignment_id)
    if not student or not assignment:
        print(f"[ERROR] [{PRINT_PREFIX}] Invalid student or assignment.")
        return False
    
    # TODO: FIND A GOOD WAY TO STORE MULTIPLE FILES LOL
    # temporary: grab first file and store that

    submitted_filename, submitted_code = list(submitted_files.items())[0]

    submitted_code_str = f"Filename: {submitted_filename}\nSTART OF SUBMITTED CODE\n\n" + submitted_code + "\n\nEND OF SUBMITTED CODE"
    
    submission = create_submission_record(student_id, assignment_id, slug, now, submitted_code=submitted_code_str)
    if not submission:
        print(f"[ERROR] [{PRINT_PREFIX}] Failed to create submission record.")
        return False

    def _error_output(message: str) -> dict:
        return {
            "assignment": assignment.title,
            "assignment_id": assignment.id,
            "student_id": student_id,
            "slug": slug,
            "tests": {},
            "passed": 0,
            "total": 0,
            "all_passed": False,
            "program_output": message
        }

    grader = None
    try:
        grader = await setup_grader(student_id, assignment.title+"_"+slug, submitted_files, now, timeout)
        print(f"[INFO] [{PRINT_PREFIX}] Grader setup complete.")
        evaluation_module = load_evaluation_module(assignment, slug)
        if not evaluation_module:
            print(f"[ERROR] [{PRINT_PREFIX}] Could not load evaluation module.")
            submission.change_grader_output(_error_output("Could not load evaluation module."))
            grader.cleanup()
            return False
        evaluation_module.set_grader(grader)
        ALL_TESTS = evaluation_module.ALL_TESTS
        results, passed_count = await run_tests(ALL_TESTS, student_id, assignment_id)
        grader_output = await compile_grader_output(
            assignment, student_id, slug, passed_count, len(ALL_TESTS), results, grader
        )
        submission.change_grader_output(grader_output)
        if passed_count == len(ALL_TESTS):
            handle_slug_completion(student_id, assignment_id, slug, submission.id, now, assignment)
        print(f"[INFO] [{PRINT_PREFIX}] Grading complete. Passed: {passed_count}/{len(ALL_TESTS)}.")
        grader.cleanup()
        return True
    except ImportError as e:
        print(f"[ERROR] [{PRINT_PREFIX}] Failed to import evaluation module for '{assignment.directory_name}': {e}")
        submission.change_grader_output(_error_output(f"Failed to import evaluation module: {e}"))
        if grader:
            grader.cleanup()
        return False
    except Exception as e:
        print(f"[ERROR] [{PRINT_PREFIX}] Unexpected error during check orchestration: {e}")
        submission.change_grader_output(_error_output(f"Unexpected error during grading: {e}"))
        if grader:
            grader.cleanup()
        return False