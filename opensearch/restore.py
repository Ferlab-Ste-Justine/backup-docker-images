import json
import os
import sys
import time
from typing import Optional
from urllib.parse import quote

import requests
from utils import build_http_kwargs, env_bool, required_env


def snapshot_url(endpoint: str, repository: str, snapshot: Optional[str] = None) -> str:
    url = f"{endpoint}/_snapshot/{quote(repository, safe='')}"
    if snapshot:
        url = f"{url}/{quote(snapshot, safe='')}"
    return url


def latest_snapshot(endpoint: str, repository: str, kwargs):
    url = f"{snapshot_url(endpoint, repository)}/_all"
    response = requests.get(url, **kwargs)
    response.raise_for_status()

    data = response.json()
    snapshots = data.get("snapshots", [])
    if not snapshots:
        print(f"No snapshots found in repository '{repository}'", file=sys.stderr)
        sys.exit(1)

    snapshots.sort(key=lambda snap: snap.get("end_time_in_millis", 0), reverse=True)
    return snapshots[0]["snapshot"]


def build_payload():
    payload = {
        "include_global_state": env_bool("OPENSEARCH_RESTORE_INCLUDE_GLOBAL_STATE", True),
        "ignore_unavailable": env_bool("OPENSEARCH_RESTORE_IGNORE_UNAVAILABLE", False),
        "partial": env_bool("OPENSEARCH_RESTORE_PARTIAL", False),
    }

    indices = os.environ.get("OPENSEARCH_RESTORE_INDICES", "").strip()
    if indices:
        payload["indices"] = indices

    rename_pattern = os.environ.get("OPENSEARCH_RESTORE_RENAME_PATTERN", "").strip()
    if rename_pattern:
        payload["rename_pattern"] = rename_pattern

    rename_replacement = os.environ.get("OPENSEARCH_RESTORE_RENAME_REPLACEMENT", "").strip()
    if rename_replacement:
        payload["rename_replacement"] = rename_replacement

    index_settings = os.environ.get("OPENSEARCH_RESTORE_INDEX_SETTINGS", "").strip()
    if index_settings:
        payload["index_settings"] = json.loads(index_settings)

    return payload


def main():
    start = time.time()
    endpoint = required_env("OPENSEARCH_ENDPOINT").rstrip("/")
    repository = required_env("OPENSEARCH_SNAPSHOT_REPOSITORY")
    wait_for_completion = env_bool("OPENSEARCH_WAIT_FOR_COMPLETION", True)

    kwargs = build_http_kwargs()
    snapshot = os.environ.get("OPENSEARCH_SNAPSHOT_NAME")
    if not snapshot:
        snapshot = latest_snapshot(endpoint, repository, kwargs)

    url = f"{snapshot_url(endpoint, repository, snapshot)}/_restore"
    params = {"wait_for_completion": str(wait_for_completion).lower()}
    payload = build_payload()

    print(f"Restoring snapshot '{snapshot}' from {url}")
    response = requests.post(url, params=params, json=payload, **kwargs)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))

    duration = (time.time() - start) / 60
    print(f"\nThe script took {duration:.2f} minute(s) to run.")


if __name__ == "__main__":
    main()
