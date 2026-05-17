# ⛅ Weather Forecast Desktop App

A lightweight, cross-platform desktop weather application built with Python. Search any city or zip code in the world and instantly see current conditions alongside a 5-day forecast — all in a clean, dark-themed GUI. No API key required.

---

## 📸 Overview

The app provides a real-time snapshot of the weather for any location on Earth. It displays the current temperature, feels-like reading, humidity, wind speed and direction, and a weather condition label with an emoji icon. Below the current conditions, a 5-day daily forecast shows high/low temperatures, expected conditions, and precipitation totals.

---

## ✨ Features

- **No API key needed** — powered by the free and open [Open-Meteo](https://open-meteo.com/) API
- **Global city search** — supports city names and zip/postal codes
- **Current conditions** — temperature, feels-like, humidity, wind speed & compass direction, and weather condition
- **5-day daily forecast** — daily high/low, condition description, and precipitation in mm
- **WMO weather code mapping** — full coverage of all standard weather condition codes with emoji labels
- **Non-blocking UI** — API calls run on a background thread so the interface stays fully responsive during fetches
- **Graceful error handling** — user-friendly messages for invalid cities, network failures, timeouts, and unexpected errors
- **Optional OpenWeatherMap support** — swap in your OWM API key with a single variable change

---

## 🖥️ Requirements

| Requirement | Version |
|---|---|
| Python | 3.8 or higher |
| tkinter | Included with Python (standard library) |
| requests | Any recent version |

> **Note:** `tkinter` ships with the standard Python installer on Windows and macOS. On Linux, install it via your package manager if missing:
> ```bash
> # Debian/Ubuntu
> sudo apt install python3-tk
>
> # Fedora
> sudo dnf install python3-tkinter
> ```

---

## 🚀 Installation & Usage

**1. Clone the repository**
```bash
git clone https://github.com/your-username/weather-forecast-app.git
cd weather-forecast-app
```

**2. Install the dependency**
```bash
pip install requests
```

**3. Run the app**
```bash
python weather_app.py
```

**4. Search for a location**

Type a city name (e.g. `London`) or a zip/postal code (e.g. `90210`) into the search bar and press **Enter** or click **Search**.

---

## 🌐 API Details

### Default: Open-Meteo (no key required)

This app uses two Open-Meteo endpoints:

| Endpoint | Purpose |
|---|---|
| `geocoding-api.open-meteo.com/v1/search` | Converts city name or zip code to latitude/longitude |
| `api.open-meteo.com/v1/forecast` | Returns current conditions and daily forecast data |

Open-Meteo is a free, open-source weather API with no rate limits for non-commercial use. No account or API key is needed.

### Optional: OpenWeatherMap

If you prefer to use OpenWeatherMap instead:

1. Visit [openweathermap.org/api](https://openweathermap.org/api) and create a free account
2. Navigate to **API Keys** in your profile dashboard and copy your key
3. In `weather_app.py`, set:
   ```python
   OWM_API_KEY = "your_api_key_here"
   ```
4. Follow the comments in the file to swap in the `fetch_weather_owm()` function

The free OWM tier provides up to **1,000 API calls per day**.

---

## 🗂️ Project Structure

```
weather-forecast-app/
├── weather_app.py   # Main application — all source code in a single file
└── README.md        # This file
```

---

## 🔧 Customisation

**Change temperature units to Fahrenheit**

In `fetch_weather()`, add these keys to the `params` dict:
```python
"temperature_unit": "fahrenheit",
"wind_speed_unit":  "mph",
```
Then update the `°C` labels in the UI to `°F`.

**Add more current weather variables**

Append any variable from the [Open-Meteo docs](https://open-meteo.com/en/docs) to the `"current"` list in `fetch_weather()`, then add a corresponding stat box in `_build_current_panel()`.

**Extend the forecast to 7 days**

In `fetch_weather()`, change:
```python
"forecast_days": 6   →   "forecast_days": 8
range(1, 6)          →   range(1, 8)
```
Then add two more cards in `_build_forecast_panel()`.

**Customise weather condition labels or emojis**

Edit the `WMO_CODES` dictionary near the top of `weather_app.py`. Each entry maps a WMO code to a `(description, emoji)` tuple.

---

## ⚠️ Error Handling

| Scenario | Behaviour |
|---|---|
| Invalid city name | Displays "City not found" message in the status bar |
| No internet connection | Displays "No internet connection" message |
| Request timeout (>8 s) | Displays "Request timed out" message |
| Unexpected API error | Displays a generic error message with details |

The application will never crash on a failed search — all exceptions are caught and surfaced as readable status messages.

---

## 📄 License

This project is released under the [MIT License](LICENSE).

---

## 🙏 Acknowledgements

- Weather data by [Open-Meteo](https://open-meteo.com/) — free and open-source
- Geocoding by [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api)
- WMO weather interpretation codes via [WMO standard 4677](https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM)
