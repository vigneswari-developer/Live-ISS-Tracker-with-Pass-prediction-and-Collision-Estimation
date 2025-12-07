# -------------------------------------------------------------
# N2YO API KEY
# IMPORTANT: Replace the placeholder below with your own API key.
# You can obtain a free key at: https://www.n2yo.com/api/ with limited access.
# Example:
# N2YO_API_KEY = "YOUR_API_KEY_HERE"
# -------------------------------------------------------------
from flask import Flask, render_template, request, redirect, url_for
import folium
from folium.plugins import Terminator
import data_fetcher
import os

app = Flask(__name__)

# --- N2YO API Key ---
N2YO_API_KEY = "YOUR_API_KEY_HERE"

# --- Manual Toggle: True = Simulated pass prediction, False = Real API pass prediction ---
USE_SIMULATED_PASSES = False # ← you can manually change this anytime


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_city = request.form["city"].strip()
        if not user_city:
            return render_template("index.html", error="Please enter a valid city name.")

        # Get coordinates
        user_lat, user_lon, full_address = data_fetcher.get_coords_from_city(user_city)
        if not user_lat:
            return render_template("index.html", error=f"Could not find location for '{user_city}'.")

        # Fetch pass data
        if USE_SIMULATED_PASSES:
            pass_times = data_fetcher.get_iss_passes(N2YO_API_KEY, user_lat, user_lon, USE_REAL_API=False)
        else:
            pass_times = data_fetcher.get_iss_passes(N2YO_API_KEY, user_lat, user_lon)

        # Get live ISS position
        iss_lat, iss_lon = data_fetcher.get_iss_position()
        place_name = data_fetcher.get_place_name(iss_lat, iss_lon) if iss_lat else "Unavailable (Network Error)"

        # Collision estimation + astronauts
        collision_risks = data_fetcher.get_collision_risks()
        astro_count, astro_names = data_fetcher.get_astronauts()

               # --- Create & Save Folium Map (improved with Satellite + Day/Night toggle) ---
        if iss_lat is not None and iss_lon is not None:
            map_center = [(user_lat + iss_lat) / 2, (user_lon + iss_lon) / 2]
        else:
            map_center = [user_lat, user_lon]

        # Initialize map (no default tiles so we can add our own)
        main_map = folium.Map(location=map_center, zoom_start=3, tiles=None)

        # Add multiple tile layers
        folium.TileLayer(
            tiles='CartoDB dark_matter',
            name='Dark Map',
            attr='&copy; OpenStreetMap contributors &copy; CARTO'
        ).add_to(main_map)

        folium.TileLayer(
            tiles='CartoDB positron',
            name='Light Map',
            attr='&copy; OpenStreetMap contributors &copy; CARTO'
        ).add_to(main_map)

        # Add Satellite imagery (Esri)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Tiles &copy; Esri',
            name='Satellite View (Esri)'
        ).add_to(main_map)

        # Add Day/Night Terminator (toggleable)
        terminator_group = folium.FeatureGroup(name="Day / Night Line", show=False)
        Terminator().add_to(terminator_group)
        terminator_group.add_to(main_map)

        # User location marker
        folium.Marker(
            [user_lat, user_lon],
            popup=f"<b>Your Location:</b><br>{full_address}",
            tooltip="Your Location",
            icon=folium.Icon(color='blue', icon='user', prefix='fa')
        ).add_to(main_map)

        # ISS marker (if available)
        if iss_lat and iss_lon:
            place_name = data_fetcher.get_place_name(iss_lat, iss_lon)
            folium.Marker(
                [iss_lat, iss_lon],
                popup=f"<b>ISS Current Position:</b><br>{place_name}",
                tooltip="ISS Position",
                icon=folium.Icon(color='red', icon='satellite', prefix='fa')
            ).add_to(main_map)

        # Add toggle control for layers
        folium.LayerControl(collapsed=False).add_to(main_map)

        # Save map to static file
        if not os.path.exists("static"):
            os.makedirs("static")
        map_file = os.path.join("static", "iss_map.html")
        main_map.save(map_file)

        # Build data for the results page
        result_data = {
            "city": user_city,
            "full_address": full_address,
            "place_name": place_name,
            "pass_times": pass_times,
            "astro_count": astro_count,
            "astro_names": astro_names,
            "collision_risks": collision_risks,
            "api_count": "—"  # optional placeholder for future tracking
        }

        return render_template("results.html", **result_data)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=False)
