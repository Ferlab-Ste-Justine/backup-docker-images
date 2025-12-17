import datetime
import json
import os
import sys
import time
from typing import Optional
from urllib.parse import quote

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


def build_payload():
    payload = {
        "include_global_state": env_bool("OPENSEARCH_SNAPSHOT_INCLUDE_GLOBAL_STATE", True),
        "ignore_unavailable": env_bool("OPENSEARCH_SNAPSHOT_IGNORE_UNAVAILABLE", False),
        "partial": env_bool("OPENSEARCH_SNAPSHOT_PARTIAL", False),
    }
    indices = os.environ.get("OPENSEARCH_SNAPSHOT_INDICES", "").strip()
    if indices:
        payload["indices"] = indices

    custom_metadata = os.environ.get("OPENSEARCH_SNAPSHOT_METADATA", "").strip()
    if custom_metadata:
        payload["metadata"] = json.loads(custom_metadata)

    return payload


def snapshot_name():
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    safe = (
        timestamp.lower()
        .replace(":", "-")
        .replace("+", "-")
        .replace("/", "-")
    )
    return f"backup-{safe}.dump"


def snapshot_url(endpoint: str, repository: str, snapshot: Optional[str] = None) -> str:
    url = f"{endpoint}/_snapshot/{quote(repository, safe='')}"
    if snapshot:
        url = f"{url}/{quote(snapshot, safe='')}"
    return url


def repository_definition():
    bucket = os.environ.get("OPENSEARCH_REPOSITORY_BUCKET", "").strip()
    endpoint = os.environ.get("OPENSEARCH_REPOSITORY_ENDPOINT", "").strip()
    region = os.environ.get("OPENSEARCH_REPOSITORY_REGION", "").strip()

    if not bucket or not endpoint or not region:
        missing = [name for name, value in [
            ("OPENSEARCH_REPOSITORY_BUCKET", bucket),
            ("OPENSEARCH_REPOSITORY_ENDPOINT", endpoint),
            ("OPENSEARCH_REPOSITORY_REGION", region),
        ] if not value]
        print(
            "Repository is missing and the following variables must be provided to create it: "
            + ", ".join(missing),
            file=sys.stderr,
        )
        sys.exit(1)

    settings = {
        "bucket": bucket,
        "endpoint": endpoint,
        "region": region,
        "protocol": os.environ.get("OPENSEARCH_REPOSITORY_PROTOCOL", "https"),
        "path_style_access": env_bool("OPENSEARCH_REPOSITORY_PATH_STYLE_ACCESS", True),
        "client": os.environ.get("OPENSEARCH_REPOSITORY_CLIENT", "default"),
    }

    base_path = os.environ.get("OPENSEARCH_REPOSITORY_BASE_PATH", "").strip()
    if base_path:
        settings["base_path"] = base_path

    return {"type": "s3", "settings": settings}


def ensure_repository(endpoint: str, repository: str, kwargs):
    url = snapshot_url(endpoint, repository)
    response = requests.get(url, **kwargs)
    if response.status_code == 404:
        payload = repository_definition()
        print(f"Snapshot repository '{repository}' missing. Creating it now.", flush=True)
        create = requests.put(url, json=payload, **kwargs)
        if not create.ok:
            print(
                f"Failed to create snapshot repository '{repository}': "
                f"{create.status_code} {create.text}",
                file=sys.stderr,
                flush=True,
            )
        try:
            create.raise_for_status()
        except requests.HTTPError:
            raise
        return

    if not response.ok:
        print(
            f"Snapshot repository probe failed with {response.status_code}: {response.text}",
            file=sys.stderr,
            flush=True,
        )
    try:
        response.raise_for_status()
    except requests.HTTPError:
        raise


def main():
    start = time.time()
    endpoint = required_env("OPENSEARCH_ENDPOINT").rstrip("/")
    repository = required_env("OPENSEARCH_SNAPSHOT_REPOSITORY")
    wait_for_completion = env_bool("OPENSEARCH_WAIT_FOR_COMPLETION", True)
    kwargs = build_http_kwargs()

    ensure_repository(endpoint, repository, kwargs)
    name = snapshot_name()
    url = snapshot_url(endpoint, repository, name)
    params = {"wait_for_completion": str(wait_for_completion).lower()}
    payload = build_payload()

    print(f"Triggering snapshot '{name}' at {url}")
    response = requests.put(url, params=params, json=payload, **kwargs)
    if not response.ok:
        print(
            f"Snapshot request failed with {response.status_code}: {response.text}",
            file=sys.stderr,
            flush=True,
        )
    response.raise_for_status()

    result = response.json()
    print(json.dumps(result, indent=2))

    duration = (time.time() - start) / 60
    print(f"\nThe script took {duration:.2f} minute(s) to run.")


if __name__ == "__main__":
    main()
