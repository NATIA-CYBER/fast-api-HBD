from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from bdi_api.s1 import exercise

app = FastAPI(
    title="BDI Aircraft API",
    description="Big Data Infrastructure Aircraft API",
    version="0.1.0"
)

@app.get("/")
def root():
    """Redirect to API documentation."""
    return RedirectResponse(url="/docs")

app.include_router(exercise.s1, prefix="/api")
