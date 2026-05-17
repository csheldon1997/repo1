"""
=============================================================
  Weather Forecast Desktop App
  Uses Open-Meteo (free, no API key needed) + Geocoding API
=============================================================

HOW TO GET STARTED
------------------
This app uses Open-Meteo (https://open-meteo.com/), which is
completely FREE and requires NO API key. Just run the script!

If you prefer OpenWeatherMap instead:
  1. Visit https://openweathermap.org/api
  2. Click "Sign Up" and create a free account
  3. Go to "API Keys" in your profile dashboard
  4. Copy your key and replace the OWM_API_KEY variable below
  5. Uncomment the fetch_weather_owm() function and call it instead

DEPENDENCIES
------------
  pip install requests

RUNNING
-------
  python weather_app.py
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
import threading
from datetime import datetime, timedelta
import json
import socket
import urllib.error
import urllib.parse
import urllib.request

# ─────────────────────────────────────────────
#  OPTIONAL: OpenWeatherMap API Key
#  (Not needed for Open-Meteo — the default provider)
# ─────────────────────────────────────────────
OWM_API_KEY = "YOUR_API_KEY_HERE"   # Replace if using OWM

# ─────────────────────────────────────────────
#  WMO WEATHER CODE → DESCRIPTION + EMOJI
#  Open-Meteo uses WMO codes (https://open-meteo.com/en/docs)
#  Update this dict to change how conditions are displayed.
# ─────────────────────────────────────────────
WMO_CODES = {
    0:  ("Clear Sky",            "☀️"),
    1:  ("Mainly Clear",         "🌤️"),
    2:  ("Partly Cloudy",        "⛅"),
    3:  ("Overcast",             "☁️"),
    45: ("Foggy",                "🌫️"),
    48: ("Icy Fog",              "🌫️"),
    51: ("Light Drizzle",        "🌦️"),
    53: ("Moderate Drizzle",     "🌦️"),
    55: ("Dense Drizzle",        "🌧️"),
    61: ("Slight Rain",          "🌧️"),
    63: ("Moderate Rain",        "🌧️"),
    65: ("Heavy Rain",           "🌧️"),
    71: ("Slight Snow",          "🌨️"),
    73: ("Moderate Snow",        "❄️"),
    75: ("Heavy Snow",           "❄️"),
    77: ("Snow Grains",          "❄️"),
    80: ("Slight Showers",       "🌦️"),
    81: ("Moderate Showers",     "🌧️"),
    82: ("Violent Showers",      "⛈️"),
    85: ("Snow Showers",         "🌨️"),
    86: ("Heavy Snow Showers",   "❄️"),
    95: ("Thunderstorm",         "⛈️"),
    96: ("Thunderstorm w/ Hail", "⛈️"),
    99: ("Severe Thunderstorm",  "⛈️"),
}


def _http_get(url: str, params: dict, timeout: int = 8) -> dict:
    query = urllib.parse.urlencode(params)
    request_url = f"{url}?{query}"
    req = urllib.request.Request(
        request_url,
        headers={"User-Agent": "Mozilla/5.0 (weather-app)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.getcode() != 200:
                raise ConnectionError(f"API error: HTTP {resp.getcode()}")
            return json.load(resp)
    except urllib.error.HTTPError as e:
        raise ConnectionError(f"API error: HTTP {e.code}")
    except urllib.error.URLError as e:
        if isinstance(e.reason, socket.timeout):
            raise ConnectionError("Request timed out. Try again.")
        raise ConnectionError("No internet connection. Please check your network.")


# ─────────────────────────────────────────────
#  DATA FETCHING FUNCTIONS
# ─────────────────────────────────────────────


def geocode_city(city_name: str) -> dict:
    """
    Convert a city name or zip code into lat/lon using
    Open-Meteo's free Geocoding API.

    Returns a dict with keys: name, country, latitude, longitude
    Raises ValueError if city not found.
    Raises ConnectionError on network failure.
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city_name, "count": 1, "language": "en", "format": "json"}

    data = _http_get(url, params, timeout=8)

    # The API returns a "results" list; empty means city not found
    if not data.get("results"):
        raise ValueError(f'City "{city_name}" not found. Check the spelling and try again.')

    result = data["results"][0]
    return {
        "name":      result.get("name", city_name),
        "country":   result.get("country", ""),
        "latitude":  result["latitude"],
        "longitude": result["longitude"],
        "timezone":  result.get("timezone", "UTC"),
    }


