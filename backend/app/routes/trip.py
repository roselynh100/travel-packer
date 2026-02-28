import datetime
import json
from typing import List, Optional

import requests
from fastapi import APIRouter, HTTPException

from app.models import (
    Activity,
    Airline,
    Item,
    RecommendedItem,
    RemovalRecommendation,
    Trip,
    TripUpdate,
)
from app.state.db import items_store, trips_store, users_store
from constants import (
    OPENWEATHER_GEOCODING_URL,
    OPENWEATHER_GEOCODING_USA_URL,
    OPENWEATHERMAP_API_KEY,
    OPENWEATHERMAP_FORECAST_URL,
    OPENWEATHERMAP_HISTORY_URL,
)
from machine_learning.generator import baseline_list_algorithm
from machine_learning.optimizer import packing_decision_algorithm

router = APIRouter()

FORECAST_WINDOW_DAYS = 16


def _kelvin_to_celsius(temp_k: float) -> float:
    return temp_k - 273.15


def _safe_prev_year_date(d: datetime.date) -> datetime.date:
    """Return the same month/day in the previous year, handling Feb 29."""
    try:
        return d.replace(year=d.year - 1)
    except ValueError:
        # Feb 29 -> Feb 28 on non-leap years
        return d.replace(year=d.year - 1, day=28)


def _get_lat_lon_for_trip(trip: Trip) -> tuple[float, float]:
    details = trip.destination_details
    city = details.city
    state = details.state
    country = details.country

    country_norm = country.strip().lower()
    is_usa = country_norm in {"us", "usa", "united states", "united states of america"}

    if state and is_usa:
        geocode_url = OPENWEATHER_GEOCODING_USA_URL.format(
            city_name=city,
            state_code=state,
            country_code=country,
            limit=1,
            OPENWEATHERMAP_API_KEY=OPENWEATHERMAP_API_KEY,
        )
    else:
        geocode_url = OPENWEATHER_GEOCODING_URL.format(
            city_name=city,
            country_code=country,
            limit=1,
            OPENWEATHERMAP_API_KEY=OPENWEATHERMAP_API_KEY,
        )

    geocode_resp = requests.get(geocode_url, timeout=15)
    if not geocode_resp.ok:
        raise HTTPException(
            status_code=geocode_resp.status_code,
            detail="Failed to geocode destination",
        )

    geocode_data = geocode_resp.json()
    if not geocode_data:
        raise HTTPException(status_code=404, detail="Destination not found")

    lat = geocode_data[0].get("lat")
    lon = geocode_data[0].get("lon")
    if lat is None or lon is None:
        raise HTTPException(
            status_code=502, detail="Geocoding response missing lat/lon"
        )

    return float(lat), float(lon)


def _extract_kelvin_temps(entry: dict) -> List[float]:
    """Extract any temperature-like values (in Kelvin) from an OpenWeather entry."""
    temps: List[float] = []

    main = entry.get("main") or {}
    temp_block = entry.get("temp") or {}

    for key in ("temp_min", "temp_max", "temp"):
        value = main.get(key)
        if isinstance(value, (int, float)):
            temps.append(float(value))

    for key in ("min", "max", "day", "eve", "morn", "night"):
        value = temp_block.get(key)
        if isinstance(value, (int, float)):
            temps.append(float(value))

    return temps


def _rain_amount(entry: dict) -> float:
    """Best-effort extraction of rain amount (mm) from an OpenWeather entry."""
    rain_value = entry.get("rain")
    if isinstance(rain_value, (int, float)):
        return float(rain_value)
    if isinstance(rain_value, dict):
        total = 0.0
        for value in rain_value.values():
            if isinstance(value, (int, float)):
                total += float(value)
        return total
    return 0.0


def _is_rainy_entry(entry: dict) -> bool:
    """Determine whether an OpenWeather entry indicates rain."""
    if _rain_amount(entry) > 0:
        return True

    pop = entry.get("pop")
    if isinstance(pop, (int, float)) and float(pop) > 0:
        return True

    weather_list = entry.get("weather") or []
    for weather in weather_list:
        main = (weather or {}).get("main")
        if isinstance(main, str) and main.lower() == "rain":
            return True

    return False


def _precipitation_percentage(rainy_days: int, total_days: int) -> float:
    if total_days <= 0:
        return 0.0
    return (rainy_days / total_days) * 100.0


