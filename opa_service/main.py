__name__ = "OPA Evaluation Service"
__version__ = "0.1.0"

import os
import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Any, Dict
from opa_client.opa import OpaClient

## -- BEGIN CONSTANTS DECLARATION -- ##
# OPA connection settings via environment variables (default to localhost:8181)
OPA_HOSTNAME = os.getenv("OPA_HOSTNAME", "localhost")
OPA_PORT = os.getenv("OPA_PORT", "8181")
## -- END CONSTANTS DECLARATION -- ##

## -- BEGIN Pydantic MODELS -- ##
class EvaluationRequest(BaseModel):
    """
    Request body for POST /evaluate
    - policy_path: The Rego package path to evaluate (e.g., "example")
    - rule_name: The rule inside the package to evaluate (e.g., "allow")
    - input: The input data dictionary for evaluation
    """
    policy_path: str
    rule_name: str
    input: Dict[str, Any]

class EvaluationResponse(BaseModel):
    """
    Response body for POST /evaluate
    - result: The evaluation result returned by OPA
    """
    result: Any
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
    path="/evaluate",
    description="Evaluate a specific rule in a Rego package on OPA.",
    tags=["Evaluate"],
    responses={
        status.HTTP_200_OK: {"model": EvaluationResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": str},
    },
)
def evaluate_policy(request: EvaluationRequest):
    """
    Sends input data to OPA and returns the result of the specified rule evaluation.
    """
    try:
        # Use the recommended query_rule() method from opa-python-client
        result = opa_client.query_rule(
            input_data=request.input,
            package_path=request.policy_path,
            rule_name=request.rule_name
        )
        return {"result": result}
    except Exception as e:
        # Return a 500 HTTP error with exception details
        raise HTTPException(status_code=500, detail=str(e))
## -- END ENDPOINTS -- ##

# Run the app with uvicorn when executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