def fetch_weather(lat: float, lon: float, timezone: str) -> dict:
    """
    Fetch current conditions + 5-day daily forecast from Open-Meteo.

    To add more variables, append them to the 'current' or 'daily'
    parameter lists in `params` below. Full variable list:
    https://open-meteo.com/en/docs

    Returns a parsed dict with 'current' and 'forecast' keys.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":    lat,
        "longitude":   lon,
        "timezone":    timezone,
        # ── Current conditions ───────────────────────────────
        "current": ",".join([
            "temperature_2m",        # °C temperature at 2 m
            "relative_humidity_2m",  # % humidity
            "apparent_temperature",  # "feels like"
            "weather_code",          # WMO weather code
            "wind_speed_10m",        # km/h wind speed
            "wind_direction_10m",    # degrees
        ]),
        # ── Daily forecast (next 6 days including today) ─────
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",     # mm rain/snow
        ]),
        "forecast_days": 6,
    }

    raw = _http_get(url, params, timeout=8)

    # ── Extract current conditions ────────────────────────────
    cur = raw["current"]
    wmo_code = cur["weather_code"]
    condition, emoji = WMO_CODES.get(wmo_code, ("Unknown", "🌡️"))

    # Wind direction degrees → compass label
    wd = cur["wind_direction_10m"]
    compass = ["N","NE","E","SE","S","SW","W","NW"][round(wd / 45) % 8]

    current = {
        "temp":        round(cur["temperature_2m"]),
        "feels_like":  round(cur["apparent_temperature"]),
        "humidity":    cur["relative_humidity_2m"],
        "wind_speed":  round(cur["wind_speed_10m"]),
        "wind_dir":    compass,
        "condition":   condition,
        "emoji":       emoji,
    }

    # ── Extract daily forecast ────────────────────────────────
    daily = raw["daily"]
    forecast = []
    for i in range(1, 6):   # Skip index 0 (today); show next 5 days
        date_str  = daily["time"][i]                    # "YYYY-MM-DD"
        dt        = datetime.strptime(date_str, "%Y-%m-%d")
        day_name  = dt.strftime("%a")                   # "Mon", "Tue" …
        wmo       = daily["weather_code"][i]
        desc, emo = WMO_CODES.get(wmo, ("Unknown", "🌡️"))
        forecast.append({
            "day":    day_name,
            "date":   dt.strftime("%b %d"),
            "emoji":  emo,
            "desc":   desc,
            "high":   round(daily["temperature_2m_max"][i]),
            "low":    round(daily["temperature_2m_min"][i]),
            "precip": daily["precipitation_sum"][i],
        })

    return {"current": current, "forecast": forecast}


# ─────────────────────────────────────────────
#  GUI APPLICATION
# ─────────────────────────────────────────────

class WeatherApp(tk.Tk):
    """Main application window."""

    # ── Colour palette ──────────────────────────────────────
    BG         = "#0f1923"   # deep navy background
    PANEL      = "#172130"   # slightly lighter panel
    CARD       = "#1e2d3d"   # forecast card background
    ACCENT     = "#38bdf8"   # sky-blue accent
    ACCENT2    = "#fb923c"   # warm orange accent
    TEXT       = "#e2e8f0"   # primary text (near-white)
    MUTED      = "#64748b"   # muted / secondary text
    SUCCESS    = "#4ade80"   # green for low values
    BORDER     = "#243447"   # subtle border colour

    def __init__(self):
        super().__init__()
        self.title("Weather Forecast")
        self.geometry("780x680")
        self.minsize(680, 580)
        self.configure(bg=self.BG)
        self.resizable(True, True)

        self._build_fonts()
        self._build_ui()

    # ── Font setup ──────────────────────────────────────────
    def _build_fonts(self):
        self.f_title  = tkfont.Font(family="Georgia",       size=16, weight="bold")
        self.f_city   = tkfont.Font(family="Georgia",       size=22, weight="bold")
        self.f_temp   = tkfont.Font(family="Courier New",   size=56, weight="bold")
        self.f_cond   = tkfont.Font(family="Georgia",       size=14, slant="italic")
        self.f_label  = tkfont.Font(family="Courier New",   size=10)
        self.f_value  = tkfont.Font(family="Courier New",   size=13, weight="bold")
        self.f_card   = tkfont.Font(family="Courier New",   size=11)
        self.f_cardb  = tkfont.Font(family="Courier New",   size=12, weight="bold")
        self.f_search = tkfont.Font(family="Courier New",   size=12)
        self.f_btn    = tkfont.Font(family="Georgia",       size=11, weight="bold")
        self.f_small  = tkfont.Font(family="Courier New",   size=9)

    # ── Layout construction ─────────────────────────────────
    def _build_ui(self):
        # ── Header bar ─────────────────────────────────────
        header = tk.Frame(self, bg=self.BG, pady=16)
        header.pack(fill="x", padx=24)

        tk.Label(header, text="⛅  WEATHER", font=self.f_title,
                 bg=self.BG, fg=self.ACCENT).pack(side="left")

        tk.Label(header, text="Open-Meteo · No API key required",
                 font=self.f_small, bg=self.BG, fg=self.MUTED).pack(side="right", pady=6)

        # ── Search bar ──────────────────────────────────────
        search_frame = tk.Frame(self, bg=self.PANEL, bd=0,
                                highlightbackground=self.BORDER, highlightthickness=1)
        search_frame.pack(fill="x", padx=24, pady=(0, 16))

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame, textvariable=self.search_var,
            font=self.f_search, bg=self.PANEL, fg=self.TEXT,
            insertbackground=self.ACCENT, relief="flat",
            bd=0
        )
        self.search_entry.pack(side="left", fill="both", expand=True, padx=14, pady=10)
        self.search_entry.insert(0, "Enter city name or zip code…")
        self.search_entry.config(fg=self.MUTED)
        self.search_entry.bind("<FocusIn>",  self._clear_placeholder)
        self.search_entry.bind("<FocusOut>", self._restore_placeholder)
        self.search_entry.bind("<Return>",   lambda _: self._start_search())

        self.search_btn = tk.Button(
            search_frame, text="Search", font=self.f_btn,
            bg=self.ACCENT, fg=self.BG, activebackground="#7dd3fc",
            activeforeground=self.BG, relief="flat", cursor="hand2",
            padx=18, pady=6, bd=0,
            command=self._start_search
        )
        self.search_btn.pack(side="right", padx=6, pady=6)

        # ── Status / error label ────────────────────────────
        self.status_var = tk.StringVar(value="")
        self.status_lbl = tk.Label(self, textvariable=self.status_var,
                                   font=self.f_small, bg=self.BG, fg="#f87171")
        self.status_lbl.pack(pady=(0, 4))

        # ── Main content area ───────────────────────────────
        self.content = tk.Frame(self, bg=self.BG)
        self.content.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        self._build_current_panel()
        self._build_forecast_panel()

        # ── Footer ──────────────────────────────────────────
        tk.Label(self, text="Data: Open-Meteo  ·  Geocoding: Open-Meteo Geocoding API",
                 font=self.f_small, bg=self.BG, fg=self.MUTED).pack(pady=(0, 10))

    def _build_current_panel(self):
        """Current conditions section."""
        self.cur_frame = tk.Frame(self.content, bg=self.PANEL,
                                  highlightbackground=self.BORDER, highlightthickness=1)
        self.cur_frame.pack(fill="x", pady=(0, 12))

        # City + country row
        top = tk.Frame(self.cur_frame, bg=self.PANEL)
        top.pack(fill="x", padx=20, pady=(16, 0))

        self.city_var = tk.StringVar(value="—")
        tk.Label(top, textvariable=self.city_var, font=self.f_city,
                 bg=self.PANEL, fg=self.TEXT).pack(side="left")

        self.updated_var = tk.StringVar(value="")
        tk.Label(top, textvariable=self.updated_var, font=self.f_small,
                 bg=self.PANEL, fg=self.MUTED).pack(side="right", pady=8)

        # Temp + condition row
        mid = tk.Frame(self.cur_frame, bg=self.PANEL)
        mid.pack(fill="x", padx=20, pady=8)

        self.temp_var = tk.StringVar(value="—")
        tk.Label(mid, textvariable=self.temp_var, font=self.f_temp,
                 bg=self.PANEL, fg=self.ACCENT).pack(side="left")

        cond_block = tk.Frame(mid, bg=self.PANEL)
        cond_block.pack(side="left", padx=18, pady=8)

        self.emoji_var = tk.StringVar(value="")
        tk.Label(cond_block, textvariable=self.emoji_var, font=tkfont.Font(size=28),
                 bg=self.PANEL).pack()
        self.cond_var = tk.StringVar(value="")
        tk.Label(cond_block, textvariable=self.cond_var, font=self.f_cond,
                 bg=self.PANEL, fg=self.TEXT).pack()
        self.feels_var = tk.StringVar(value="")
        tk.Label(cond_block, textvariable=self.feels_var, font=self.f_small,
                 bg=self.PANEL, fg=self.MUTED).pack()

        # Stats row (humidity, wind, etc.)
        stats = tk.Frame(self.cur_frame, bg=self.PANEL)
        stats.pack(fill="x", padx=20, pady=(4, 16))

        self.stat_labels = {}
        stat_defs = [
            ("humidity",   "💧 Humidity",   "—"),
            ("wind",       "🌬 Wind",       "—"),
        ]
        for key, label, _ in stat_defs:
            box = tk.Frame(stats, bg=self.CARD,
                           highlightbackground=self.BORDER, highlightthickness=1)
            box.pack(side="left", padx=(0, 10), pady=4, ipadx=14, ipady=8)
            tk.Label(box, text=label, font=self.f_label,
                     bg=self.CARD, fg=self.MUTED).pack()
            var = tk.StringVar(value="—")
            tk.Label(box, textvariable=var, font=self.f_value,
                     bg=self.CARD, fg=self.TEXT).pack()
            self.stat_labels[key] = var

    def _build_forecast_panel(self):
        """5-day forecast section."""
        tk.Label(self.content, text="5-DAY FORECAST", font=self.f_label,
                 bg=self.BG, fg=self.MUTED).pack(anchor="w", pady=(4, 6))

        self.forecast_frame = tk.Frame(self.content, bg=self.BG)
        self.forecast_frame.pack(fill="x")

        self.forecast_cards = []
        for _ in range(5):
            card = self._make_forecast_card(self.forecast_frame)
            self.forecast_cards.append(card)

    def _make_forecast_card(self, parent) -> dict:
        """Create one forecast card; return dict of its StringVars."""
        frame = tk.Frame(parent, bg=self.CARD,
                         highlightbackground=self.BORDER, highlightthickness=1)
        frame.pack(side="left", fill="both", expand=True, padx=(0, 8))

        vars_ = {}
        for key, size, color in [
            ("day",   self.f_cardb, self.ACCENT),
            ("date",  self.f_small, self.MUTED),
            ("emoji", tkfont.Font(size=20), self.TEXT),
            ("desc",  self.f_small, self.MUTED),
            ("high",  self.f_cardb, self.ACCENT2),
            ("low",   self.f_card,  self.MUTED),
            ("rain",  self.f_small, "#38bdf8"),
        ]:
            v = tk.StringVar(value="—")
            tk.Label(frame, textvariable=v, font=size,
                     bg=self.CARD, fg=color, pady=2).pack(pady=1)
            vars_[key] = v

        return vars_

    # ── Placeholder helpers ─────────────────────────────────
    def _clear_placeholder(self, _event):
        if self.search_entry.cget("fg") == self.MUTED:
            self.search_entry.delete(0, "end")
            self.search_entry.config(fg=self.TEXT)

    def _restore_placeholder(self, _event):
        if not self.search_var.get():
            self.search_entry.insert(0, "Enter city name or zip code…")
            self.search_entry.config(fg=self.MUTED)

    # ── Search logic ────────────────────────────────────────
    def _start_search(self):
        """Kick off the weather fetch on a background thread so the UI stays responsive."""
        city = self.search_var.get().strip()
        if not city or city == "Enter city name or zip code…":
            self.status_var.set("⚠  Please enter a city name or zip code.")
            return

        self.status_var.set("Fetching weather…")
        self.search_btn.config(state="disabled", text="…")
        self.config(cursor="watch")

        # Run network calls in a separate thread to avoid freezing the GUI
        thread = threading.Thread(target=self._fetch_and_update, args=(city,), daemon=True)
        thread.start()

    def _fetch_and_update(self, city: str):
        """Background thread: geocode → fetch weather → update UI via after()."""
        try:
            geo     = geocode_city(city)
            weather = fetch_weather(geo["latitude"], geo["longitude"], geo["timezone"])
            # Schedule UI update back on the main thread (tkinter is not thread-safe)
            self.after(0, self._update_ui, geo, weather)
        except ValueError as e:
            # City not found
            self.after(0, self._show_error, str(e))
        except ConnectionError as e:
            # Network issue
            self.after(0, self._show_error, str(e))
        except Exception as e:
            # Unexpected error — catch-all so the app never crashes
            self.after(0, self._show_error, f"Unexpected error: {e}")
        finally:
            self.after(0, self._reset_button)

    def _update_ui(self, geo: dict, weather: dict):
        """Update all widgets with fresh data. Called on the main thread."""
        self.status_var.set("")

        cur = weather["current"]

        # City name + timestamp
        self.city_var.set(f"{geo['name']}, {geo['country']}")
        self.updated_var.set("Updated " + datetime.now().strftime("%H:%M"))

        # Temperature
        self.temp_var.set(f"{cur['temp']}°C")
        self.emoji_var.set(cur["emoji"])
        self.cond_var.set(cur["condition"])
        self.feels_var.set(f"Feels like {cur['feels_like']}°C")

        # Stats
        self.stat_labels["humidity"].set(f"{cur['humidity']}%")
        self.stat_labels["wind"].set(f"{cur['wind_speed']} km/h {cur['wind_dir']}")

        # Forecast cards
        for i, day in enumerate(weather["forecast"]):
            c = self.forecast_cards[i]
            c["day"].set(day["day"])
            c["date"].set(day["date"])
            c["emoji"].set(day["emoji"])
            c["desc"].set(day["desc"])
            c["high"].set(f"↑ {day['high']}°")
            c["low"].set(f"↓ {day['low']}°")
            # Show precipitation only if non-zero
            c["rain"].set(f"🌧 {day['precip']} mm" if day["precip"] > 0 else "")

    def _show_error(self, message: str):
        """Display an error message in the status bar."""
        self.status_var.set(f"⚠  {message}")

    def _reset_button(self):
        """Re-enable search button and restore cursor."""
        self.search_btn.config(state="normal", text="Search")
        self.config(cursor="")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()