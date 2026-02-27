# src/frontend/api/app.py
# Main API application using FastAPI

import os
import uvicorn
import threading
from fastapi import Cookie, FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from config.config import API_ENABLED, API_PORT
from src.db.grader_db import delete_login_token
from .paths import STATIC_DIR, templates
from .student import router as student_router
from .student.constants import STUDENT_LOGIN_URL, COOKIE_KEY
from .instructor.constants import INSTRUCTOR_LOGIN_URL, COOKIE_KEY as INSTRUCTOR_COOKIE_KEY
from .instructor import router as instructor_router

PRINT_PREFIX = "API"

app = FastAPI()


@app.exception_handler(StarletteHTTPException)
async def custom_404_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    raise exc


@app.exception_handler(HTTPException)
async def auth_exception_handler(request: Request, exc: HTTPException):
    """Handle 401 authentication exceptions by redirecting to login."""
    if exc.status_code == 400:
        response = RedirectResponse(url=INSTRUCTOR_LOGIN_URL, status_code=303)
        response.delete_cookie(key=INSTRUCTOR_COOKIE_KEY)
        return response
    if exc.status_code == 401:
        response = RedirectResponse(url=STUDENT_LOGIN_URL, status_code=303)
        response.delete_cookie(key=COOKIE_KEY)
        return response
    if exc.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

app.include_router(student_router)
app.include_router(instructor_router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def start_api_server():
    """Start the API server using Uvicorn."""
    if not API_ENABLED:
        print(f"[INFO] [{PRINT_PREFIX}] API server is disabled in configuration. Not starting.")
        return
    print(f"[INFO] [{PRINT_PREFIX}] Starting API server on port {API_PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)
    # def _run_uvicorn():
    #     uvicorn.run(app, host="0.0.0.0", port=API_PORT)
    # api_thread = threading.Thread(target=_run_uvicorn, daemon=True, name="APIServerThread")
    # api_thread.start()

@app.post("/logout", name="logout_post")
def student_logout_post(token: str = Cookie(None)):
    """Handle student logout."""
    if token:
        success = delete_login_token(token)
        if success:
            print(f"[INFO] [{PRINT_PREFIX}] Successfully logged out student with token: {token[-5:]}")
        else:
            print(f"[WARNING] [{PRINT_PREFIX}] Failed to delete login token during logout: {token[-5:]}")
    else:
        print(f"[INFO] [{PRINT_PREFIX}] No login token found in cookies during logout attempt.")
    
    response = RedirectResponse(url=STUDENT_LOGIN_URL, status_code=303)
    response.delete_cookie(key=COOKIE_KEY)
    return response

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve the favicon."""
    favicon_path = os.path.join(STATIC_DIR, "images", "favicon.ico")
    return FileResponse(favicon_path)
    