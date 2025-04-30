from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from bdi_api.s1.exercise import s1

app = FastAPI(
    title="BDI Aircraft API",
    description="Big Data Infrastructure Aircraft API",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Redirect root to API documentation"""
    return RedirectResponse(url="/docs")

app.include_router(s1)
