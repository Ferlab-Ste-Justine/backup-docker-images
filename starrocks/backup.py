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

    # submit all databases before polling any — StarRocks snapshot names are globally
    # unique in the repository, so all databases must join the same in-progress snapshot
    # before any one of them commits it
    pending = []
    for db in databases:
        print(f"Submitting backup for {db}...", flush=True)
        if cmd_utils.submit_backup(conn, db, stamp):
            pending.append(db)

    for db in pending:
        print(f"Polling {db}...", flush=True)
        cmd_utils.poll_backup(conn, db, stamp)
        print(f"{db} FINISHED.", flush=True)

    conn.close()
    duration = (time.time() - start) / 60
    print(f"\nThe script took {duration:.2f} minute(s) to run.", flush=True)
