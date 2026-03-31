# Bulldog Simple Grader

A small-scale automated grading system for computer science class assignments. Instructors can create assignments with test suites, students submit code through a web interface, and submissions are evaluated in an isolated sandbox environment. The system is built with FastAPI + Jinja2 templates for the web interface. Every transaction is logged, and instructors can view results through a dashboard. The project includes automated backups and logging for reliability.

## Features
- **Web interface** for both students and instructors (FastAPI + Jinja2 templates)
- **Sandboxed code execution**: student code runs in a jailed process with network isolation, CPU limits (10s), and memory limits (512MB) <No virtualization or containerization, just Linux namespaces (`unshare`)>
- **Instructor dashboard**: manage students, assignments, and view submissions/completions
- **Student portal**: view assignments, submit code files, and see grading results
- **Automated backups**: Database system allows for quick migrations, automatic backups, replicas and rollbacks/restores
- **Rotating file logs**: Print function is monkey-patched to log all prints. The system automatically rotates the logs once every 24h and keeps them up to 7 days.

## Tech Stack
- **Python 3.10+**
- **FastAPI**: REST API and server-side rendered templates
- **Uvicorn**: ASGI server
- **SQLite**: database (via custom ORM helpers)
- **bcrypt**: password hashing
- **python-dotenv**: environment variable configuration
- **Linux namespaces (`unshare`)**: sandbox isolation

## Installation and Setup

### Prerequisites
- Python 3.10+
- Linux (required for sandboxing)

### Install dependencies
```bash 
pip install -r requirements.txt
```

### Configure environment
Create a `.env` file under /config (see .env.example for guidance)

### Run the application
```bash
python main.py
```

The application will automatically set everything up, including the database and logging.

## How to use

### Login & Users

- Instructors can log in to the dashboard to create assignments, manage students, and view submissions.
- Students can log in to view assignments, submit their code, and see grading results.

**To add instructors/students, look at /automations/scripts/add_user.py**

### Creating Assignments

To create an assignment, read EVAL_DOCS.md

## Project Structure

```
bulldog-simple-grader/
├── main.py                          # Entry point, admin REPL (not in use), and startup sequence
├── requirements.txt
├── config/
│   └── config.py                    # All env-var stuff
├── src/
│   ├── log_module.py                # Monkey-patches print(); daily log rotation/deletion
│   ├── utils.py                     # Shared async helpers (in_executor, format_datetime, etc.)
│   ├── checks/
│   │   ├── check.py                 # @check decorator: wraps tests, catches errors
│   │   ├── raised.py                # RaisedError: structured grading failure with hints
│   │   └── orchestrator.py          # Wraps everything together at a high-level (Upload -> Test -> Record results -> Return feedback)
│   ├── grader/
│   │   ├── grader.py                # Grader class: high-level async jail API for evaluations
│   │   └── jailer.py                # Jailer class: Linux namespace sandbox + ulimit enforcement
│   ├── db/
│   │   ├── connections.py           # SQLite connection management, init, migrate, clear
│   │   ├── app_context.py           # data/app_context.json key-value store (assignments, app_data)
│   │   ├── backups.py               # Handles database backups, replicas, and restores/rollbacks
│   │   └── grader_db/
│   │       ├── schema.py            # CREATE TABLE definitions for all tables
│   │       ├── students.py          # Student model + CRUD
│   │       ├── instructors.py       # Instructor model + CRUD
│   │       ├── assignments.py       # Assignment model + CRUD
│   │       ├── slugs.py             # CRUD for assignment slugs (questions)
│   │       ├── submissions.py       # Record of every submission (student, code, timestamp, etc.)
│   │       ├── slug_completions.py  # Record of students that have completed specific slugs (questions)
│   │       ├── full_completions.py  # Record of students that have completed an assignment
│   │       ├── login_tokens.py      # Tokens used for logging in
│   │       └── helpers.py           # Higher-level DB queries used by the frontend
│   └── frontend/
│       └── api/
│           ├── app.py               # FastAPI app, exception handlers, static mount, /logout
│           ├── paths.py             # Resolves static/ and templates/ paths, Jinja2 instance
│           ├── student/
│           │   ├── authentication.py  # Validates password or cookie token for students
│           │   ├── constants.py       # URL paths, template names, cookie config
│           │   └── routes.py          # Student routes: login, home, assignment view, file submit
│           └── instructor/
│               ├── authentication.py  # Same as student auth, raises 400 instead of 401 (feel free to fix/rewrite if you want to unify them)
│               ├── constants.py       # URL paths and template names for all instructor pages
│               └── routes.py          # Instructor routes: dashboard, add/view students & assignments
├── evaluations/                     # One subdirectory per assignment (see EVAL_DOCS.md)
│   ├── files/
│   │   ├── sales/                   # Example: file-based assignment with summary comparison
│   │   └── todolist/                # Example: randomized to-do list assignment
│   └── minesweeper/                 # Example: assignment focused on a game
├── automations/
│   └── scripts/
│       ├── add_user.py              # CLI: add a single student/instructor
│       ├── change_password.py       # CLI: force-reset a password (no old password required)
│       ├── migrate_db.py            # CLI: drop and recreate a database to the current schema
│       └── parse_txt.py             # CLI: bulk-create users from a plain-text roster file
├── data/
│   ├── app_context.json             # Runtime key-value state (backup timestamps, etc.)
│   ├── backups/                     # Point-in-time SQLite snapshots
│   └── replicas/                    # A replica db that gets updated frequently and is the first automated restore point if something goes wrong (e.g. a bad migration [if this fails, systems starts rolling from backups until it finds a working one])
├── logs/
│   ├── app_logs.log                 # Active log file (written by the monkey-patched print)
│   └── rotated_logs/                # Archived logs in dated subdirectories 
└── submissions/                     # Jail root directory; student code files get copied here for execution
```

