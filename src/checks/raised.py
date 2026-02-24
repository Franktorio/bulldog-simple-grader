# src/checks/raised.py
# Definiton of errors


class RaisedError(Exception):
    """Custom error class for raised exceptions in checks."""
    header = "Error: Raised Exception"
    def __init__(self, message: str = None, hint: str = None, instructions: str = None, expected_output: str = None, actual_output: str = None, traceback: str = None):
        self.message = message
        self.hint = hint
        self.instructions = instructions
        self.expected_output = expected_output
        self.actual_output = actual_output
        self.traceback = traceback
        super().__init__(message)

    def __str__(self):
        return f"RaisedError: {self.message}"

def is_raised_error(obj) -> bool: # Probably not needed
    """Check if an object is an instance of RaisedError."""
    return isinstance(obj, RaisedError)

