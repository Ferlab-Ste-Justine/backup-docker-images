import os
import sys

import cmd_utils

SR_DATABASE = os.environ.get('SR_DATABASE')
SR_SNAPSHOT = os.environ.get('SR_SNAPSHOT')

if __name__ == "__main__":
    if not SR_DATABASE or not SR_SNAPSHOT:
        print("SR_DATABASE and SR_SNAPSHOT are required.")
        sys.exit(1)

    conn = cmd_utils.get_connection()

    print("Ensuring repository exists...")
    cmd_utils.create_repository(conn)

    print(f"Restoring {SR_DATABASE}/{SR_SNAPSHOT}...")
    cmd_utils.submit_restore(conn, SR_DATABASE, SR_SNAPSHOT)
    cmd_utils.poll_restore(conn, SR_DATABASE, SR_SNAPSHOT)
    print(f"{SR_DATABASE}/{SR_SNAPSHOT} RESTORED.")

    conn.close()
