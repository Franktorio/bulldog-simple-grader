# src\db\backups.py
# Backup Manager - Handles backup and restoration of databases

PRINT_PREFIX = "BACKUP MANAGER"

# Standard library imports
import os
import sqlite3
import datetime
import threading
import time

# Local imports
from . import app_context
from . import DB_DIR, REPLICAS_DIR, SNAPSHOTS_DIR, DATABASES
from .connections import connect_db
from config.config import DB_SNAPSHOT_INTERVAL, DB_REPLICA_SYNC_INTERVAL, DB_SNAPSHOT_RETENTION_COUNT

def init_backup_manager():
    """
    Initializes and starts the backup manager thread.
    """
    # Ensure database backups directory exists
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    os.makedirs(REPLICAS_DIR, exist_ok=True)

    for thread in threading.enumerate():
        if thread.name == "BackupManagerThread":
            print(f"[INFO] [{PRINT_PREFIX}] Backup manager thread already running. Skipping initialization.")
            return
    
    backup_thread = threading.Thread(target=backup_manager, daemon=True, name="BackupManagerThread")
    backup_thread.start()
    print(f"[INFO] [{PRINT_PREFIX}] Backup manager initialization complete")

def create_snapshot(db_file_name: str) -> bool:
    """
    Create a snapshot of the specified database in the snapshots directory.
    Args:
        db_file_name: Name of the database file to snapshot
    Returns:
        bool: True if snapshot creation was successful, False otherwise
    """

    try:
        with open(os.path.join(DB_DIR, db_file_name), 'rb') as src_file:
            with open(os.path.join(SNAPSHOTS_DIR, db_file_name+f"_snapshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"), 'wb') as dest_file:
                dest_file.write(src_file.read())
    except Exception as e:
        print(f"[ERROR] [{PRINT_PREFIX}] Failed to create snapshot for {db_file_name}: {e}")
        return False
    return True

def create_replica(db_file_name: str) -> bool:
    """
    Create a replica of the specified database in the replicas directory and replaces the old replica.
    Args:
        db_file_name: Name of the database file to replicate 
    Returns:
        bool: True if replica creation was successful, False otherwise
    """

    try:
        with open(os.path.join(DB_DIR, db_file_name), 'rb') as src_file:
            with open(os.path.join(REPLICAS_DIR, db_file_name), 'wb') as dest_file:
                dest_file.write(src_file.read())
    except Exception as e:
        print(f"[ERROR] [{PRINT_PREFIX}] Failed to create replica for {db_file_name}: {e}")
        return False
    return True

def restore_from_replica(db_file_name: str) -> bool:
    """
    Restore the specified database from its replica.
    
    Args:
        db_file_name: Name of the database file to restore
    Returns:
        bool: True if restoration was successful, False otherwise
    """
    try:
        with open(os.path.join(REPLICAS_DIR, db_file_name), 'rb') as src_file:
            with open(os.path.join(DB_DIR, db_file_name), 'wb') as dest_file:
                dest_file.write(src_file.read())
    except Exception as e:
        print(f"[ERROR] [{PRINT_PREFIX}] Failed to restore {db_file_name} from replica: {e}")
        return False
    return True

def restore_from_snapshot(db_file_name: str, index: int) -> bool:
    """
    Restore the specified database from a snapshot.
    
    Args:
        db_file_name: Name of the database file to restore
        index: Index of the snapshot to restore from (0 = most recent)
    Returns:
        bool: True if restoration was successful, False otherwise
    """

    try:
        # List all snapshots for the database
        snapshots = [f for f in os.listdir(SNAPSHOTS_DIR) if f.startswith(db_file_name+"_snapshot_")]
        snapshots.sort(key=lambda x: os.path.getmtime(os.path.join(SNAPSHOTS_DIR, x)), reverse=True)

        if index >= len(snapshots):
            print(f"[WARNING] [{PRINT_PREFIX}] No snapshot available at index {index} for {db_file_name}.")
            return False

        snapshot_file = snapshots[index]

        with open(os.path.join(SNAPSHOTS_DIR, snapshot_file), 'rb') as src_file:
            with open(os.path.join(DB_DIR, db_file_name), 'wb') as dest_file:
                dest_file.write(src_file.read())
    except Exception as e:
        print(f"[ERROR] [{PRINT_PREFIX}] Failed to restore {db_file_name} from snapshot: {e}")
        return False
    return True

