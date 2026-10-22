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
    if code == TIMEOUT:
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
- `input_and_wait_for_output("text\n", "expected response", timeout=5)` - Send input and poll stdout for the expected text.
- `get_output()` / `get_errors()` - Get stdout/stderr
- `wait_for_completion(timeout=5)` - Wait for exit code
- `place_file_in_jail(source, dest)` - Add file to jail, optionally remove the source.
- `read_jail_file("name.txt")` - Read file from jail
- `clear_output_buffers()` - Reset buffers between tests

## Interactive input and output

```python
try:
    output = await grader.input_and_wait_for_output(
        "test input\n", expected_output="expected response\n", timeout=3
    )
    next_output = await grader.input_and_wait_for_output(
        "next input\n", expected_output=False, timeout=3
    )
except TimeoutError:
    raise RaisedError("Timeout", hint="Expected response was not received")
```

Arguments:

- `input_str`: Text sent to stdin exactly as provided. Include a newline when the program expects a line of input.
- `expected_output`: A case-sensitive substring to wait for, or `False` to wait for any new stdout. An empty string matches immediately.
- `timeout`: Seconds to wait after sending input; defaults to 5. This does not reset the overall execution timeout.

Returns a string containing all captured stdout after the index saved before
sending input. Existing text before that index is excluded. The method polls
every 10 ms and raises `TimeoutError` if the condition is not met in time;
it does not kill the process or stop waiting solely because the process exits.

Partial matches keep waiting until the full expected substring appears. Include
a newline in the expected text when you need that line ending. In `False` mode,
the first available text is returned. Neither mode guarantees that the program
has finished writing its entire response.

Call the method sequentially and do not clear buffers during a wait. The existing
reader requires flushed output followed by a newline (or EOF), and stops retaining
stdout at 10,000 characters. Output beyond that cap cannot satisfy a match. Output
written earlier but captured after the saved index can still be included.
