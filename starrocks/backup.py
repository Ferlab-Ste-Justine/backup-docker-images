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

    for db in databases:
        print(f"Backing up {db}...", flush=True)
        cmd_utils.submit_backup(conn, db, stamp)
        cmd_utils.poll_backup(conn, db, stamp)
        print(f"{db} FINISHED.", flush=True)

    conn.close()
    duration = (time.time() - start) / 60
    print(f"\nThe script took {duration:.2f} minute(s) to run.", flush=True)