def db_integrity_check(db_file_name: str) -> bool:
    """
    Perform an integrity check on the specified database.
    
    Args:
        db_file_name: Name of the database file to check
        
    Returns:
        bool: True if the database is intact, False otherwise
    """
    try:
        conn = connect_db(db_file_name, read_only=True)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check(1);") # Check up to 1 error
        result = cursor.fetchone()
        conn.close()
        return result[0] == "ok"
    except sqlite3.DatabaseError as e:
        print(f"[ERROR] [{PRINT_PREFIX}] Database integrity check failed for {db_file_name}: {e}")
        return False

def backup_manager(interval: int = None): # Runs based on DB_HEALTH_CHECK_INTERVAL
    """
    Runs periodically to create snapshots and replicas of databases when their interval is met.
    It will:
    - Perform integrity checks
    - Create snapshots
    - Create replicas

    If main database fails the integrity check, it will attempt to restore from the replica, and
    if the replica also shows integrity issues, it will rollback to the nearest snapshot.
    
    Args:
        interval: Health check interval in seconds. If None, uses DB_HEALTH_CHECK_INTERVAL from config.
    """
    from config.config import DB_HEALTH_CHECK_INTERVAL
    if interval is None:
        interval = DB_HEALTH_CHECK_INTERVAL

    while True:
        time_now = datetime.datetime.now().timestamp()
        last_snapshot = app_context.get_app_data("last_snapshot_time", 0)
        last_replica = app_context.get_app_data("last_replica_time", 0)

        print(f"[DEBUG] [{PRINT_PREFIX}] Running backup manager loop (current time: {datetime.datetime.now()}, last snapshot: {datetime.datetime.fromtimestamp(last_snapshot)}, last replica: {datetime.datetime.fromtimestamp(last_replica)})")

        # Do integrity checks on all databases
        for db_file in DATABASES:
            check = db_integrity_check(db_file)

            if check:
                continue

            print(f"[ERROR] [{PRINT_PREFIX}] Integrity check failed for {db_file}. Attempting restoration.")

            # Try restoring from replica
            print(f"[INFO] [{PRINT_PREFIX}] Attempting to restore {db_file} from replica...")
            replica_success = restore_from_replica(db_file)
            if replica_success and db_integrity_check(db_file):
                print(f"[INFO] [{PRINT_PREFIX}] Successfully restored {db_file} from replica.")
                continue
            
            for i in range(3): # Try up to 3 snapshots
                print(f"[INFO] [{PRINT_PREFIX}] Attempting to restore {db_file} from snapshot index {i}...")
                snapshot_success = restore_from_snapshot(db_file, i)
                if snapshot_success and db_integrity_check(db_file):
                    print(f"[INFO] [{PRINT_PREFIX}] Successfully restored {db_file} from snapshot index {i}.")
                    break
        
        # Create snapshot if interval met (DB_SNAPSHOT_INTERVAL is in seconds)
        if time_now - last_snapshot >= DB_SNAPSHOT_INTERVAL:
            for db_file in DATABASES:
                snapshot_success = create_snapshot(db_file)
                if snapshot_success:
                    print(f"[INFO] [{PRINT_PREFIX}] Created snapshot for {db_file}.")
            app_context.set_app_data("last_snapshot_time", time_now)
        
        # Create replica if interval met (DB_REPLICA_SYNC_INTERVAL is in seconds)
        if time_now - last_replica >= DB_REPLICA_SYNC_INTERVAL:
            for db_file in DATABASES:
                replica_success = create_replica(db_file)
                if replica_success:
                    print(f"[INFO] [{PRINT_PREFIX}] Created replica for {db_file}.")
            app_context.set_app_data("last_replica_time", time_now)
        
        # Delete old snapshots beyond retention count (keep only the most recent N snapshots per database)
        for db_file in DATABASES:
            snapshots = [f for f in os.listdir(SNAPSHOTS_DIR) if f.startswith(db_file+"_snapshot_")]
            snapshots.sort(key=lambda x: os.path.getmtime(os.path.join(SNAPSHOTS_DIR, x)), reverse=True)
            
            # Delete snapshots beyond retention count
            for snapshot_file in snapshots[DB_SNAPSHOT_RETENTION_COUNT:]:
                snapshot_path = os.path.join(SNAPSHOTS_DIR, snapshot_file)
                try:
                    os.remove(snapshot_path)
                    print(f"[INFO] [{PRINT_PREFIX}] Deleted old snapshot: {snapshot_file} (retention limit: {DB_SNAPSHOT_RETENTION_COUNT}).")
                except Exception as e:
                    print(f"[ERROR] [{PRINT_PREFIX}] Failed to delete old snapshot {snapshot_file}: {e}")
    
        print(f"[DEBUG] [{PRINT_PREFIX}] Backup manager loop complete. Sleeping for {interval} seconds.")
    
        time.sleep(interval)