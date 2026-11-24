from fastapi import FastAPI

app = FastAPI(title="SITRA Viewer API", version="0.1.0")


@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
