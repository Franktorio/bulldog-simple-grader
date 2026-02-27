import os
from src.checks import check
from src.checks.raised import RaisedError
from src.grader.grader import Grader
from . import test_gen

grader = None

def set_grader(g: Grader) -> None:
    """Set the grader instance for checks."""
    global grader
    grader = g
    test_gen.set_grader(g)


@check
async def file_exists_check():
    """Check if todolist.py exists in the jail."""
    
    # Check if the file exists in the jail (should already be placed by orchestrator)
    if not os.path.isfile(os.path.join(grader.jail_path, "todolist.py")):
        error = RaisedError(
            message="The file 'todolist.py' is missing from the submission.",
            hint="Ensure that you have included 'todolist.py' in your submission."
        )
        error.header = "File Not Found"
        raise error
    return True
    
def run_test_length(length: int):
    @check
    async def test_length_check():
        """Check if the output file has the correct number of tasks."""
        try:
            # Clear output buffers from previous tests
            await grader.clear_output_buffers()
            
            # Generate test for length
            test_files = await test_gen.orchestrate_test_generation("test_input.txt", length)

            # Paths for challenge and solution files
            challenge_file = test_files["output_test_file"]
            sol_file = test_files["output_sol_file"]

            # Place test file in jail
            await grader.place_file_in_jail(challenge_file, "test_input.txt")
            await grader.place_file_in_jail(sol_file, "test_input_sol.txt")
            print()

            # Run student code in the jail
            await grader.execute_in_jail(["python", "todolist.py"])
            await grader.send_input("test_input.txt\n")
            await grader.send_input("output.txt\n")
            
            # Wait for process to complete
            return_code = await grader.wait_for_completion(timeout=3)
            
            if return_code is None:
                error = RaisedError(
                    message=f"todolist.py did not complete within the time limit.",
                    hint="Check for infinite loops or long-running processes in your code."
                )
                error.header = "Timeout Error"
                raise error
            
            if return_code != 0:
                errors = await grader.get_errors()
                error = RaisedError(
                    message=f"todolist.py exited with code {return_code}",
                    hint=f"Check for runtime errors. Error output: {errors}"
                )
                error.header = "Runtime Error"
                raise error

            # Compare if output is the same as the solution file
            with open(os.path.join(grader.jail_path, "output.txt")) as student_output_file:
                student_output = student_output_file.read()

            with open(os.path.join(grader.jail_path, "test_input_sol.txt")) as expected_output_file:
                expected_output = expected_output_file.read()

            if student_output != expected_output:
                print(f"[DEBUG] Expected output ({len(expected_output)} chars):")
                print(repr(expected_output[:200]))
                print(f"[DEBUG] Student output ({len(student_output)} chars):")
                print(repr(student_output[:200]))
                error = RaisedError(
                    message="The output does not match the expected solution.",
                    hint="Check your program's output against the expected output.",
                    expected_output=expected_output[:200] + ("... (first 200 characters)" if len(expected_output) > 200 else ""),
                    actual_output=student_output[:200] + ("... (first 200 characters)" if len(student_output) > 200 else "")
                )
                error.header = "Output Mismatch"
                raise error
            return True
        except RaisedError as e:
            raise e
        except Exception as e:
            error = RaisedError(
                message=f"An error occurred while executing the student's code: {e}",
                hint="Ensure your code runs without errors and produces the correct output."
            )
            error.header = "Execution Error"
            raise error
        
    test_length_check.__name__ = f"test_length_{length}"
    return test_length_check

ALL_TESTS = [
    file_exists_check,
    run_test_length(5),
    run_test_length(10),
    run_test_length(50),
    run_test_length(200)
]