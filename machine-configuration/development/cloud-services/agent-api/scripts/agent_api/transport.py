from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from agent_api.catalog import describe, discover, providers
from agent_api.contract import MAXIMUM_REQUEST_BYTES, CapabilityError, OperationRequest
from agent_api.service import CapabilityService

ERROR_STATUS = {
    "operation_not_found": 404,
    "operation_conflict": 409,
    "operation_incomplete": 409,
    "capacity_exceeded": 409,
    "network_failed": 502,
    "provider_failed": 502,
    "worker_failed": 502,
    "execution_failed": 502,
    "deadline_exceeded": 504,
}


class OperationBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    capability: str = Field(min_length=1, max_length=100)
    input: dict[str, Any]
    timeout_seconds: int = Field(default=180, ge=1, le=600, strict=True)
    allow_paid: StrictBool = False


async def capability_error(request: Request, error: CapabilityError):
    category = str(error)
    return JSONResponse(
        status_code=ERROR_STATUS.get(category, 422), content={"error": category}
    )


async def bounded_body(request: Request, call_next):
    if request.method in ("PUT", "POST"):
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > MAXIMUM_REQUEST_BYTES:
                return JSONResponse(
                    status_code=413, content={"error": "request_too_large"}
                )
        request._body = bytes(body)
    return await call_next(request)


def list_providers():
    return {"providers": providers()}


def discover_capabilities(query: str = "", provider: str | None = None):
    return {"capabilities": discover(query, provider)}


def inspect_capability(capability_id: str):
    return describe(capability_id)


def execute(request: Request, operation_id: str, body: OperationBody):
    return request.app.state.service.run(
        operation_id, OperationRequest(**body.model_dump())
    )


def inspect_operation(request: Request, operation_id: str):
    return request.app.state.service.store.inspect(operation_id)


def artifact(request: Request, operation_id: str, filename: str):
    store = request.app.state.service.store
    receipt = store.inspect(operation_id)
    if receipt["status"] != "succeeded":
        raise HTTPException(status_code=404, detail="artifact_not_found")
    filenames = {entry["path"] for entry in receipt["artifacts"]}
    if filename not in filenames:
        raise HTTPException(status_code=404, detail="artifact_not_found")
    return FileResponse(store.directory(operation_id) / filename)


def create_app(state_directory):
    app = FastAPI(title="Private agent capability API", version="1.0.0")
    app.state.service = CapabilityService(state_directory)
    app.add_exception_handler(CapabilityError, capability_error)
    app.middleware("http")(bounded_body)
    app.get("/v1/providers")(list_providers)
    app.get("/v1/capabilities")(discover_capabilities)
    app.get("/v1/capabilities/{capability_id}")(inspect_capability)
    app.put("/v1/operations/{operation_id}")(execute)
    app.get("/v1/operations/{operation_id}")(inspect_operation)
    app.get("/v1/operations/{operation_id}/artifacts/{filename}")(artifact)
    return app
