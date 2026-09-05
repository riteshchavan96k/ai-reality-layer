from fastapi import FastAPI
from pydantic import BaseModel
from backend.app.services.solve_service import process_task


app = FastAPI()


class SolveRequest(BaseModel):
    task: str
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
