import datetime
from typing import List, Optional

import requests
from fastapi import HTTPException

from app.models import Trip
from constants import (
    OPENWEATHER_GEOCODING_URL,
    OPENWEATHER_GEOCODING_USA_URL,
    OPENWEATHERMAP_API_KEY,
    OPENWEATHERMAP_FORECAST_URL,
    OPENWEATHERMAP_HISTORY_URL,
)

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
