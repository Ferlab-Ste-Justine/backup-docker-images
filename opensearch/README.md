# About

This image manages OpenSearch snapshots using the cluster’s native snapshot repository. It simply triggers the REST APIs, so OpenSearch itself handles the data transfer to S3 (or any other repository backend) and keeps the incremental relationships between snapshots.

# Usage

The image contains three scripts that are meant to be run separately, following the same convention as the other database backup images in this repository.

Before running the scripts you must have:

- An OpenSearch cluster reachable from the container.
- A configured snapshot repository (see the [OpenSearch documentation](https://docs.opensearch.org/latest/tuning-your-cluster/availability-and-recovery/snapshots/snapshot-restore/)).
- Appropriate TLS material or credentials (client certificate/key, HTTP basic auth, etc.).

Unless mentioned otherwise, all scripts accept the following environment variables:

- `OPENSEARCH_ENDPOINT` (required): Base URL of the OpenSearch cluster, e.g. `https://opensearch:9200`.
- `OPENSEARCH_SNAPSHOT_REPOSITORY` (required): Name of the repository configured in OpenSearch.
- `OPENSEARCH_CLIENT_CERT` / `OPENSEARCH_CLIENT_KEY`: Paths to the client certificate and key if certificate-based auth is used.
- `OPENSEARCH_CA_CERT`: CA certificate used to validate the endpoint. Defaults to the system store unless `OPENSEARCH_SSL_SKIP_VERIFY` is set to `true`.
- `OPENSEARCH_SSL_SKIP_VERIFY`: Set to `true` to skip TLS verification (not recommended).
- `OPENSEARCH_USERNAME` / `OPENSEARCH_PASSWORD`: Basic-auth credentials.
- `OPENSEARCH_WAIT_FOR_COMPLETION`: Whether the API calls should block until completion (`true` by default).

## /opt/backup.py

Triggers a snapshot in the configured repository. The snapshot name uses the `backup-<timestamp>.dump` convention shared by the other images in this repo (for example `backup-2024-06-09T12:45:03.000000+00:00.dump`), so external tooling can reason about ordering.

Additional environment variables:

- `OPENSEARCH_SNAPSHOT_INDICES`: Comma-separated list of indices to include. Leave empty to snapshot everything.
- `OPENSEARCH_SNAPSHOT_INCLUDE_GLOBAL_STATE`: Defaults to `true`.
- `OPENSEARCH_SNAPSHOT_IGNORE_UNAVAILABLE`: Defaults to `false`.
- `OPENSEARCH_SNAPSHOT_PARTIAL`: Defaults to `false`.
- `OPENSEARCH_SNAPSHOT_METADATA`: Optional JSON object injected into the snapshot metadata.
- `OPENSEARCH_REPOSITORY_BUCKET`, `OPENSEARCH_REPOSITORY_ENDPOINT`, `OPENSEARCH_REPOSITORY_REGION`: Required only if the repository does not exist yet; the script will create it automatically when missing.
- `OPENSEARCH_REPOSITORY_PROTOCOL`: Optional protocol override (defaults to `https`).
- `OPENSEARCH_REPOSITORY_BASE_PATH`: Optional base path within the bucket.
- `OPENSEARCH_REPOSITORY_PATH_STYLE_ACCESS`: Defaults to `true`.
- `OPENSEARCH_REPOSITORY_CLIENT`: Name of the S3 client configured in the OpenSearch keystore (defaults to `default`).

Example:

```bash
docker run --rm \
  -e OPENSEARCH_ENDPOINT=https://opensearch:9200 \
  -e OPENSEARCH_SNAPSHOT_REPOSITORY=logs \
  -e OPENSEARCH_CLIENT_CERT=/secrets/admin.crt \
  -e OPENSEARCH_CLIENT_KEY=/secrets/admin.key \
  -e OPENSEARCH_CA_CERT=/secrets/ca.crt \
  -v $PWD/secrets:/secrets:ro \
  ferlabcrsj/opensearch-backup:latest \
  python /opt/backup.py
```

## /opt/prune-backups.py

This is the generic pruning script shared with the other images. If you mirror the OpenSearch snapshot state into a secondary object store or log file using the same naming scheme, you can delete aged artifacts by setting `S3_ENDPOINT`, `S3_BUCKET`, etc., exactly like the other images.

**Important**: Deleting snapshot objects directly from the repository will corrupt incremental snapshots. Prefer the OpenSearch `_snapshot/<repo>/<snapshot>` DELETE API or the repository cleanup API and use `S3_BACKUP_MAX_AGE` with caution.

## /opt/prune_snapshots.py

Deletes OpenSearch snapshots older than a retention window using the native `_snapshot` APIs, then calls `_snapshot/<repo>/_cleanup` to free orphaned blobs. Typical environment variables:

- `OPENSEARCH_PRUNE_MAX_AGE_DAYS`: Age threshold in days (defaults to `60`).
- `OPENSEARCH_PRUNE_MIN_SNAPSHOTS`: Minimum number of snapshots to keep regardless of age (defaults to `0`).
- `OPENSEARCH_PRUNE_DRY_RUN`: Set to `true` to see which snapshots would be removed without actually deleting them.

The script reuses the same TLS/basic-auth environment variables as `backup.py`/`restore.py`.

## /opt/restore.py

Restores a snapshot using the OpenSearch API. If `OPENSEARCH_SNAPSHOT_NAME` is omitted, the script automatically restores the most recent snapshot in the repository (based on `end_time_in_millis`).

Additional environment variables:

- `OPENSEARCH_SNAPSHOT_NAME`: Snapshot name to restore (optional).
- `OPENSEARCH_RESTORE_INDICES`: Comma-separated list of indices to restore.
- `OPENSEARCH_RESTORE_INCLUDE_GLOBAL_STATE`: Defaults to `true`.
- `OPENSEARCH_RESTORE_IGNORE_UNAVAILABLE`: Defaults to `false`.
- `OPENSEARCH_RESTORE_PARTIAL`: Defaults to `false`.
- `OPENSEARCH_RESTORE_RENAME_PATTERN`: Optional regex rename pattern.
- `OPENSEARCH_RESTORE_RENAME_REPLACEMENT`: Optional rename replacement.
- `OPENSEARCH_RESTORE_INDEX_SETTINGS`: JSON object merged into the restored indices.

Example:

```bash
docker run --rm \
  -e OPENSEARCH_ENDPOINT=https://opensearch:9200 \
  -e OPENSEARCH_SNAPSHOT_REPOSITORY=logs \
  -e OPENSEARCH_SNAPSHOT_NAME=backup-2024-06-09T12:45:03.000000+00:00.dump \
  -e OPENSEARCH_CLIENT_CERT=/secrets/admin.crt \
  -e OPENSEARCH_CLIENT_KEY=/secrets/admin.key \
  -e OPENSEARCH_CA_CERT=/secrets/ca.crt \
  -v $PWD/secrets:/secrets:ro \
  ferlabcrsj/opensearch-backup:latest \
  python /opt/restore.py
```

# Notes on Snapshot Retention

OpenSearch snapshots are incremental, so each snapshot depends on the previous history within the repository. Deleting the base layers directly in the repository will make later snapshots unusable. Use index lifecycle policies and the OpenSearch snapshot management APIs to control retention, and test the full restore workflow (take multiple snapshots, tear down the cluster, and restore) to validate the automation.
