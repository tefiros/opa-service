import os
import pytest
from opa_client.opa import OpaClient
from fastapi.testclient import TestClient
from opa_service.main import app

# Configuración
OPA_HOSTNAME = os.getenv("OPA_HOSTNAME", "localhost")
OPA_PORT = int(os.getenv("OPA_PORT", "8181"))

opa_client = OpaClient(host=OPA_HOSTNAME, port=OPA_PORT)
client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def load_policy():
    """
    Load the example policy into OPA before running tests.
    """
    policy_file = os.path.join(os.path.dirname(__file__), "example.rego")
    policy_file = os.path.abspath(policy_file)

    opa_client.update_opa_policy_fromfile(policy_file, endpoint="example")
    yield

    opa_client.delete_policy("example")


def test_allow_user_alice():
    """
    Alice should be allowed by the policy.
    """
    response = client.post(
        "/evaluate",
        json={
            "policy_path": "example",
            "rule_name": "allow",
            "input": {"user": "alice"},
        },
    )
    assert response.status_code == 200
    assert response.json()["result"] is True


def test_deny_other_users():
    """
    Any user other than Alice should be denied.
    """
    response = client.post(
        "/evaluate",
        json={
            "policy_path": "example",
            "rule_name": "allow",
            "input": {"user": "bob"},
        },
    )
    assert response.status_code == 200
    assert response.json()["result"] is False
