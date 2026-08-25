from fastapi import FastAPI

app = FastAPI(
    title="AI Reality Layer",
    description="AI Reality Layer backend",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai-reality-layer",
        "version": "0.1.0",
    }