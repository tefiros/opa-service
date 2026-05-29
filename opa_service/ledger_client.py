# ledger_client.py
"""
Ledger client for Python modules.

Zero-configuration usage — just set LEDGER_MODULE_NAME and import:

    # my_service.py
    import ledger_client as ledger

    ledger.read_log("report.pdf")
    ledger.send_log("invoice-99", recipient="client-a")

On first use the client self-registers with the ledger node and persists
the token to a local file. Subsequent imports load the token from that file.
No human intervention required.

Configuration (environment variables):
  LEDGER_MODULE_NAME   Name this module should register as (required)
  LEDGER_NODE_URL      Full URL of the ledger node (default: http://localhost:3001)
  LEDGER_TOKEN_DIR     Directory to store the token file (default: ~/.ledger)
"""

import json
import os
import pathlib
import requests
from typing import Any, Dict, Optional, Union

# ── Configuration ─────────────────────────────────────────────────────────────

_NODE_URL: str = (
    os.getenv("LEDGER_NODE_URL")
    or f"http://localhost:{os.getenv('HTTP_PORT', '3001')}"
).rstrip("/")

_MODULE_NAME: Optional[str] = os.getenv("LEDGER_MODULE_NAME")

_TOKEN_DIR: pathlib.Path = pathlib.Path(
    os.getenv("LEDGER_TOKEN_DIR", pathlib.Path.home() / ".ledger")
)

# Populated lazily on first log call via _ensure_registered()
_token: Optional[str] = None


# ── Token persistence ─────────────────────────────────────────────────────────

def _token_file(module_name: str, node_url: str) -> pathlib.Path:
    """One token file per (module_name, node_url) pair — avoids cross-node collisions."""
    safe_host = node_url.replace("://", "_").replace("/", "_").replace(":", "_")
    return _TOKEN_DIR / f"{module_name}@{safe_host}.json"


def _load_token(module_name: str, node_url: str) -> Optional[str]:
    f = _token_file(module_name, node_url)
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text())["token"]
    except Exception:
        return None


def _save_token(module_name: str, node_url: str, token: str) -> None:
    _TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    f = _token_file(module_name, node_url)
    f.write_text(json.dumps({"module": module_name, "node": node_url, "token": token}))
    # Restrict to owner read/write only — token contains private key material
    f.chmod(0o600)


# ── Auto-registration ─────────────────────────────────────────────────────────

def _ensure_registered(node_url: str) -> str:
    """
    Return the module's Bearer token, registering with the ledger node if needed.

    Flow:
      1. Check in-process cache (_token)
      2. Check token file on disk (~/.ledger/<name>@<node>.json)
      3. POST /modules to self-register, save token to disk
      4. If the name is already taken on the node (409), the token file was
         probably deleted — raise a clear error so the operator knows to either
         restore the file or revoke+re-register the module.
    """
    global _token

    if not _MODULE_NAME:
        raise RuntimeError(
            "LEDGER_MODULE_NAME environment variable is not set. "
            "Set it to a unique name for this service (e.g. 'billing-service')."
        )

    # 1. In-process cache
    if _token:
        return _token

    # 2. Disk cache
    saved = _load_token(_MODULE_NAME, node_url)
    if saved:
        _token = saved
        return _token

    # 3. Self-register
    try:
        r = requests.post(
            f"{node_url}/modules",
            json={"name": _MODULE_NAME},
            timeout=5,
        )
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(f"Cannot reach ledger node at {node_url}: {e}") from e

    if r.status_code == 409:
        # Name already registered but we have no token file — unrecoverable without admin action
        raise RuntimeError(
            f"Module '{_MODULE_NAME}' is already registered on {node_url} but no local token "
            f"file was found at {_token_file(_MODULE_NAME, node_url)}. "
            "Either restore the token file or ask an admin to revoke the module "
            f"(DELETE /modules/{_MODULE_NAME}) so it can re-register."
        )

    if not r.ok:
        raise RuntimeError(f"Registration failed {r.status_code}: {r.text}")

    data   = r.json()
    _token = data["token"]
    _save_token(_MODULE_NAME, node_url, _token)
    print(
        f"[ledger] Registered '{_MODULE_NAME}' with {node_url}. "
        f"Token saved to {_token_file(_MODULE_NAME, node_url)}"
    )
    return _token


