__name__ = "OPA Evaluation Service"
__version__ = "1.0.0"

import os
import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Any, Dict
from opa_client.opa import OpaClient

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
            result = opa_client.query_rule(
                input_data=request.input,
                package_path="AccessControl",
                rule_name="allow",
            )

            allow = result.get("result", False)

            return OpaDecisionResponse(
                result={
                    "allow": allow,
                    "reason": "Access granted" if allow else "Access denied",
                    "status_code": 200 if allow else 403,
                    "headers": {}
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
## -- END ENDPOINTS -- ##

# Run the app with uvicorn when executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
