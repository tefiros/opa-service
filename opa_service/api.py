# api.py — clean ledger client (no UUID propagation)

import os
import requests
from typing import Any, Dict, Optional, Union


# ------------------------------------------------------------
# Ledger node configuration
# ------------------------------------------------------------

HTTP_PORT = os.getenv("HTTP_PORT", "3001")
NODE_URL = os.getenv("NODE_URL", "http://ledger-ip:3001")


def _url(path: str, node_url: Optional[str] = None) -> str:
    """Construct full ledger node URL."""
    return (node_url or NODE_URL).rstrip("/") + path


def _post(path: str, data: Dict[str, Any], node_url: Optional[str] = None) -> Dict[str, Any]:
    """POST helper with error handling."""
    r = requests.post(_url(path, node_url), json=data, timeout=5)
    if not r.ok:
        raise RuntimeError(f"Ledger error {r.status_code}: {r.text}")
    return r.json()


# ------------------------------------------------------------
# Basic Logging API (no UUIDs)
# ------------------------------------------------------------

def send_log(resource: Union[str, Dict[str, Any]], recipient: str, node_url: Optional[str] = None):
    """
    Create a SEND log.
    :param resource: what is being sent
    :param recipient: destination module
    """
    return _post("/log", {
        "action": "SEND",
        "what": resource,
        "to": recipient
    }, node_url)


def receive_log(resource: Union[str, Dict[str, Any]], sender: str, node_url: Optional[str] = None):
    """
    Create a RECEIVE log.
    :param resource: what is being received
    :param sender: originating module
    """
    return _post("/log", {
        "action": "RECEIVE",
        "what": resource,
        "from": sender
    }, node_url)


def exec_log(resource: str,
             input_data: Any,
             output_data: Any,
             node_url: Optional[str] = None):
    """
    Create an EXEC log.
    :param resource: operation name (e.g., "generate-policy")
    :param input_data: input used by the module
    :param output_data: output produced by the module
    """
    return _post("/log", {
        "action": "EXEC",
        "what": resource,
        "input": input_data,
        "output": output_data
    }, node_url)


def read_log(resource: Union[str, Dict[str, Any]], node_url: Optional[str] = None):
    """
    Create a READ log.
    :param resource: what was read (string or JSON)
    """
    return _post("/log", {
        "action": "READ",
        "what": resource
    }, node_url)