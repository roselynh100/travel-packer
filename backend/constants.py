# Openweathermap API
OPENWEATHERMAP_API_KEY = "KEY"

OPENWEATHER_GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct?q={city_name},{country_code}&limit={limit}&appid={OPENWEATHERMAP_API_KEY}"

OPENWEATHER_GEOCODING_USA_URL = "https://api.openweathermap.org/geo/1.0/direct?q={city_name},{state_code},{country_code}&limit={limit}&appid={OPENWEATHERMAP_API_KEY}"

OPENWEATHERMAP_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast/daily?lat={lat}&lon={lon}&cnt={cnt}&appid={OPENWEATHERMAP_API_KEY}"

OPENWEATHERMAP_HISTORY_URL = "https://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=hour&start={start}&end={end}&appid={OPENWEATHERMAP_API_KEY}"

# SerpAPI
SERPAPI_API_KEY = "KEY"

SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"

# Exchange API
EXCHANGE_API_URLS = [
    "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies",
    "https://latest.currency-api.pages.dev/v1/currencies",
]

# myclimate API
MYCLIMATE_API_URL = "https://api.myclimate.org/v2/flight_calculators.json"
MYCLIMATE_API_USERNAME = "USERNAME"
MYCLIMATE_API_PASSWORD = "PASSWORD"
