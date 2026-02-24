# src/frontend/api/paths.py
# Paths for templates and static files used across the API

import os
from fastapi.templating import Jinja2Templates

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "frontend", "templates")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
