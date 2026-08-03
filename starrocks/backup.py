import datetime
import time

import cmd_utils

if __name__ == "__main__":
    start = time.time()
    stamp = datetime.datetime.now().strftime('%Y%m%d')

    conn = cmd_utils.get_connection()

    print("Creating repository...", flush=True)
    cmd_utils.create_repository(conn)

    databases = cmd_utils.get_user_databases(conn)
    print(f"Databases to backup: {databases}", flush=True)

    # StarRocks snapshot names are globally unique in the repository — use per-database
    # names (snap_{stamp}_{db}) so databases never conflict with each other
    pending = []
    for db in databases:
        db_stamp = f"{stamp}_{db}"
        print(f"Submitting backup for {db}...", flush=True)
        if cmd_utils.submit_backup(conn, db, db_stamp):
            pending.append((db, db_stamp))

    for db, db_stamp in pending:
        print(f"Polling {db}...", flush=True)
        cmd_utils.poll_backup(conn, db, db_stamp)
        print(f"{db} FINISHED.", flush=True)

    conn.close()
    duration = (time.time() - start) / 60
    print(f"\nThe script took {duration:.2f} minute(s) to run.", flush=True)
