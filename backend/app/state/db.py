from typing import Dict

from app.models import Item, RemovalRecommendation, Trip, User

trips_store: Dict[str, Trip] = {}
items_store: Dict[str, Item] = {}
users_store: Dict[str, User] = {}
recommendations_store: Dict[str, RemovalRecommendation] = {}