def _get_forecast_stats(
    lat: float, lon: float, start: datetime.date, end: datetime.date, trip_days: int
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    forecast_url = OPENWEATHERMAP_FORECAST_URL.format(
        lat=lat,
        lon=lon,
        cnt=FORECAST_WINDOW_DAYS,
        OPENWEATHERMAP_API_KEY=OPENWEATHERMAP_API_KEY,
    )
    resp = requests.get(forecast_url, timeout=15)
    if not resp.ok:
        raise HTTPException(
            status_code=resp.status_code,
            detail="Failed to fetch forecast data",
        )

    data = resp.json()
    forecast_list = data.get("list") or []

    lows: List[float] = []
    highs: List[float] = []
    rainy_dates: set[datetime.date] = set()

    for entry in forecast_list:
        dt_value = entry.get("dt")
        if not isinstance(dt_value, (int, float)):
            continue
        entry_date = datetime.datetime.utcfromtimestamp(dt_value).date()
        if not (start <= entry_date <= end):
            continue

        temp_block = entry.get("temp") or {}
        min_k = temp_block.get("min")
        max_k = temp_block.get("max")
        if isinstance(min_k, (int, float)):
            lows.append(_kelvin_to_celsius(float(min_k)))
        if isinstance(max_k, (int, float)):
            highs.append(_kelvin_to_celsius(float(max_k)))

        if _is_rainy_entry(entry):
            rainy_dates.add(entry_date)

    if not lows or not highs:
        return None, None, None

    precip_pct = _precipitation_percentage(len(rainy_dates), trip_days)
    return min(lows), max(highs), precip_pct


def _get_historical_stats(
    lat: float, lon: float, start: datetime.date, end: datetime.date, trip_days: int
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    prev_year_start = _safe_prev_year_date(start)
    prev_year_end = _safe_prev_year_date(end)

    start_dt = datetime.datetime.combine(
        prev_year_start, datetime.time.min, tzinfo=datetime.timezone.utc
    )
    end_dt = datetime.datetime.combine(
        prev_year_end, datetime.time.max, tzinfo=datetime.timezone.utc
    )

    history_url = OPENWEATHERMAP_HISTORY_URL.format(
        lat=lat,
        lon=lon,
        start=int(start_dt.timestamp()),
        end=int(end_dt.timestamp()),
        OPENWEATHERMAP_API_KEY=OPENWEATHERMAP_API_KEY,
    )
    resp = requests.get(history_url, timeout=15)
    if not resp.ok:
        raise HTTPException(
            status_code=resp.status_code,
            detail="Failed to fetch historical weather data",
        )

    data = resp.json()
    history_list = data.get("list") or data.get("hourly") or []

    temps_c: List[float] = []
    rainy_dates: set[datetime.date] = set()
    for entry in history_list:
        for temp_k in _extract_kelvin_temps(entry):
            temps_c.append(_kelvin_to_celsius(temp_k))

        dt_value = entry.get("dt")
        if not isinstance(dt_value, (int, float)):
            continue
        entry_date = datetime.datetime.utcfromtimestamp(dt_value).date()
        if not (prev_year_start <= entry_date <= prev_year_end):
            continue
        if _is_rainy_entry(entry):
            rainy_dates.add(entry_date)

    if not temps_c:
        return None, None, None

    precip_pct = _precipitation_percentage(len(rainy_dates), trip_days)
    return min(temps_c), max(temps_c), precip_pct


def _trip_within_forecast_window(start: datetime.date, end: datetime.date) -> bool:
    today = datetime.date.today()
    last_forecast_day = today + datetime.timedelta(days=FORECAST_WINDOW_DAYS)
    return today <= start <= last_forecast_day and end <= last_forecast_day


@router.post("/", response_model=Trip)
def create_trip(trip: Trip, user_id: Optional[str] = None):
    # TODO: do the airline name to airline type mapping
    trips_store[trip.trip_id] = trip

    # associate user if provided
    if user_id:
        if user_id not in users_store:
            raise HTTPException(status_code=404, detail="User not found")

        user = users_store[user_id]
        if trip.trip_id not in user.trips:
            user.trips.append(trip.trip_id)

    return trip


@router.get("/", response_model=List[Trip])
def get_trips():
    """Get all trips."""
    return list(trips_store.values())


@router.get("/activities", response_model=List[str])
def get_activities():
    """Get all activities."""
    return [activity.value for activity in Activity]


@router.get("/airlines", response_model=List[str])
def get_airlines():
    """Get all airlines."""
    return [airline.value for airline in Airline]


@router.get("/{trip_id}", response_model=Trip)
def get_trip(trip_id: str):
    """Get a specific trip by ID."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trips_store[trip_id]


@router.put("/{trip_id}", response_model=Trip)
def update_trip(trip_id: str, update: TripUpdate):
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    existing = trips_store[trip_id]
    patch_data = update.model_dump(exclude_unset=True)
    updated = existing.model_copy(update=patch_data)

    trips_store[trip_id] = updated
    return updated


@router.delete("/{trip_id}")
def delete_trip(trip_id: str):
    """Delete a trip."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    # remove trip reference from items
    for item in items_store.values():
        if trip_id in item.trips:
            item.trips.remove(trip_id)

    # remove from users
    for user in users_store.values():
        if trip_id in user.trips:
            user.trips.remove(trip_id)

    del trips_store[trip_id]
    return {"message": "Trip deleted successfully"}


@router.post("/{trip_id}/item/{item_id}")
def add_item_to_trip(trip_id: str, item_id: str):
    """Add existing item to a trip. This endpoint does not create the item itself."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    if item_id not in items_store:
        raise HTTPException(status_code=404, detail="Item not found")

    trip = trips_store[trip_id]
    item = items_store[item_id]
    if item.item_id not in trip.items:
        trip.items.append(item.item_id)

    if trip_id not in item.trips:
        item.trips.append(trip_id)

    if item.estimated_volume_cm3 is not None or item.weight_kg is not None:
        recalculate_trip_totals(trip_id)


@router.delete("/{trip_id}/item/{item_id}")
def remove_item_from_trip(trip_id: str, item_id: str):
    """Remove existing item from a trip. This endpoint does not delete the item itself."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    if item_id not in items_store:
        raise HTTPException(status_code=404, detail="Item not found")

    trip = trips_store[trip_id]
    item = items_store[item_id]
    if item.item_id in trip.items:
        trip.items.remove(item.item_id)

    if trip_id in item.trips:
        item.trips.remove(trip_id)

    if item.estimated_volume_cm3 is not None or item.weight_kg is not None:
        recalculate_trip_totals(trip_id)


@router.get("/{trip_id}/items", response_model=List[Item])
def get_trip_items(trip_id: str):
    """Get all items for a specific trip."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip = trips_store[trip_id]
    if trip.items is None:
        return []
    trip_items = [items_store[id] for id in trip.items if id in items_store]

    return trip_items


@router.post("/{trip_id}/recalculate-totals")
def recalculate_trip_totals(trip_id: str):
    """Recalculate total weight and volume for a trip."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip = trips_store[trip_id]

    trip.total_items_weight = sum(
        (items_store[item_id].weight_kg or 0.0) for item_id in trip.items
    )
    trip.total_items_volume = sum(
        (items_store[item_id].estimated_volume_cm3 or 0.0) for item_id in trip.items
    )

    # TO-DO: can remove the return if not useful
    return {
        "trip_id": trip_id,
        "total_weight": trip.total_items_weight,
        "total_volume": trip.total_items_volume,
    }


@router.get("/{trip_id}/recommendations", response_model=List[RecommendedItem])
def get_trip_recommendations(trip_id: str):
    """Generate packing recommendations from the trip metadata and activities"""

    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip = trips_store[trip_id]

    recs = baseline_list_algorithm(trip)

    if recs is None:
        raise HTTPException(status_code=500, detail="No recommendations generated")

    return recs


@router.get(
    "/{trip_id}/item/{item_id}/packing-decision", response_model=RemovalRecommendation
)
def get_packing_decision(trip_id: str, item_id: str):
    """Returns decision on whether to pack an item."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    if item_id not in items_store:
        raise HTTPException(status_code=404, detail="Item not found")

    trip = trips_store[trip_id]
    item = items_store[item_id]

    items = get_trip_items(trip_id)

    return packing_decision_algorithm(item, trip, items)


@router.get("/{trip_id}/weather", response_model=Trip)
def get_weather(trip_id: str):
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip = trips_store[trip_id]

    start_date = trip.start_date.date()
    end_date = trip.end_date.date()
    if end_date < start_date:
        raise HTTPException(
            status_code=400, detail="Trip end_date is before start_date"
        )
    trip_days = (end_date - start_date).days + 1

    lat, lon = _get_lat_lon_for_trip(trip)

    if _trip_within_forecast_window(start_date, end_date):
        lowest, highest, precip_pct = _get_forecast_stats(
            lat, lon, start_date, end_date, trip_days
        )
    else:
        lowest, highest, precip_pct = _get_historical_stats(
            lat, lon, start_date, end_date, trip_days
        )

    if lowest is None or highest is None or precip_pct is None:
        raise HTTPException(
            status_code=502,
            detail="Weather data unavailable for the requested trip dates",
        )

    trip.lowest_temp = lowest
    trip.highest_temp = highest
    trip.precipitation_percentage = precip_pct

    trips_store[trip_id] = trip
    return trip
