__name__ = "OPA Evaluation Service"
__version__ = "1.0.0"

import os
import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Any, Dict, List
from opa_client.opa import OpaClient

from .api import exec_log

## -- BEGIN CONSTANTS DECLARATION -- ##
OPA_HOSTNAME = os.getenv("OPA_HOSTNAME")
OPA_PORT = int(os.getenv("OPA_PORT", "8181"))
## -- END CONSTANTS DECLARATION -- ##

## -- BEGIN Pydantic MODELS -- ##
class EvaluationRequest(BaseModel):
    """
    Request body for POST /evaluate
    - policy_path: The Rego package path to evaluate (e.g., "example")
    - rule_name: The rule inside the package to evaluate (e.g., "allow")
    - input: The input data dictionary for evaluation
    """
    input: Dict[str, Any]


class OpaDecisionResponse(BaseModel):
    """
    Response body for POST /evaluate
    - result: The evaluation result returned by OPA
    """
    result: Dict[str, Any]
## -- END Pydantic MODELS -- ##


## -- BEGIN Helpers -- ##
def get_policy_ids_for_package(package_name: str) -> List[str]:
    matches: List[str] = []

    try:
        policies = opa_client.get_policies_list()

        for pid in policies:
            try:
                p = opa_client.get_policy(pid)
            except Exception as e:
                print("Error fetching policy:", pid, e)
                continue

            raw = (
                p.get("result", {}).get("raw")
                or p.get("raw")
                or ""
            )

            if f"package {package_name}" in raw:
                matches.append(pid)

    except Exception as e:
        print("Error discovering policies by package:", e)

    return matches

## -- END Helpers -- ##

# Initialize FastAPI app
app = FastAPI(
    title=__name__ + " - REST API",
    version=__version__,
)

# Initialize OPA client
opa_client = OpaClient(host=OPA_HOSTNAME, port=int(OPA_PORT))

## -- BEGIN ENDPOINTS -- ##
@app.post(
    path="/v1/data/AccessControl",
    description="Evaluate policies in a Rego package on OPA.",
    tags=["Evaluate"],
    response_model=OpaDecisionResponse,
    responses={
        status.HTTP_200_OK: {"description": "Decision response"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "OPA error"},
    },
)
    
def evaluate_policy(request: EvaluationRequest):
    """
    Sends input data to OPA and returns the result
    """
    try:
            package_name = "AccessControl"

            policy_ids = get_policy_ids_for_package(package_name)

            result = opa_client.query_rule(
                input_data=request.input,
                package_path=package_name,
                rule_name="allow",
            )

            # Generate Accounting Log
            exec_log(
                resource="policy evaluation",
                input_data={
                    "input": request.input,
                    "package": package_name,
                    "policy_ids": policy_ids,
                },
                output_data={
                    "allow": allow,
                    "package": package_name,
                    "policy_ids": policy_ids,
                },
            )

            allow = result.get("result", False)

            return OpaDecisionResponse(
                result={
                    "allow": allow,
                    "policy_ids": policy_ids,
                    "reason": "Access granted" if allow else "Access denied",
                    "status_code": 200 if allow else 403,
                    "headers": {}
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/v1/data/AccessControl/allow")
def evaluate_allow(request: EvaluationRequest):
    try:
        result = opa_client.query_rule(
            input_data=request.input,
            package_path="AccessControl",
            rule_name="allow",
        )

        allow = result.get("result", False)
        return {"result": allow}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
## -- END ENDPOINTS -- ##

# Run the app with uvicorn when executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
