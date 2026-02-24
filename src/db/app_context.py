# src\db\app_context.py
# Application Context Handler - Manages app_context.json file
# Stores configuration and runtime data for the grading system.

PRINT_PREFIX = "APP CONTEXT"

# Standard library imports
import json
import os

# Local imports
from . import DB_DIR

# Determine project root and app_context.json path
APP_CONTEXT_PATH = os.path.join(DB_DIR, "app_context.json")

context_data = None

def create_app_context() -> None:
    """Initialize app_context.json with default structure if it doesn't exist."""
    global context_data
    if not os.path.exists(APP_CONTEXT_PATH):
        with open(APP_CONTEXT_PATH, 'w') as f:
            json.dump({
                "assignments": {},       # Assignment-specific data (keyed by assignment ID)
                "app_data": {},          # General application data (timestamps, locks, etc.)
            }, f, indent=2)
        print(f"[INFO] [{PRINT_PREFIX}] Created new app_context.json")
    else:
        print(f"[INFO] [{PRINT_PREFIX}] app_context.json already exists. Loaded existing context.")

    # Load context data
    with open(APP_CONTEXT_PATH, 'r') as f:
        context_data = json.load(f)


# Function to save context data back to app_context.json
def _save_context() -> None:
    """Save the context_data dictionary to app_context.json file."""
    with open(APP_CONTEXT_PATH, 'w') as f:
        json.dump(context_data, f, indent=2)
    print(f"[DEBUG] [{PRINT_PREFIX}] app_context.json saved")


def export_context() -> dict:
    """Export the entire context_data dictionary"""
    print(f"[DEBUG] [{PRINT_PREFIX}] Exported app_context.json data")
    return context_data


# Functions to add or update entries in context data
def set_assignment_data(key: str, value: any) -> None:
    """Add or update an assignment entry in context_data."""
    context_data["assignments"][key] = value
    _save_context()


def set_app_data(key: str, value: any) -> None:
    """Add or update a general application data entry in context_data."""
    context_data["app_data"][key] = value
    _save_context()


# Functions to retrieve entries from context data
def get_assignment_data(key: str, default: any = None) -> any:
    """Retrieve an assignment entry from context_data."""
    return context_data["assignments"].get(key, default)


def get_app_data(key: str, default: any = None) -> any:
    """Retrieve a general application data entry from context_data."""
    return context_data["app_data"].get(key, default)


# Functions to delete entries from context data
def delete_assignment_data(key: str) -> None:
    """Delete an assignment entry from context_data."""
    if key in context_data["assignments"]:
        del context_data["assignments"][key]
        _save_context()


def delete_app_data(key: str) -> None:
    """Delete a general application data entry from context_data."""
    if key in context_data["app_data"]:
        del context_data["app_data"][key]
        _save_context()