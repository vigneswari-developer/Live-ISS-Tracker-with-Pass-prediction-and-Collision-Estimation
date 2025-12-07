🌍 Live ISS Tracker with Pass Prediction & Collision Estimation

🚀 Overview

This project provides a real-time, interactive web platform to track the International Space Station (ISS), view upcoming pass predictions, 
estimate potential space-debris collision risks, and explore astronaut information through dynamic links. Designed with lightweight architecture, 
it works smoothly even on moderate hardware, making it accessible for students, amateur astronomers, and space enthusiasts.


---

✨ Key Features

Live ISS Tracking: Real-time ISS coordinates using WhereTheISS.at API.

Pass Prediction: Future pass times via N2YO API or intelligent simulation fallback.

Collision Risk Estimation: Lightweight NASA-inspired model estimating potential conjunction events.

Astronaut Information: Live astronaut count and clickable Wikipedia links for each astronaut.

Interactive Map: Folium-based ISS and user-location visualization.

User-Friendly UI: HTML/CSS interface enhanced with space-themed visuals.

Lightweight Deployment: Runs on Flask with minimal system requirements.



---

🧠 System Architecture

The application follows a two-layer architecture:

Backend (data_fetcher.py)

Geocoding (Nominatim API)

ISS live position retrieval

N2YO pass prediction

Astronaut data retrieval (OpenNotify API)

Collision estimation module


Frontend (app.py + Templates)

Flask-based routing and request handling

Map rendering (Folium → HTML)

Results assembly and user presentation

Space-themed UI with static assets



---

🛠️ Tech Stack

Python 3.13

Flask

Folium

Requests (API handling)

HTML, CSS (Frontend)

APIs Used:

Nominatim (Geocoding)

WhereTheISS.at (Live ISS Position)

N2YO (Pass Prediction)

OpenNotify (Astronaut Information)




---

📦 Installation & Setup

git clone https://github.com/vigneswari-developer/Live-ISS-Tracker-with-Pass-prediction-and-Collision-Estimation.git
cd Live-ISS-Tracker-with-Pass-prediction-and-Collision-Estimation

pip install -r requirements.txt

python app.py

Open your browser and visit:
http://127.0.0.1:5000


---

📷 Screenshots

![nn1](https://github.com/user-attachments/assets/e089835e-fe98-4b8a-b5c0-424cea00cb3d)


![ff2](https://github.com/user-attachments/assets/75e893d9-94c9-4c58-a300-2d33dd8b5cb1)


![ff3](https://github.com/user-attachments/assets/9a43ffc3-a2e2-48d2-963b-27b3cfc04b4c)


![ff6](https://github.com/user-attachments/assets/43b3c42c-6ab3-4715-b1f9-e2798e11a147)


---

💡 Applications

Educational demonstrations

Amateur astronomy observations

Real-time ISS awareness

Space research learning tools

Interactive dashboards for students



---

🔮 Future Enhancements

Multi-satellite tracking

Historical pass data storage

3D orbital visualization

Automated global city suggestions



---

📚 References

1. Nominatim API – OpenStreetMap Geocoding


2. WhereTheISS.at – ISS Real-Time Position


3. N2YO Satellite Tracking API


4. OpenNotify Astronaut Information Service


5. Folium Mapping Library


6. Flask Web Framework


👩‍💻 Author

K. Vigneshwari
MCA – Space Technology Mini Project
