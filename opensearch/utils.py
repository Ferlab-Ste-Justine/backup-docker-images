import os
import sys
from typing import Any, Dict, Optional, Tuple, Union


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(
        f"Invalid boolean for {name}: '{value}'. Expected 'true' or 'false'."
    )


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def build_http_kwargs() -> Dict[str, Any]:
    verify: Union[str, bool] = os.environ.get("OPENSEARCH_CA_CERT")
    if not verify:
        verify = not env_bool("OPENSEARCH_SSL_SKIP_VERIFY", False)

    cert: Optional[Union[str, Tuple[str, str]]] = None
    client_cert = os.environ.get("OPENSEARCH_CLIENT_CERT")
    client_key = os.environ.get("OPENSEARCH_CLIENT_KEY")
    if client_cert and client_key:
        cert = (client_cert, client_key)
    elif client_cert:
        cert = client_cert

    username = os.environ.get("OPENSEARCH_USERNAME")
    password = os.environ.get("OPENSEARCH_PASSWORD")
    auth: Optional[Tuple[str, str]] = (username, password) if username and password else None

    return {"verify": verify, "cert": cert, "auth": auth}
