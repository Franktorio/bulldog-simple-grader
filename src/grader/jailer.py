# src/grader/jailer.py
# Creates a temporary directory to safely execute untrusted code.

import subprocess
import threading
import shutil
import os
import time
from typing import Literal, Optional

from src.utils import in_executor
from config.config import FALLBACK_NUKE_TIME, DEFAULT_TIMEOUT_TIME, JAILER_BASE_PATH

PRINT_PREFIX = "JAILER"

class Jailer:
    def __init__(self,  student_id: int, assignment: str, timeout: int | None = DEFAULT_TIMEOUT_TIME):
        self.temp_dir = None
        self.nuked = False
        self.timeout = timeout
        self.stdout_buffer = ""
        self.stderr_buffer = ""
        self.process = None

        self.student_id = student_id
        self.assignment = assignment

        self.name = f"{student_id}_{assignment}"

        self.nuke_after_time(FALLBACK_NUKE_TIME)  # Nuke jail after configured time as a safety measure

    @in_executor
    def create_jail(self) -> str:
        """Create a temporary directory to serve as a jail."""
        # Remove if exists first
        path = os.path.join(JAILER_BASE_PATH, f"{self.student_id}_{self.assignment}")
        if os.path.exists(path):
            shutil.rmtree(path)
        os.mkdir(path)
        self.temp_dir = os.path.abspath(path)
        print(f"[INFO] [{PRINT_PREFIX}] Created jail at {self.temp_dir}")
        return self.temp_dir
    
    @in_executor
    def execute_in_jail(self, command: list[str]) -> bool:
        """Execute a command inside the jail (temporary directory)."""
        if not self.temp_dir:
            raise RuntimeError("Jail has not been created.")
        
        # Replace 'python' with 'python3' for better compatibility
        if command and command[0] == 'python':
            command[0] = 'python3'
        
        # Maximum security isolation with resource limits
        jailed_command = [
            "unshare",
            "--net",            # Network isolation (no internet, no sockets)
            "--pid",            # Process ID isolation
            "--ipc",            # Inter-process communication isolation
            "--uts",            # Hostname/domain isolation
            "--fork",           # Fork to new process
            "--mount-proc",     # Mount clean /proc
            "--map-root-user",  # Map to fake root inside namespace
            "sh", "-c",         # Use shell to apply resource limits
            f"""
            ulimit -t 10          # CPU time: 10 seconds max
            ulimit -v 524288      # Virtual memory: 512MB max (in KB)
            ulimit -f 10240       # File size: 10MB max per file (in KB)
            ulimit -n 256         # Max open files: 256
            ulimit -c 0           # Core dump size: 0 (no core dumps)
            
            cd {self.temp_dir}
            exec env -i \
                HOME=/jail \
                PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
                PYTHONIOENCODING=utf-8 \
                PYTHONDONTWRITEBYTECODE=1 \
                LANG=C.UTF-8 \
                LC_ALL=C.UTF-8 \
                TMPDIR={self.temp_dir} \
                {' '.join(command)}
            """
        ]
        
        # Security features:
        # - CPU: 10 seconds max execution time
        # - Memory: 512MB max virtual memory
        # - File size: 10MB per file max
        # - Processes: 64 max
        # - Open files: 256 max
        # - Network: Completely isolated (--net)
        # - Process isolation: Separate PID namespace
        # - IPC: Isolated inter-process communication

        # Exec env -i sets environment variables that hide host information

        print(f"[INFO] [{PRINT_PREFIX}] Executing command in jail {self.temp_dir} with resource limits")


        def _buffer_stdout():
            """Helper function to buffer stdout from the jailed process."""
            process = self.process  # Store local reference to avoid None access if process is cleared
            if process is None:
                return
            
            try:
                while True:
                    output = process.stdout.readline()
                    # Check if program has terminated
                    terminated = process.poll() is not None # Poll returns None if process is still running
                    if output:
                        self.stdout_buffer += output
                    if terminated:
                        break
            except Exception as e:
                print(f"[ERROR] [{PRINT_PREFIX}] Error while buffering stdout: {e}")
        
        def _buffer_stderr():
            """Helper function to buffer stderr from the jailed process."""
            process = self.process  # Store local reference to avoid None access if process is cleared
            if process is None:
                return
            
            try:
                while True:
                    output = process.stderr.readline()
                    terminated = process.poll() is not None
                    if output:
                        self.stderr_buffer += output
                    if terminated:
                        break
            except Exception as e:
                print(f"[ERROR] [{PRINT_PREFIX}] Error while buffering stderr: {e}")

        try:
            threading.Thread(target=self._timeout_thread, args=(self.timeout,), daemon=True).start()  # Start timeout thread to kill process if it runs too long
            # Use Popen to start the process in the background
            self.process = subprocess.Popen(
                jailed_command,
                cwd=self.temp_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1024,
            )
        except Exception as e:
            print(f"[ERROR] [{PRINT_PREFIX}] Failed to start jailed process: {e}")
            return False
        threading.Thread(target=_buffer_stdout, daemon=True).start()
        threading.Thread(target=_buffer_stderr, daemon=True).start()
        return True
    
    def stdin_to_jail(self, input_str: str) -> None:
        """Pass input to the jailed process's standard input."""
        if not self.temp_dir or self.process is None:
            raise RuntimeError("Jail or jailed process has not been created.")
        
        try:
            self.process.stdin.write(input_str)
            self.process.stdin.flush()
            print(f"[INFO] [{PRINT_PREFIX}] Passed input to jailed process.")
        except Exception as e:
            print(f"[ERROR] [{PRINT_PREFIX}] Failed to pass input to jailed process: {e}")

    def stdout_from_jail(self, lines: int | None = 0, return_as = Literal['str', 'list']) -> str | list:
        """Get output from the jailed process's standard output."""
        if not self.temp_dir:
            raise RuntimeError("Jail has not been created.")
        
        limit = None if lines == 0 else lines
        output_lines = self.stdout_buffer.splitlines(keepends=True)

        if limit:
            output_lines = output_lines[-limit:]
        if return_as == 'str':
            output = ''.join(output_lines)
        elif return_as == 'list':
            output = output_lines
        else:
            raise ValueError("invalid return_as value, must be 'str' or 'list'.")
        
        print(f"[INFO] [{PRINT_PREFIX}] Retrieved output from jail {self.temp_dir} process.")
        return output
    
    def stderr_from_jail(self, lines: int | None = 0, return_as = Literal['str', 'list']) -> str | list:
        """Get error output from the jailed process's standard error."""
        if not self.temp_dir:
            raise RuntimeError("Jail has not been created.")
        
        limit = None if lines == 0 else lines
        output_lines = self.stderr_buffer.splitlines(keepends=True)

        if limit:
            output_lines = output_lines[-limit:]
        if return_as == 'str':
            output = ''.join(output_lines)
        elif return_as == 'list':
            output = output_lines
        else:
            raise ValueError("invalid return_as value, must be 'str' or 'list'.")
        
        print(f"[INFO] [{PRINT_PREFIX}] Retrieved stderr from jail {self.temp_dir} process.")
        return output
    
    def is_process_running(self) -> bool:
        """Check if the jailed process is still running."""
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def wait_for_process(self, timeout: Optional[int] = None) -> Optional[int]:
        """Wait for the jailed process to complete and return its exit code."""
        if self.process is None:
            raise RuntimeError("No jailed process has been created.")
        
        try:
            returncode = self.process.wait(timeout=timeout or self.timeout)
            print(f"[INFO] [{PRINT_PREFIX}] Process completed with return code: {returncode}")
            return returncode
        except subprocess.TimeoutExpired:
            print(f"[WARNING] [{PRINT_PREFIX}] Process timed out after {timeout or self.timeout} seconds.")
            print(f"[INFO] [{PRINT_PREFIX}] Killing timed-out process.")
            self.process.kill()
            self.process.wait()  # Wait for process to fully terminate
            return None
    
    def get_return_code(self) -> Optional[int]:
        """Get the return code of the jailed process (None if still running)."""
        if self.process is None:
            return None
        return self.process.poll()
    
    def terminate_process(self) -> None:
        """Terminate the jailed process gracefully."""
        if self.process is not None:
            self.process.terminate()
            print(f"[INFO] [{PRINT_PREFIX}] Process terminated.")
    
    def kill_process(self) -> None:
        """Forcefully kill the jailed process."""
        if self.process is not None:
            self.process.kill()
            print(f"[INFO] [{PRINT_PREFIX}] Process killed.")
    
    def jail_exists(self) -> bool:
        """Check if the jail directory exists."""
        return self.temp_dir is not None and not self.nuked
    
    def clear_buffers(self) -> None:
        """Clear stdout and stderr buffers."""
        self.stdout_buffer = ""
        self.stderr_buffer = ""
        print(f"[INFO] [{PRINT_PREFIX}] Cleared output buffers.")

    def nuke_jail(self):
        """Delete the temporary directory and all its contents."""
        if not self.temp_dir:
            print(f"[WARNING] [{PRINT_PREFIX}] Attempted to nuke jail {self.name} but it does not exist.")
            return
        
        _jail_name = self.temp_dir

        if self.process is not None:
            if self.process.poll() is None:
                self.process.kill()
        
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"[ERROR] [{PRINT_PREFIX}] Failed to nuke jail {_jail_name}: {e}")
            print(f"[WARNING] [{PRINT_PREFIX}] Attempting to nuke jail {_jail_name} again after failure.")
            time.sleep(1)
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"[ERROR] [{PRINT_PREFIX}] Second attempt to nuke jail {_jail_name} also failed: {e}")
                print(f"[WARNING] [{PRINT_PREFIX}] Jail {_jail_name} may not have been fully nuked. Manual cleanup may be required.")
            return
        self.nuked = True
        self.temp_dir = None
        self.process = None

        print(f"[INFO] [{PRINT_PREFIX}] Nuked jail {_jail_name} successfully.")

    def nuke_after_time(self, seconds: int):
        """Nuke the jail after a specified time in seconds."""

        def _delayed_nuke():
            """Helper function to nuke after delay. Fallback incase code doesn't terminate properly."""
            seconds_passed = 0
            while seconds_passed < seconds:
                if self.nuked:
                    return
                threading.Event().wait(1)
                seconds_passed += 1
            print(f"[WARNING] [{PRINT_PREFIX}] Nuking jail {self.temp_dir} after {seconds} seconds because it has not been nuked yet.")
            self.nuke_jail()
        
        threading.Thread(target=_delayed_nuke, daemon=True).start()

    def _timeout_thread(self, timeout: int):
        """Helper function to stop the process after a timeout."""
        threading.Event().wait(timeout)
        if self.is_process_running():
            print(f"[WARNING] [{PRINT_PREFIX}] Process in jail {self.temp_dir} timed out after {timeout} seconds. Killing process.")
            self.kill_process()