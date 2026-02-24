# config/config.py
# Helper functions to read and parse environment variables for configuration

import os
import sys
from typing import Optional, Sequence
from dotenv import load_dotenv

PRINT_PREFIX = "CONFIG"

# Load environment variables from .env file
env_file = os.getenv('ENV_FILE', '.env')
env_path = os.path.join(os.path.dirname(__file__), env_file)
load_dotenv(env_path)

def _get_env_int(key: str, default: Optional[int | str] = None) -> int:
    """Helper function to get integer from environment with error handling"""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Required environment variable {key} not found")
    try:
        print(f"[INFO] [{PRINT_PREFIX}] Loaded integer env var {key}={value}")
        return int(value)
    except ValueError:
        raise ValueError(f"Environment variable {key} must be a valid integer, got: {value}")

def _get_env_int_list(key: str, default: Optional[Sequence[int] | str] = None) -> list[int]:
    """Helper function to get comma-separated integers from environment"""
    value = os.getenv(key)
    if value is None:
        if default is None:
            raise ValueError(f"Required environment variable {key} not found")
        if isinstance(default, (list, tuple)):
            print(f"[INFO] [{PRINT_PREFIX}] Using default integer list for env var {key}={default}")
            return [int(x) for x in default]
        value = str(default)
    try:
        print(f"[INFO] [{PRINT_PREFIX}] Loaded integer list env var {key}={value}")
        return [int(x.strip()) for x in value.split(',') if x.strip()]
    except ValueError:
        raise ValueError(f"Environment variable {key} must be comma-separated integers, got: {value}")

def _get_env_str_list(key: str, default: Optional[Sequence[str] | str] = None) -> list[str]:
    """Helper function to get comma-separated strings from environment"""
    value = os.getenv(key)
    if value is None:
        if default is None:
            raise ValueError(f"Required environment variable {key} not found")
        if isinstance(default, (list, tuple)):
            print(f"[INFO] [{PRINT_PREFIX}] Using default string list for env var {key}={default}")
            return [str(x) for x in default]
        value = str(default)
    print(f"[INFO] [{PRINT_PREFIX}] Loaded string list env var {key}={value}")
    return [x.strip() for x in value.split(',') if x.strip()]
    
def _get_env_bool(key: str, default: Optional[bool | str] = None) -> bool:
    """Helper function to get boolean from environment"""
    value = os.getenv(key)
    if value is None:
        if default is None:
            raise ValueError(f"Required environment variable {key} not found")
        value = str(default)
        print(f"[INFO] [{PRINT_PREFIX}] Using default boolean env var {key}={value}")
    else:
        print(f"[INFO] [{PRINT_PREFIX}] Loaded boolean env var {key}={value}")
    return value.lower() in ('true', '1', 'yes')

# General Configuration
OPERATING_MODE = os.getenv('OPERATING_MODE', 'development')

_working_os = sys.platform.lower()
IS_LINUX = False
IS_WINDOWS = False
IS_MACOS = False
if _working_os.startswith('linux'):
    IS_LINUX = True
    print(f"[WARNING] [{PRINT_PREFIX}] Starting application with Linux configuration.")
elif _working_os.startswith('win'):
    IS_WINDOWS = True
    raise NotImplementedError("Windows is not supported at this time")
elif _working_os.startswith('darwin'):
    IS_MACOS = True
    raise NotImplementedError("macOS is not supported at this time")

# API Configuration
API_ENABLED = _get_env_bool('API_ENABLED', 'true')
API_PORT = _get_env_int('API_PORT', '8000')
API_SECRET_KEY = os.getenv('API_SECRET_KEY', 'supersecretkey_PLEASE_CHANGE_ME')
print(f"[INFO] [{PRINT_PREFIX}] API configuration loaded (enabled={API_ENABLED}, port={API_PORT})")

# Database Configuration
DB_REPLICA_SYNC_INTERVAL = _get_env_int('DB_REPLICA_SYNC_INTERVAL', '300')  # seconds
DB_SNAPSHOT_INTERVAL = _get_env_int('DB_SNAPSHOT_INTERVAL', '3600')  # seconds
DB_SNAPSHOT_RETENTION_COUNT = _get_env_int('DB_SNAPSHOT_RETENTION_COUNT', '72')
DB_HEALTH_CHECK_INTERVAL = _get_env_int('DB_HEALTH_CHECK_INTERVAL', '120')  # seconds
print(f"[INFO] [{PRINT_PREFIX}] Database configuration loaded (snapshot interval={DB_SNAPSHOT_INTERVAL}s, replica sync={DB_REPLICA_SYNC_INTERVAL}s)")

# Startup Configuration
RUN_STARTUP_TESTS = _get_env_bool('RUN_STARTUP_TESTS', 'false')

# Jailer Configuration
JAILER_BASE_PATH = os.getenv('JAILER_BASE_PATH', 'submissions/')
FALLBACK_NUKE_TIME = _get_env_int('FALLBACK_NUKE_TIME', '300')  # seconds
DEFAULT_TIMEOUT_TIME = _get_env_int('DEFAULT_TIMEOUT_TIME', '10')  # seconds
print(f"[INFO] [{PRINT_PREFIX}] Jailer configuration loaded (fallback nuke time={FALLBACK_NUKE_TIME}s, default timeout={DEFAULT_TIMEOUT_TIME}s)")