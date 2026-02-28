# src/grader/grader.py
# Orchestrates the grading process using the Jailer to safely execute code.

import os
import random
import asyncio
import time
from src.grader.jailer import Jailer
from src.utils import in_executor

PRINT_PREFIX = "GRADER"
TIMEOUT: str = "TIMEOUT"

class Grader:
    def __init__(self, student_id: str, assignment: str, random_seed: int = 42, timeout: int = 10):
        self.jailer = Jailer(student_id=student_id, assignment=assignment, timeout=timeout)
        self.jail_path = None
        self.random = random.Random(random_seed)

    async def create_jail(self) -> str:
        """Create the jail directory for this grader."""
        self.jail_path = await self.jailer.create_jail()
        return self.jail_path

    @in_executor
    def submit_code(self, code: str, filename: str) -> None:
        """Submit code to be graded."""
        # Save code to a file in the jail
        code_file_path = f"{self.jail_path}/{filename}"
        with open(code_file_path, "w") as code_file:
            code_file.write(code)
        print(f"[INFO] [{PRINT_PREFIX}] Code submitted to {code_file_path}")

    @in_executor
    def place_file_in_jail(self, source_path: str, dest_filename: str, remove_source: bool = True) -> None:
        """Place an external file into the jail."""
        dest_path = f"{self.jail_path}/{dest_filename}"
        with open(source_path, "r") as src_file:
            with open(dest_path, "w") as dest_file:
                dest_file.write(src_file.read())
        if remove_source:
            os.remove(source_path)
        print(f"[INFO] [{PRINT_PREFIX}] Placed file {source_path} into jail at {dest_path}")

    @in_executor
    def run_check(self, check: callable) -> dict:
        """Run a single check function and return its result."""
        check_result = check()  # Will either be True or a RaisedError
        if check_result != True:
            print(f"[INFO] [{PRINT_PREFIX}] Check {check.__name__} failed with error: {check_result}")
            result = {
                "header": check_result.header,
                "message": check_result.message,
                "hint": check_result.hint,
                "instructions": check_result.instructions
            }
            if hasattr(check_result, "expected") and hasattr(check_result, "actual"):
                result["expected"] = check_result.expected
                result["actual"] = check_result.actual
            return result
        else:
            return "Passed"
    
    async def execute_in_jail(self, command: list[str]) -> bool:
        """Execute a command inside the jail."""
        return await self.jailer.execute_in_jail(command)
    
    @in_executor
    def send_input(self, input_str: str) -> None:
        """Send input to the jailed process."""
        self.jailer.stdin_to_jail(input_str)
        print(f"[INFO] [{PRINT_PREFIX}] Sent input to jailed process.")
    
    @in_executor
    def get_output(self, lines: int | None = 0, return_as='str') -> str | list:
        """Get output from the jailed process."""
        output = self.jailer.stdout_from_jail(lines=lines, return_as=return_as)
        print(f"[INFO] [{PRINT_PREFIX}] Retrieved output from jailed process.")
        return output
    
    @in_executor
    def get_errors(self, lines: int | None = 0, return_as='str') -> str | list:
        """Get error output from the jailed process."""
        errors = self.jailer.stderr_from_jail(lines=lines, return_as=return_as)
        print(f"[INFO] [{PRINT_PREFIX}] Retrieved errors from jailed process.")
        return errors
    
    @in_executor
    def is_running(self) -> bool:
        """Check if the jailed process is still running."""
        return self.jailer.is_process_running()
    
    @in_executor
    def wait_for_completion(self, timeout: int | None = None) -> int | str:
        """Wait for the jailed process to complete.

        Returns:
            0               -- process exited successfully.
            TIMEOUT         -- process was killed after exceeding the time limit.
            str (stderr)    -- process exited with a non-zero code; value is the
                               captured stderr, or a generic message if stderr is empty.
        """
        return_code = self.jailer.wait_for_process(timeout=timeout)
        print(f"[INFO] [{PRINT_PREFIX}] Process completed with return code: {return_code}")
        if return_code is None:
            return TIMEOUT
        if return_code == 0:
            return 0
        stderr = self.jailer.stderr_buffer.strip()
        return stderr or f"Process exited with return code {return_code}"
    
    @in_executor
    def get_exit_code(self) -> int | None:
        """Get the exit code of the jailed process (None if still running)."""
        return self.jailer.get_return_code()
    
    @in_executor
    def stop_execution(self, force: bool = False) -> None:
        """Stop the jailed process (gracefully or forcefully)."""
        if force:
            self.jailer.kill_process()
            print(f"[INFO] [{PRINT_PREFIX}] Forcefully killed jailed process.")
        else:
            self.jailer.terminate_process()
            print(f"[INFO] [{PRINT_PREFIX}] Terminated jailed process.")

    @in_executor
    def clear_output_buffers(self) -> None:
        """Clear the stdout and stderr buffers."""
        self.jailer.clear_buffers()
        print(f"[INFO] [{PRINT_PREFIX}] Cleared output buffers.")
    
    def cleanup(self) -> None:
        """Clean up the jail and all resources."""
        self.jailer.nuke_jail()
        print(f"[INFO] [{PRINT_PREFIX}] Cleaned up jail resources.")

    def get_random_int(self, a: int, b: int) -> int:
        """Get a random integer between a and b using the grader's random instance."""
        return self.random.randint(a, b)
    
    def get_random_choice(self, seq: list) -> any:
        """Get a random choice from a sequence using the grader's random instance."""
        return self.random.choice(seq)