import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List

import requests


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def build_http_kwargs():
    verify = os.environ.get("OPENSEARCH_CA_CERT")
    if not verify:
        verify = not env_bool("OPENSEARCH_SSL_SKIP_VERIFY", False)

    cert = None
    client_cert = os.environ.get("OPENSEARCH_CLIENT_CERT")
    client_key = os.environ.get("OPENSEARCH_CLIENT_KEY")
    if client_cert and client_key:
        cert = (client_cert, client_key)
    elif client_cert:
        cert = client_cert

    username = os.environ.get("OPENSEARCH_USERNAME")
    password = os.environ.get("OPENSEARCH_PASSWORD")
    auth = (username, password) if username and password else None

    return {"verify": verify, "cert": cert, "auth": auth}


def snapshot_url(endpoint: str, repository: str, snapshot: str = "") -> str:
    base = f"{endpoint}/_snapshot/{repository}"
    return f"{base}/{snapshot}" if snapshot else base


def list_snapshots(endpoint: str, repository: str, kwargs):
    url = f"{snapshot_url(endpoint, repository)}/_all"
    response = requests.get(url, **kwargs)
    response.raise_for_status()
    data = response.json()
    snapshots: List[dict] = data.get("snapshots", [])
    snapshots.sort(key=lambda snap: snap.get("end_time_in_millis", 0))
    return snapshots


def delete_snapshot(endpoint: str, repository: str, snapshot: str, kwargs):
    url = snapshot_url(endpoint, repository, snapshot)
    response = requests.delete(url, **kwargs)
    if not response.ok:
        print(
            f"Failed to delete snapshot '{snapshot}': {response.status_code} {response.text}",
            file=sys.stderr,
        )
    response.raise_for_status()


def cleanup_repository(endpoint: str, repository: str, kwargs):
    url = f"{snapshot_url(endpoint, repository)}/_cleanup"
    response = requests.post(url, **kwargs)
    if not response.ok:
        print(
            f"Cleanup failed for repository '{repository}': {response.status_code} {response.text}",
            file=sys.stderr,
        )
    response.raise_for_status()
    return response.json()


def main():
    start = time.time()
    endpoint = required_env("OPENSEARCH_ENDPOINT").rstrip("/")
    repository = required_env("OPENSEARCH_SNAPSHOT_REPOSITORY")
    max_age_days = int(os.environ.get("OPENSEARCH_PRUNE_MAX_AGE_DAYS", "60"))
    min_snapshots = int(os.environ.get("OPENSEARCH_PRUNE_MIN_SNAPSHOTS", "0"))
    dry_run = env_bool("OPENSEARCH_PRUNE_DRY_RUN", False)

    kwargs = build_http_kwargs()
    snapshots = list_snapshots(endpoint, repository, kwargs)

    if not snapshots:
        print("No snapshots found, nothing to prune.")
        return

    now = datetime.utcnow()
    cutoff = now - timedelta(days=max_age_days)
    cutoff_ms = int(cutoff.timestamp() * 1000)

    expired = [s for s in snapshots if s.get("end_time_in_millis", 0) <= cutoff_ms]

    if not expired:
        print("No snapshots are older than the retention window.")
        return

    deletable_budget = len(snapshots) - min_snapshots
    if deletable_budget <= 0:
        print(
            "Retention min snapshot threshold prevents pruning (set OPENSEARCH_PRUNE_MIN_SNAPSHOTS lower)."
        )
        return

    to_delete = expired[:deletable_budget]

    if not to_delete:
        print("Nothing to delete after applying min snapshot constraint.")
        return

    print(f"Deleting {len(to_delete)} snapshot(s) older than {max_age_days} days" + (" (dry-run)" if dry_run else ""))
    for snapshot in to_delete:
        name = snapshot.get("snapshot")
        finished = snapshot.get("end_time")
        print(f" - {name} (ended {finished})")
        if not dry_run:
            delete_snapshot(endpoint, repository, name, kwargs)

    if not dry_run:
        cleanup = cleanup_repository(endpoint, repository, kwargs)
        deleted_bytes = cleanup.get("results", {}).get("deleted_bytes", 0)
        deleted_blobs = cleanup.get("results", {}).get("deleted_blobs", 0)
        print(f"Cleanup released {deleted_bytes} bytes across {deleted_blobs} blob(s)")

    duration = (time.time() - start) / 60
    print(f"\nThe script took {duration:.2f} minute(s) to run.")


+if __name__ == "__main__":
+    main()
