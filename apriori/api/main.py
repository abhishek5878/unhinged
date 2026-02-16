from fastapi import FastAPI

from apriori.api.routes import profiles, simulate

app = FastAPI(
    title="APRIORI",
    description="Relational Foundation Model API",
    version="0.1.0",
)

app.include_router(simulate.router, prefix="/simulate", tags=["simulation"])
app.include_router(profiles.router, prefix="/profiles", tags=["profiles"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
