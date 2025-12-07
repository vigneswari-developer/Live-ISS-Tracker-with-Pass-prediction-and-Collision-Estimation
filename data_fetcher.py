# data_fetcher.py
from datetime import datetime, timedelta, timezone
from dateutil import tz
from geopy.geocoders import Nominatim
import requests
import math
import random

# -----------------------------
#  Helper: format datetime nicely
# -----------------------------
def _fmt_pass_dt(dt: datetime) -> str:
    """Return a human-readable local datetime string for pass display."""
    return dt.strftime("%A, %B %d at %I:%M:%S %p")

# -----------------------------
#  Get current ISS position (WhereTheISS.at)
# -----------------------------
def get_iss_position(timeout=8):
    """
    Uses whereetheiss.at (no API key) to get current ISS lat/lon.
    Returns (lat, lon) or (None, None) on failure.
    """
    api_url = "https://api.wheretheiss.at/v1/satellites/25544"
    try:
        r = requests.get(api_url, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        return float(data.get("latitude")), float(data.get("longitude"))
    except requests.exceptions.RequestException as e:
        print(f"⚠ Error fetching ISS position: {e}")
        return None, None

# -----------------------------
#  Reverse geocode place name
# -----------------------------
def get_place_name(latitude, longitude, timeout=10):
    """
    Convert lat/lon to a readable place name or ocean region.
    Returns a string (city, region or ocean).
    """
    try:
        geolocator = Nominatim(user_agent="iss_tracker_project", timeout=timeout)
        location = geolocator.reverse((latitude, longitude), exactly_one=True, language='en')
        if location:
            address = location.raw.get('address', {})
            # prefer ocean/sea keys first
            for key in ['ocean', 'sea', 'water', 'bay']:
                if key in address:
                    return f"Over the {address[key]}"
            city = address.get('city') or address.get('town') or address.get('village') or address.get('municipality')
            state = address.get('state')
            country = address.get('country')
            if city and country:
                return f"{city}, {country}"
            if state and country:
                return f"{state}, {country}"
            if country:
                return country
        # fallback ocean/region guesses
        lat, lon = latitude, longitude
        if -60 <= lat <= 30 and 20 <= lon <= 150:
            return "Over the Indian Ocean"
        elif -60 <= lat <= 60 and -180 <= lon <= -70:
            return "Over the South Pacific Ocean"
        elif 0 <= lat <= 60 and -180 <= lon <= -100:
            return "Over the North Pacific Ocean"
        elif lat >= 0 and -100 <= lon <= -20:
            return "Over the North Atlantic Ocean"
        elif lat < 0 and -70 <= lon <= 20:
            return "Over the South Atlantic Ocean"
        elif abs(lat) > 60:
            return "Over the Polar Region"
        else:
            return "Over an unknown area"
    except Exception as e:
        print(f"⚠ Reverse geocoding error: {e}")
        return "Location not available"

# -----------------------------
#  Geocode city -> lat/lon
# -----------------------------
def get_coords_from_city(city_name, timeout=10):
    """
    Return (lat, lon, full_address) or (None, None, None).
    Uses Nominatim (OpenStreetMap).
    """
    try:
        geolocator = Nominatim(user_agent="iss_tracker_project", timeout=timeout)
        location = geolocator.geocode(city_name)
        if location:
            return (location.latitude, location.longitude, location.address)
        return (None, None, None)
    except Exception as e:
        print(f"⚠ Geocoding error: {e}")
        return (None, None, None)

# -------------------------------------------------------------------------
# SIMULATED PASS GENERATOR
# Used for testing the application without consuming N2YO API requests limits.
# Allows full backend validation (geocoding → pass prediction → map build)
# even when:
#   - API quota is exceeded
#   - No API key is available
#   - Network connectivity is limited
# Generates realistic ISS pass timestamps for safe, offline development.
# -------------------------------------------------------------------------
def _simulated_passes(number=3, start_utc=None, seed=None):
     
    if seed is not None:
        random.seed(seed)
    else:
        random.seed()

    if start_utc is None:
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
    else:
        now = start_utc if isinstance(start_utc, datetime) else datetime.utcnow().replace(tzinfo=timezone.utc)

    day_gap_choices = [1, 1, 2, 2, 3, 4]  # common gaps between visible passes (makes varied spacing)
    passes = []
    current_date = now

    # start preference: more likely evening or morning (bias random)
    is_evening = random.random() < 0.65

    for i in range(number):
        gap = random.choice(day_gap_choices)
        current_date = current_date + timedelta(days=gap)

        # occasionally switch period
        if random.random() >= 0.15:
            is_evening = not is_evening

        # pick hour in evening or morning windows
        if is_evening:
            hour = random.randint(18, 23)   # 6 PM - 11 PM
        else:
            hour = random.randint(4, 7)     # 4 AM - 7 AM

        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        # UTC pass time constructed using chosen hour/minute/second
        pass_dt_utc = datetime(
            year=current_date.year,
            month=current_date.month,
            day=current_date.day,
            hour=hour, minute=minute, second=second,
            tzinfo=timezone.utc
        )

        # Convert UTC -> local system timezone (so displayed times match system / IST if your laptop is IST)
        local_tz = tz.gettz()
        pass_dt_local = pass_dt_utc.astimezone(local_tz)

        # Build a plausible duration and max elevation value
        max_elev = round(min(85.0, max(10.0, random.gauss(45, 15))), 1)
        duration = int(max(120, min(900, int(120 + max_elev * 6 + random.randint(-60, 60)))))

        passes.append({
            'time': _fmt_pass_dt(pass_dt_local),
            'iso_time_local': pass_dt_local.isoformat(),
            'iso_time_utc': pass_dt_utc.isoformat(),
            'duration': duration,
            'max_elev_deg': max_elev,
            'source': 'simulated'
        })

    return passes

# -----------------------------
#  ISS passes: N2YO real or fallback
# -----------------------------
def get_iss_passes(api_key, lat, lon, number_of_passes=5, USE_REAL_API=True, timeout=10):
    """
    If USE_REAL_API True -> try N2YO 'radiopasses' endpoint with provided api_key.
    If N2YO fails or USE_REAL_API False -> return simulated pass list.
    Returns a list of dicts with time (string), duration (sec), source.
    """
    if not USE_REAL_API:
        return _simulated_passes(number=number_of_passes)

    api_url = (f"https://api.n2yo.com/rest/v1/satellite/radiopasses/25544/"
               f"{lat}/{lon}/0/{number_of_passes}/300/&apiKey={api_key}")
    try:
        r = requests.get(api_url, timeout=timeout)
        # Check for rate-limited/forbidden before raising
        if r.status_code in (403, 429):
            print("⚠ N2YO limit reached or access denied. Falling back to simulated data.")
            return _simulated_passes(number=number_of_passes)
        r.raise_for_status()
        data = r.json()
        if not data or 'passes' not in data or not data['passes']:
            print("⚠ No pass data returned from N2YO (empty 'passes'). Falling back to simulated.")
            return _simulated_passes(number=number_of_passes)

        pass_info = []
        for p in data['passes']:
            # convert UTC timestamp to local timezone for display
            start_time_utc = datetime.fromtimestamp(p['startUTC'], tz=timezone.utc)
            local_timezone = tz.gettz()
            start_time_local = start_time_utc.astimezone(local_timezone)
            formatted_time = _fmt_pass_dt(start_time_local)
            duration = p.get('duration', 0)
            pass_info.append({'time': formatted_time, 'duration': duration, 'source': 'n2yo',
                              'iso_time_utc': start_time_utc.isoformat(),
                              'iso_time_local': start_time_local.isoformat()})
        return pass_info

    except requests.exceptions.RequestException as e:
        print(f"⚠ N2YO request error: {e}. Falling back to simulated passes.")
        return _simulated_passes(number=number_of_passes)

# -----------------------------
#  Collision estimator (3 day window) - improved lightweight algorithm
# -----------------------------
def get_collision_risks(days=3):
    """
    Lightweight simulated conjunction analysis for demonstration (3-day window).
    Produces sorted list of risk events with miss distance, level and tiny probability score.
    This is a simulation only—replace with CelesTrak/SOCRATES calls for real data.
    """
    print("🛰 Running simulated conjunction analysis (3-day window)...")

    ISS_ALTITUDE_KM = 408.0
    ISS_INCLINATION_DEG = 51.6

    # small set of representative debris/objects for demo
    debris_objects = [
        {"name": "FENGYUN-1C DEB", "altitude": 850, "inclination": 98.5},
        {"name": "COSMOS-2251 DEB", "altitude": 790, "inclination": 74.0},
        {"name": "IRIDIUM-33 DEB", "altitude": 770, "inclination": 86.4},
        {"name": "ATLAS V R/B", "altitude": 420, "inclination": 51.7},
        {"name": "STARLINK DEB", "altitude": 550, "inclination": 53.0},
        {"name": "CZ-2C R/B", "altitude": 430, "inclination": 49.5}
    ]

    now = datetime.utcnow()
    risks = []
    for obj in debris_objects:
        altitude_diff = abs(obj["altitude"] - ISS_ALTITUDE_KM)
        inc_diff = abs(obj["inclination"] - ISS_INCLINATION_DEG)
        # scale inclination diff to km-equivalent (small heuristic)
        distance = math.sqrt(altitude_diff*2 + (inc_diff * 10)*2)
        if distance < 10:
            level = "High"
        elif distance < 30:
            level = "Medium"
        else:
            level = "Low"
        # gaussian-like small probability scaled for demo readability
        Pc = math.exp(-(distance*2) / (2 * (20*2))) * 1e-3
        Pc = round(Pc, 6)
        event_time = now + timedelta(hours=random.randint(6, max(6, days * 24)))
        event_str = event_time.strftime("On %A, %b %d at %I:%M %p UTC")
        risks.append({
            "object_name": obj["name"],
            "miss_distance_km": round(distance, 2),
            "time": event_str,
            "level": level,
            "probability": Pc,
            "simulated": True
        })
    risks.sort(key=lambda x: x["miss_distance_km"])
    return risks

# -----------------------------
#  Astronaut data from Open Notify
# -----------------------------
def get_astronauts(timeout=6):
    """
    Returns (number_of_people, [names]) or (None, []) on failure.
    """
    api_url = 'http://api.open-notify.org/astros.json'
    try:
        r = requests.get(api_url, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        number_of_people = data.get('number')
        names = [person['name'] for person in data.get('people', [])]
        return number_of_people, names
    except requests.exceptions.RequestException as e:
        print(f"⚠ Astronaut data error: {e}")
        return None, []