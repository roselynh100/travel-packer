from fastapi import FastAPI

from app.routes import sample_router, item_router, user_router, trip_router

app = FastAPI(
    title="Travel Packer API",
    version="0.1.0",
)

app.include_router(sample_router, prefix="/sample", tags=["sample"])
app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(trip_router, prefix="/trips", tags=["trips"])
app.include_router(item_router, prefix="/items", tags=["items"])


@app.get("/")
def read_root():
    return {"message": "Hello from travel-packer backend!"}
