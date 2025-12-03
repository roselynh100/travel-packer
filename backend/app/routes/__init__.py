from app.routes.item import router as item_router
from app.routes.trip import router as trip_router
from app.routes.user import router as user_router

__all__ = ["item_router", "user_router", "trip_router"]
