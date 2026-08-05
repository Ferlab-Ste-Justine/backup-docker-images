# About

This image takes snapshots of OpenStack volumes and deletes old ones.

# Usage

The image contains two scripts that are meant to be run separately, following the same convention as the other backup images in this repository.

Authentication uses the standard `OS_*` environment variables.

## Snapshot creation (`/opt/snapshot.py`)

> [!IMPORTANT]
>
> Before snapshotting a root volume that has cloud-init: make sure cloud-init is disabled, so a new instance using a restored root volume will not reprovision itself. An easy way to do this is by creating a `/etc/cloud/cloud-init.disabled` file (see [How to disable cloud-init](https://docs.cloud-init.io/en/latest/howto/disable_cloud_init.html#how-to-disable-cloud-init)).

This script creates a snapshot for each specified volume listed. Snapshots are named `<volume_name>_snapshot_<timestamp>`.

Variables in addition to `OS_*` ones:
- `OPENSTACK_VOLUMES`: comma separated list of volume names or ids to act on.
- `OPENSTACK_SNAPSHOT_TIMEOUT`: how long to wait, in seconds, for a snapshot to become available (defaults to 3600 which is 1 hour)

Command:
```bash
docker run --rm \
  -e OS_AUTH_URL=<auth_url> \
  -e OS_AUTH_TYPE=v3applicationcredential \
  -e OS_APPLICATION_CREDENTIAL_ID=<app_cred_id> \
  -e OS_APPLICATION_CREDENTIAL_SECRET=<app_cred_secret> \
  -e OPENSTACK_VOLUMES=<volume_name_1>,<volume_name_2>,<volume_name_3> \
  -e OPENSTACK_SNAPSHOT_TIMEOUT=<snapshot_timeout> \
  ferlabcrsj/openstack-backup:latest \
  python /opt/snapshot.py
```

## Snapshot pruning (`/opt/prune-snapshots.py`)

This script deletes the snapshots of specified volumes that are older than the retention window.

Variables in addition to `OS_*` ones:
- `OPENSTACK_VOLUMES`: comma separated list of volume names or ids to act on.
- `OPENSTACK_SNAPSHOT_MAX_AGE`: retention window in seconds (defaults to 2592000 which is 30 days)

Command:
```bash
docker run --rm \
  -e OS_AUTH_URL=<auth_url> \
  -e OS_AUTH_TYPE=v3applicationcredential \
  -e OS_APPLICATION_CREDENTIAL_ID=<app_cred_id> \
  -e OS_APPLICATION_CREDENTIAL_SECRET=<app_cred_secret> \
  -e OPENSTACK_VOLUMES=<volume_name_1>,<volume_name_2>,<volume_name_3> \
  -e OPENSTACK_SNAPSHOT_MAX_AGE=<snapshot_max_age> \
  ferlabcrsj/openstack-backup:latest \
  python /opt/prune-snapshots.py
```

# Snapshot restoring (manual)

A script to restore a snapshot was not created. If your instance and its volume were created with Terraform, you can follow these steps:
1. Get the desired snapshot ID
2. Create a new volume that points to this snapshot ID (using argument `snapshot_id` in resource `openstack_blockstorage_volume_v3`)
3. Change the volume used by your instance, which will destroy it and create a new one so **make sure that this is really what you want to do**
4. Update `OPENSTACK_VOLUMES` for both scripts to consider the new volume
5. Remember to delete the old volume at some point in the future (when there's no snapshot linked to it anymore, otherwise its deletion is not possible)

Note that snapshotting an attached volume is crash-consistent, not application-consistent. A database that is mid-write during a snapshot would be restore the way it would come back from an unclean shutdown. For databases, keep using the database backup images in this repository. Also, a volume snapshot holds no instance metadata (flavor, networks, ...). Restoring a snapshot means creating a volume from it and booting an instance from that volume, so the instance definition itself should live somewhere like in Terraform.

# Known Limitation

## No Verification For Number of Snapshots Held

Technically, you may find yourself without snapshots if:
  - You run both scripts
  - The snapshot script stops functioning and the situation is not addressed

So you should monitor the snapshot script and address the situation in a timely manner if it stops working (a sane operating procedure either way, you don't want to rely on snapshots that are too old).
