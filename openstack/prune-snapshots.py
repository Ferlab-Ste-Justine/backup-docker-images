import datetime
import openstack
import os
import sys
import time

OPENSTACK_VOLUMES = os.environ.get('OPENSTACK_VOLUMES', '')
OPENSTACK_SNAPSHOT_MAX_AGE = int(os.environ.get('OPENSTACK_SNAPSHOT_MAX_AGE', '2592000'))  # default is 30 days
 
if __name__ == "__main__":
    start = time.time()
 
    now = datetime.datetime.now(datetime.timezone.utc)
    max_age = datetime.timedelta(seconds=OPENSTACK_SNAPSHOT_MAX_AGE)
    volumes = [volume.strip() for volume in OPENSTACK_VOLUMES.split(',') if volume.strip()]

    if not volumes:
        print("ERROR: Missing required environment variable 'OPENSTACK_VOLUMES'", file=sys.stderr)
        sys.exit(1)
 
    conn = openstack.connect()

    deleted = 0

    print(f"Deleting expired snapshots older than {OPENSTACK_SNAPSHOT_MAX_AGE} second(s) ...")
    for volume_name in volumes:
        volume = conn.block_storage.find_volume(volume_name, ignore_missing=False)
        for snapshot in conn.block_storage.snapshots(volume_id=volume.id):
            created_at = datetime.datetime.fromisoformat(snapshot.created_at)
            if (now - created_at.replace(tzinfo=datetime.timezone.utc)) >= max_age:
                print(f" - {snapshot.name}")
                conn.block_storage.delete_snapshot(snapshot, ignore_missing=True)
                deleted += 1

    if deleted == 0:
        print("No expired snapshot found.")
 
    duration = (time.time() - start) / 60
    print(f"\nThe script took {duration:.2f} minute(s) to run.")
