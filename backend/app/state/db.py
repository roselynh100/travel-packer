from typing import Dict
from app.models import Trip, Item, User

trips_store: Dict[str, Trip] = {}
items_store: Dict[str, Item] = {}
users_store: Dict[str, User] = {}
