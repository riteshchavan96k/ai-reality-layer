from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field

from backend.app.api.errors import (
    unhandled_exception_handler,
    validation_exception_handler,
)
from backend.app.api.request_id import RequestIdMiddleware
from backend.app.services.solve_service import process_task


app = FastAPI(
    title="AI Reality Layer API",
    version="0.1.0",
    description="Production-oriented API surface for AI Reality Layer orchestration.",
)

app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


class SolveRequest(BaseModel):
    task: str = Field(min_length=1, max_length=10_000)
    human_approved: bool = False


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai-reality-layer",
        "version": "0.1.0",
    }


@app.post("/api/v1/solve")
def solve(request: SolveRequest):
    return process_task(request.task, human_approved=request.human_approved)
