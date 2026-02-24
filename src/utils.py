import asyncio
import json
from datetime import datetime
import os
from functools import partial

def in_executor(func):
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        func_with_args = partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, func_with_args)
    return wrapper

@in_executor
def load_json(file_path):
    """Load a JSON file and return its contents as a dictionary."""
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def move_file(source_path: str, dest_path: str, keep_source: bool = False) -> None:
    """Move a file from source_path to dest_path."""
    with open(source_path, "r") as src_file:
        with open(dest_path, "w") as dest_file:
            dest_file.write(src_file.read())
    if not keep_source:
        os.remove(source_path)

def format_datetime(timestamp: int | None) -> str:
    """Convert a UNIX timestamp to a human-readable string."""
    if timestamp is None:
        return "No due date"
    dt = datetime.fromtimestamp(timestamp)
    day = dt.day
    ending = _decide_ending(day)
    return dt.strftime(f"%A, %B {day}{ending}, %Y")

def _decide_ending(day: int) -> str:
    """Helper function to determine the correct ordinal suffix for a day."""
    if 11 <= day <= 13:
        return "th"
    last_digit = day % 10
    if last_digit == 1:
        return "st"
    elif last_digit == 2:
        return "nd"
    elif last_digit == 3:
        return "rd"
    else:
        return "th"