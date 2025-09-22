import os
import pytest
from opa_client.opa import OpaClient
from fastapi.testclient import TestClient
from opa_service.main import app
import requests

# Configuración
OPA_HOSTNAME = os.getenv("OPA_HOSTNAME")
OPA_PORT = int(os.getenv("OPA_PORT", "8181"))

opa_client = OpaClient(host=OPA_HOSTNAME, port=OPA_PORT)
client = TestClient(app)


def test_allow_user_alice():
    """
    Alice should be allowed by the policy.
    """
    response = client.post(
        "/evaluate",
        json={
            "package_path": "example",
            "rule_name": "allow",
            "input": {"user": "alice"},
        },
    )
    assert response.status_code == 200
    assert response.json()["result"]["result"] is True


def test_deny_other_users():
    """
    Any user other than Alice should be denied.
    """
    response = client.post(
        "/evaluate",
        json={
            "package_path": "example",
            "rule_name": "allow",
            "input": {"user": "bob"},
        },
    )
    assert response.status_code == 200
    assert response.json()["result"]["result"] is False
