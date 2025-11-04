from fastapi import FastAPI

from app.routes import sample_router

app = FastAPI(
    title="Travel Packer API",
    version="0.1.0",
)

app.include_router(sample_router, prefix="/sample", tags=["sample"])


@app.get("/")
def read_root():
    return {"message": "Hello from travel-packer backend!"}
