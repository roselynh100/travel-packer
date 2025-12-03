from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import item_router, trip_router, user_router

app = FastAPI(
    title="Travel Packer API",
    version="0.1.0",
)

origins = [
    "http://localhost:8081",
    "http://127.0.0.1:8081",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(trip_router, prefix="/trips", tags=["trips"])
app.include_router(item_router, prefix="/items", tags=["items"])


@app.get("/")
def read_root():
    return {"message": "Hello from travel-packer backend!"}
