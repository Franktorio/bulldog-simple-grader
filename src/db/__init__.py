# src\db\__init__.py
# Database module for the grading system
# Provides database connections, backups, and application context storage

import os

# Global database directories
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) # get out of src/db (place in working dir)
DB_DIR = os.path.join(PROJECT_ROOT, "data")
SNAPSHOTS_DIR = os.path.join(DB_DIR, 'backups')
REPLICAS_DIR = os.path.join(DB_DIR, 'replicas')

# Global databases dictionary that stores the filename and its module
DATABASES = {} # Gets populated when the dbs are initialized

# Create necessary directories if they don't exist
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
os.makedirs(REPLICAS_DIR, exist_ok=True)

# Exported modules
from . import connections
from . import app_context
from . import backups


