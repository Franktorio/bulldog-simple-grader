from src.checks import check
from src.checks.raised import RaisedError
from src.grader.grader import Grader
import os

grader = None

CORRECT_SUMMARY_PATH = os.path.join(os.path.dirname(__file__), "correct_summary.txt")


def set_grader(g: Grader) -> None:
    global grader
    grader = g

@check
async def sales_py_exists():
    """Check if sales.py exists in the jail."""
    
    # Check if the file exists in the jail (should already be placed by orchestrator)
    if not os.path.isfile(os.path.join(grader.jail_path, "sales.py")):
        error = RaisedError(
            message="The file 'sales.py' is missing from the submission.",
            hint="Ensure that you have included 'sales.py' in your submission."
        )
        error.header = "File Not Found"
        raise error
    return True

@check
async def sales_py_runs():
    """Check if sales.py runs without errors."""
    try:
        await grader.execute_in_jail(["python", "sales.py"])
        return_code = await grader.wait_for_completion(timeout=3)
        if return_code != 0:
            error = RaisedError(
                message=f"sales.py did not run successfully. Return code: {return_code}",
                hint="Check your code for errors and ensure it runs without issues."
            )
            error.header = "Execution Error"
            raise error
        return True
    except Exception as e:
        error = RaisedError(
            message=f"An error occurred while running sales.py: {str(e)}",
            hint="Check your code for errors and ensure it runs without issues."
        )
        error.header = "Execution Error"
        raise error

@check
async def summary_txt_exists():
    """Check if summary.txt was created in the jail."""
    summary_path = os.path.join(grader.jail_path, "summary.txt")
    if not os.path.isfile(summary_path):
        error = RaisedError(
            message="The file 'summary.txt' was not created by sales.py.",
            hint="Ensure that your code creates 'summary.txt' with the correct content."
        )
        error.header = "Output Not Found"
        raise error
    return True

@check
async def correct_summary():
    """Check if summary.txt contains the correct summary."""
    summary_path = os.path.join(grader.jail_path, "summary.txt")
    check_summary_path = os.path.join(os.path.dirname(__file__), "check_summary.txt")

    with open(summary_path) as student_file, open(CORRECT_SUMMARY_PATH) as correct_file:
        student_output = student_file.read().strip()
        expected_output = correct_file.read().strip()

        if student_output != expected_output:
            error = RaisedError(
                message="The summary.txt content does not match the expected summary.",
                hint="Check your code's output against the expected summary.",
                expected_output="No output provided", # Hide expected output
                actual_output=student_output
            )
            error.header = "Output Mismatch"
            raise error
    return True

ALL_TESTS = [sales_py_exists, sales_py_runs, summary_txt_exists, correct_summary]  # Required: list of all test functions