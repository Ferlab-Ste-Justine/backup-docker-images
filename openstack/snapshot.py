import datetime
import openstack
import os
import sys
import time

OPENSTACK_VOLUMES = os.environ.get('OPENSTACK_VOLUMES', '')
OPENSTACK_SNAPSHOT_TIMEOUT = int(os.environ.get('OPENSTACK_SNAPSHOT_TIMEOUT', '3600'))  # default is 1 hour

if __name__ == "__main__":
    start = time.time()

    now = datetime.datetime.now().isoformat()
    volumes = [volume.strip() for volume in OPENSTACK_VOLUMES.split(',') if volume.strip()]

    if not volumes:
        print("ERROR: Missing required environment variable 'OPENSTACK_VOLUMES'", file=sys.stderr)
        sys.exit(1)

    conn = openstack.connect()

    for volume_name in volumes:
        volume = conn.block_storage.find_volume(volume_name, ignore_missing=False)
        name = f"{volume.name}_snapshot_{now}"
        print(f"Snapshotting volume '{volume.name}' as '{name}' ...")
        snapshot = conn.block_storage.create_snapshot(
            volume_id=volume.id,
            name=name,
            force=True  # needed to snapshot a volume attached to a running instance
        )
        conn.block_storage.wait_for_status(
            snapshot,
            status='available',
            failures=['error'],
            wait=OPENSTACK_SNAPSHOT_TIMEOUT
        )

    duration = (time.time() - start) / 60
    print(f"\nThe script took {duration:.2f} minute(s) to run.")