## Notes for maintainers

### Adding a new assignment

Each assignment lives in its own folder under `evaluations/`. Inside it, you need an `__init__.py` that defines your test functions and an `ALL_TESTS` list. Read [src/EVAL_DOCS.md](src/EVAL_DOCS.md) for the full walkthrough (it covers the `@check` decorator, how to use the `Grader` API, and some example patterns. Once the folder is ready, register the assignment through the instructor dashboard.

Each assignment is split into *slugs*, where each slug is one thing a student submits (usually one file). Keep them small and focused.

### Adding a new database table

Add your `CREATE TABLE IF NOT EXISTS` statement to `src/db/grader_db/schema.py`, then create a new file (e.g. `my_table.py`) in the same folder with a dataclass and the usual CRUD functions. Look at any of the existing modules like `students.py` or `slugs.py` for the pattern to follow. Finally, re-export everything from `src/db/grader_db/__init__.py` so the rest of the app can import it from one place.

Keep raw SQL inside its own module. Don't scatter queries around the codebase. ALWAYS create a module for every table, even if it's just one or two queries. This keeps the code organized and makes it easier to maintain the database layer.

After changing the schema, run `automations/scripts/migrate_db.py <database_name>.db` to apply it.

### Adding a new route

Student and instructor routes live in separate folders and should stay that way. Add student routes to `src/frontend/api/student/routes.py` and instructor routes to `src/frontend/api/instructor/routes.py`. Put any new URL strings in the corresponding `constants.py` before referencing them anywhere. Every route that requires a logged-in user must use the `get_authenticated_student` or `get_authenticated_instructor` dependency.

### Configuration

All settings go in `.env` and get read through `config/config.py`. Don't hardcode ports, paths, or timeouts anywhere else. If you need a new setting, add a typed getter to `config.py` following the existing helpers.

### Logging

Just use `print()`. It's already wired up to write timestamped entries to the log file. Follow the format the rest of the codebase uses: `[LEVEL] [MODULE_PREFIX] message`, for example `[INFO] [GRADER] Jail created`. Don't introduce a separate logging library.

### Sandbox safety

Student code must always run through `Grader.execute_in_jail()`. Never execute anything from a student submission directly on the host.

### Automation scripts

Run the scripts in `automations/scripts/` as modules, not files directly:

```bash
python -m automations.scripts.add_user student 42 "Jane Doe" password123
```

This is necessary because they import from the main codebase. Running them with `python automations/scripts/add_user.py` will break the imports.
(feel free to fix/rewrite them)

