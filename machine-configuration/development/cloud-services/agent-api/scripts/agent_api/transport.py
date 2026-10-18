from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from agent_api.catalog import describe, discover, providers
from agent_api.contract import MAXIMUM_REQUEST_BYTES, CapabilityError, OperationRequest
from agent_api.service import CapabilityService


class OperationBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    capability: str = Field(min_length=1, max_length=100)
    input: dict[str, Any]
    timeout_seconds: int = Field(default=180, ge=1, le=600, strict=True)
    allow_paid: StrictBool = False


def create_app(state_directory):
    app = FastAPI(title="Private agent capability API", version="1.0.0")
    service = CapabilityService(state_directory)

    @app.exception_handler(CapabilityError)
    async def capability_error(request: Request, error: CapabilityError):
        category = str(error)
        status = 422
        if category == "operation_not_found":
            status = 404
        elif category in (
            "operation_conflict",
            "operation_incomplete",
            "capacity_exceeded",
        ):
            status = 409
        elif category in (
            "network_failed",
            "provider_failed",
            "worker_failed",
            "execution_failed",
        ):
            status = 502
        elif category == "deadline_exceeded":
            status = 504
        return JSONResponse(status_code=status, content={"error": category})

    @app.middleware("http")
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

    @app.get("/v1/providers")
    def list_providers():
        return {"providers": providers()}

    @app.get("/v1/capabilities")
    def discover_capabilities(query: str = "", provider: str | None = None):
        return {"capabilities": discover(query, provider)}

    @app.get("/v1/capabilities/{capability_id}")
    def inspect_capability(capability_id: str):
        return describe(capability_id)

    @app.put("/v1/operations/{operation_id}")
    def execute(operation_id: str, body: OperationBody):
        return service.run(operation_id, OperationRequest(**body.model_dump()))

    @app.get("/v1/operations/{operation_id}")
    def inspect_operation(operation_id: str):
        return service.store.inspect(operation_id)

    @app.get("/v1/operations/{operation_id}/artifacts/{filename}")
    def artifact(operation_id: str, filename: str):
        receipt = service.store.inspect(operation_id)
        if receipt["status"] != "succeeded" or filename not in {
            entry["path"] for entry in receipt["artifacts"]
        }:
            raise HTTPException(status_code=404, detail="artifact_not_found")
        return FileResponse(Path(service.store.directory(operation_id)) / filename)

    return app