# ── Internal HTTP helpers ─────────────────────────────────────────────────────

def _url(path: str, node_url: Optional[str]) -> str:
    return (node_url or _NODE_URL) + path


def _post(
    path: str,
    data: Dict[str, Any],
    node_url: Optional[str] = None,
    authenticated: bool = True,
) -> Dict[str, Any]:
    base = node_url or _NODE_URL
    headers: Dict[str, str] = {}
    if authenticated:
        token = _ensure_registered(base)
        headers["Authorization"] = f"Bearer {token}"
    r = requests.post(_url(path, node_url), json=data, headers=headers, timeout=5)
    if not r.ok:
        raise RuntimeError(f"Ledger error {r.status_code}: {r.text}")
    return r.json()


def _get(path: str, node_url: Optional[str] = None) -> Dict[str, Any]:
    r = requests.get(_url(path, node_url), timeout=5)
    if not r.ok:
        raise RuntimeError(f"Ledger error {r.status_code}: {r.text}")
    return r.json()


# ── Log API ───────────────────────────────────────────────────────────────────

def send_log(
    resource: Union[str, Dict[str, Any]],
    recipient: str,
    node_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a SEND log.
    :param resource:  what is being sent (string or dict)
    :param recipient: identifier of the recipient
    """
    if not recipient or not isinstance(recipient, str):
        raise ValueError("recipient must be a non-empty string")
    return _post("/log", {"action": "SEND", "what": resource, "to": recipient}, node_url)


def receive_log(
    resource: Union[str, Dict[str, Any]],
    sender: str,
    node_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a RECEIVE log.
    :param resource: what is being received (string or dict)
    :param sender:   identifier of the sender
    """
    if not sender or not isinstance(sender, str):
        raise ValueError("sender must be a non-empty string")
    return _post("/log", {"action": "RECEIVE", "what": resource, "from": sender}, node_url)


def exec_log(
    resource: Union[str, Dict[str, Any]],
    input_data: Any,
    output_data: Any,
    node_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create an EXEC log.
    :param resource:    the resource on which execution happens
    :param input_data:  state/parameters before execution
    :param output_data: state/result after execution
    """
    if input_data is None or output_data is None:
        raise ValueError("EXEC logs require both input_data and output_data")
    return _post(
        "/log",
        {"action": "EXEC", "what": resource, "input": input_data, "output": output_data},
        node_url,
    )


def read_log(
    resource: Union[str, Dict[str, Any]],
    node_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a READ log.
    :param resource: what is being read
    """
    return _post("/log", {"action": "READ", "what": resource}, node_url)


# ── Admin helpers (no token required) ────────────────────────────────────────

def propose_block(node_url: Optional[str] = None) -> Dict[str, Any]:
    """Propose a new block with all buffered logs."""
    return _post("/propose", {}, node_url, authenticated=False)


def get_blocks(node_url: Optional[str] = None) -> Dict[str, Any]:
    """Get the full blockchain."""
    return _get("/blocks", node_url)


def get_logs(node_url: Optional[str] = None) -> Dict[str, Any]:
    """Get uncommitted logs currently in the node's pool."""
    return _get("/logs", node_url)


def get_public_key(node_url: Optional[str] = None) -> Dict[str, Any]:
    """Get this node's PoA authority public key."""
    return _get("/public-key", node_url)


def get_status(node_url: Optional[str] = None) -> Dict[str, Any]:
    """Get node status: block count, pending logs, registered modules."""
    return _get("/status", node_url)