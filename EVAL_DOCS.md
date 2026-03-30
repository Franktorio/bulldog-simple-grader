# Evaluation Creation Guide

## Overview
Evaluations test student submissions in an isolated jail environment with security limits (10s CPU , 512MB RAM, no network).

## Add an assignment
1. Create a new directory under `evaluations/` for the assignment (e.g. `evaluations/assignment1/`)
2. For every assignment question (slug), create a subdirectory (e.g. `evaluations/assignment1/q1/`)
3. In each slug directory, create an `__init__.py` file that defines the tests for that question (see below for required structure and examples)
4. On the instructor dashboard (webapp), create a new assignment and add questions with the same slugs as the directories you created. The system will automatically link them to the test functions you defined in the `__init__.py` files.

## Required Structure

Every evaluation module at `evaluations/{assignment_dir}/{slug_name}/__init__.py` needs:

```python
from src.checks import check
from src.checks.raised import RaisedError
from src.grader.grader import Grader, TIMEOUT

grader = None



def set_grader(g: Grader) -> None:
    global grader
    grader = g

@check
async def my_test_one():
    return True

@check
async def my_test_two():
    return True

@check
async def run_code_check():
    await grader.execute_in_jail(["python", "solution.py"])
    code = await grader.wait_for_completion(timeout=3)
    if code == TIMEOUT:
        raise RaisedError("Timeout", hint="Check for infinite loops")
    if code != 0:
        raise RaisedError("Runtime error", traceback=code)
    return True
ALL_TESTS = [my_test_one, my_test_two, run_code_check]  # Required: list of all test functions
```

## Writing Tests

Tests use the `@check` decorator and either return `True` or raise `RaisedError`:

```python
@check
async def output_check():
    await grader.clear_output_buffers()  # Clear previous output
    await grader.execute_in_jail(["python", "solution.py"])
    await grader.send_input("test input\n")
    
    code = await grader.wait_for_completion(timeout=5)
    if code is None:
        raise RaisedError("Timeout", hint="Check for infinite loops")
    if code != 0:
        raise RaisedError("Runtime error", hint=await grader.get_errors())
    
    actual = await grader.get_output()
    if actual != "expected output\n":
        raise RaisedError("Wrong output", hint="Check formatting")
    return True
```

## Common Grader Methods

- `execute_in_jail(["python", "file.py"])` - Run command in jail
- `send_input("text\n")` - Send to stdin
- `get_output()` / `get_errors()` - Get stdout/stderr
- `wait_for_completion(timeout=5)` - Wait for exit code
- `place_file_in_jail(source, dest)` - Add file to jail, optionally remove the source.
- `read_jail_file("name.txt")` - Read file from jail
- `clear_output_buffers()` - Reset buffers between tests