from __future__ import annotations

from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorDetail(BaseModel):
    code: str = Field(..., examples=["provider_error"])
    message: str = Field(..., examples=["AI provider request failed"])
    type: str = Field(default="governance_error", examples=["governance_error"])
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    event_id: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail


class GovernanceError(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = 400,
        request_id: str | None = None,
        trace_id: str | None = None,
        event_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.request_id = request_id
        self.trace_id = trace_id
        self.event_id = event_id
        self.details = details or {}
        super().__init__(message)


def error_payload(
    *,
    code: str,
    message: str,
    error_type: str,
    request_id: str | None = None,
    trace_id: str | None = None,
    event_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "type": error_type,
            "request_id": request_id,
            "trace_id": trace_id,
            "event_id": event_id,
            "details": details or {},
        }
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(GovernanceError)
    async def governance_error_handler(request: Request, exc: GovernanceError):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(
                code=exc.code,
                message=exc.message,
                error_type="governance_error",
                request_id=exc.request_id,
                trace_id=exc.trace_id,
                event_id=exc.event_id,
                details=exc.details,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        detail = exc.detail
        if isinstance(detail, dict):
            code = detail.get("code", "http_error")
            message = detail.get("message", str(detail))
            request_id = detail.get("request_id")
            trace_id = detail.get("trace_id")
            event_id = detail.get("event_id")
            details = detail.get("details", {})
        else:
            code = "http_error"
            message = str(detail)
            request_id = None
            trace_id = None
            event_id = None
            details = {}

        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(
                code=code,
                message=message,
                error_type="http_error",
                request_id=request_id,
                trace_id=trace_id,
                event_id=event_id,
                details=details,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error_payload(
                code="validation_error",
                message="Request validation failed",
                error_type="validation_error",
                details={"errors": exc.errors()},
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=error_payload(
                code="internal_server_error",
                message="An unexpected internal error occurred",
                error_type="internal_error",
            ),
        )
