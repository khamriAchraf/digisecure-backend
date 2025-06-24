from fastapi import FastAPI

from app.api.v1 import auth, org

app = FastAPI()

app.include_router(auth.router, prefix="/api/v1")
app.include_router(org.router, prefix="/api/v1")


@app.get("/health")
def read_root():
    return {"message": "API is alive"}
