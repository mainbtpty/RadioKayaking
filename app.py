import streamlit as st
import requests
from datetime import datetime
from gtts import gTTS
from io import BytesIO

st.set_page_config(page_title="Cape Kayak Adventure Radio FM", layout="wide")

# Reliable 90s pop hits stream (181.fm Star 90's – active and high-quality)
RADIO_STREAM_URL = "https://listen.181fm.com/181-star90s_128k.mp3"

# Session state for mute toggle
if 'muted' not in st.session_state:
    st.session_state.muted = True  # Start muted (silent until click)

# Header with Toggle Button
col1, col2 = st.columns([1, 6])
with col1:
    if st.session_state.muted:
        if st.button("🔇 Sound Off", key="toggle"):
            st.session_state.muted = False
            st.rerun()
    else:
        if st.button("🔊 Sound On", key="toggle"):
            st.session_state.muted = True
            st.rerun()

with col2:
    status = "🔇 (click to turn on)" if st.session_state.muted else "🔊"
    st.title(f"🌊 Cape Kayak Adventure Radio FM  {status}")

st.markdown("""
Welcome to **Cape Kayak Adventure Radio FM** – non-stop 90s hits for kayakers in Three Anchor Bay, Cape Town!  
Click the button to turn on sound (one click required by browsers). Music starts right away.
""")

# Background radio – only when unmuted, hidden player
if not st.session_state.muted:
    st.audio(RADIO_STREAM_URL, format="audio/mp3", autoplay=True)
    st.markdown("<style>audio { display: none; }</style>", unsafe_allow_html=True)

# Weather Section (robust with fallbacks)
st.header("🌤️ Current Kayaking Conditions in Three Anchor Bay")
lat, lon = -33.9083, 18.3958

forecast_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,wind_speed_10m,wind_direction_10m"
marine_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,swell_wave_height"

try:
    forecast_data = requests.get(forecast_url, timeout=10).json()["current"]
    marine_data = requests.get(marine_url, timeout=10).json()["current"]

    temp = forecast_data.get("temperature_2m", "N/A")
    feels_like = forecast_data.get("apparent_temperature", "N/A")
    wind_speed = forecast_data.get("wind_speed_10m", "N/A")
    wind_dir = forecast_data.get("wind_direction_10m", "N/A")
    wave_height = marine_data.get("wave_height", [1.0])[0] if isinstance(marine_data.get("wave_height"), list) else marine_data.get("wave_height", 1.0)
    swell_height = marine_data.get("swell_wave_height", [0.5])[0] if isinstance(marine_data.get("swell_wave_height"), list) else marine_data.get("swell_wave_height", 0.5)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Temperature", f"{temp}°C" if temp != "N/A" else "N/A", f"Feels {feels_like}°C")
    with col2:
        st.metric("Wind Speed", f"{wind_speed} km/h" if wind_speed != "N/A" else "N/A", f"Dir: {wind_dir}°")
    with col3:
        st.metric("Wave Height", f"{wave_height:.1f} m", f"Swell: {swell_height:.1f} m")

    # Assessment
    if not isinstance(wind_speed, (int, float)) or wind_speed > 25 or wave_height > 1.5:
        assessment, color = "Poor – strong winds/high waves. Avoid paddling.", "🔴"
    elif wind_speed > 15 or wave_height > 1:
        assessment, color = "Moderate – caution advised. Experienced only.", "🟡"
    else:
        assessment, color = "Good – calm and perfect for kayaking!", "🟢"

    st.subheader("Kayaking Suitability")
    st.markdown(f"**{color} {assessment}**")
    st.write(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    forecast_text = f"Kayak forecast for Three Anchor Bay: Temperature {temp} degrees, feels like {feels_like}. Wind {wind_speed} km/h from {wind_dir} degrees. Waves {wave_height:.1f} meters. {assessment} Paddle safe!"

    if st.button("🔊 Speak Full Weather Forecast"):
        tts = gTTS(text=forecast_text, lang='en')
        audio = BytesIO()
        tts.write_to_fp(audio)
        audio.seek(0)
        st.audio(audio, format="audio/mp3", autoplay=True)

except Exception:
    st.warning("Weather data temporarily unavailable – refresh to retry.")

# Safety Tips
st.header("🛶 Safety Tips for Three Anchor Bay Kayaking")

with st.expander("For Beginners"):
    beginner_tips = """
    - Always wear a PFD (life jacket)—it's mandatory on the Atlantic.
    - Paddle with a buddy or join a guided group (like Kaskazi Kayaks).
    - Mornings are often calmer due to shelter from Table Mountain.
    - Stay close to shore; currents can be strong.
    - Wear sunscreen, a hat, and quick-dry clothes—the sun is intense here.
    """
    st.markdown(beginner_tips)
    if st.button("🔊 Read Beginner Tips Aloud", key="beginner"):
        tts = gTTS(text=beginner_tips.replace("- ", "").replace("\n", " "), lang='en')
        audio = BytesIO()
        tts.write_to_fp(audio)
        audio.seek(0)
        st.audio(audio, format="audio/mp3", autoplay=True)

with st.expander("For Experienced Paddlers"):
    experienced_tips = """
    - Monitor swell and offshore winds—the Southeaster can build quickly.
    - Know your escape points like ladders and beaches along the Sea Point promenade.
    - Cold water shock is a risk—dress for immersion.
    - Avoid solo paddles in winds over 20 kilometers per hour or waves over 1.5 meters.
    - Always tell someone your float plan.
    """
    st.markdown(experienced_tips)
    if st.button("🔊 Read Experienced Tips Aloud", key="experienced"):
        tts = gTTS(text=experienced_tips.replace("- ", "").replace("\n", " "), lang='en')
        audio = BytesIO()
        tts.write_to_fp(audio)
        audio.seek(0)
        st.audio(audio, format="audio/mp3", autoplay=True)

st.markdown("Sources: Local guides like Kaskazi Kayaks & general ocean safety best practices.")

# Guided Tours (updated with your document info)
st.header("🛶 Cape Kayak Adventure Guided Tours")
st.markdown("""
Experience the best views of Cape Town and get up close with ocean life!

**Cape Kayak Adventures** has been operating fun and safe tours since 1995 in the Table Mountain National Marine Park. Based at Three Anchor Bay Beach (meet at the Beach Shed).

- Morning, sunset, and full moon tours (weather permitting)
- Spot seals, dolphins, whales (in season), sunfish, and explore kelp forests
- No experience needed – expert guides teach basics
- Top rated on TripAdvisor

Book now: [kayak.co.za](https://kayak.co.za/)
""")

# Footer
st.markdown("---")
st.markdown("""
**Music:** 181.fm Star 90's (non-stop 90s pop hits) | **Voice:** gTTS | Built with ❤️ Streamlit  
Developer: Oni Charles – LinkedIn: [linkedin.com/in/charles-oni-b45a91253](https://www.linkedin.com/in/charles-oni-b45a91253/)
""")
