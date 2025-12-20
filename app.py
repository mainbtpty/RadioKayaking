import streamlit as st
import requests
from datetime import datetime
from gtts import gTTS
from io import BytesIO

st.set_page_config(page_title="Cape Kayak Adventure Radio", layout="wide")

# Direct 90s radio stream URL
RADIO_STREAM_URL = "https://listen.181fm.com/181-star90s_128k.mp3"

# Session state for sound toggle (True = muted)
if 'muted' not in st.session_state:
    st.session_state.muted = True  # Start muted – one click to enable sound

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

# Radio Jingle on Load (plays once per session)
if 'jingle_played' not in st.session_state:
    st.session_state.jingle_played = True
    jingle_text = "Welcome to Cape Kayak Adventure Radio FM in Three Anchor Bay!"
    tts = gTTS(text=jingle_text, lang='en')
    jingle_audio = BytesIO()
    tts.write_to_fp(jingle_audio)
    jingle_audio.seek(0)
    st.audio(jingle_audio, format="audio/mp3", autoplay=True)

st.markdown("""
Welcome to **Cape Kayak Adventure Radio FM** – your AI-powered companion for kayaking in Three Anchor Bay, Cape Town!  
Non-stop 90s pop hits in the background. Click the button to turn sound on (one click required by browsers). Toggle anytime.
""")

# Hidden background audio player
st.audio(
    RADIO_STREAM_URL,
    format="audio/mp3",
    autoplay=not st.session_state.muted,
    start_time=0
)

st.markdown(
    """
    <style>
        audio { display: none; }
    </style>
    """,
    unsafe_allow_html=True
)

# Weather & Conditions
st.header("🌤️ Current Kayaking Conditions in Three Anchor Bay")
lat, lon = -33.9083, 18.3958

forecast_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,wind_speed_10m,wind_direction_10m"
marine_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,wave_period,wind_wave_height,swell_wave_height"

try:
    forecast_data = requests.get(forecast_url).json()
    marine_data = requests.get(marine_url).json()

    current = forecast_data["current"]
    marine_current = marine_data["current"]

    temp = current["temperature_2m"]
    feels_like = current["apparent_temperature"]
    wind_speed = current["wind_speed_10m"]
    wind_dir = current["wind_direction_10m"]
    wave_height = marine_current["wave_height"][0] if isinstance(marine_current["wave_height"], list) else marine_current["wave_height"]
    swell_height = marine_current.get("swell_wave_height", [None])[0] or "Low"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Temperature", f"{temp}°C", f"Feels like {feels_like}°C")
    with col2:
        st.metric("Wind Speed", f"{wind_speed} km/h", f"Direction: {wind_dir}°")
    with col3:
        st.metric("Wave Height", f"{wave_height} m", f"Swell: {swell_height} m")

    # Safety assessment
    if wind_speed > 25 or wave_height > 1.5:
        assessment = "Poor conditions – strong winds or high waves. Avoid paddling today, especially for beginners."
        color = "🔴"
    elif wind_speed > 15 or wave_height > 1:
        assessment = "Moderate conditions – caution advised. Best for experienced paddlers."
        color = "🟡"
    else:
        assessment = "Good conditions – calm and ideal for all levels. Get out on the water!"
        color = "🟢"

    st.subheader("Kayaking Suitability")
    st.markdown(f"**{color} {assessment}**")
    st.write(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Full spoken forecast text
    forecast_text = f"Weather forecast for kayaking in Three Anchor Bay, Cape Town: Current temperature is {temp} degrees Celsius, feeling like {feels_like}. Wind speed {wind_speed} kilometers per hour from {wind_dir} degrees. Wave height {wave_height} meters with swell around {swell_height} meters. Overall: {assessment} Safe paddling!"

    if st.button("🔊 Speak Full Weather Forecast"):
        with st.spinner("Generating voice..."):
            tts = gTTS(text=forecast_text, lang='en')
            audio_bytes = BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)

except Exception:
    st.error("Weather data temporarily unavailable. Check back soon!")

# Safety Tips (unchanged)
st.header("🛶 Safety Tips for Three Anchor Bay Kayaking")
# ... (keep your existing expanders here)

# Guided Tours Section
st.header("🛶 Cape Kayak Adventure Guided Tours")
st.markdown("""
Ready for a real adventure? Book a **guided kayak tour** with the experts right here in Three Anchor Bay!

**Cape Kayak Adventures** (the original since 1995) offers breathtaking guided trips along the Atlantic Seaboard. Paddle with seals, dolphins, penguins, and even whales in season – all with stunning views of Table Mountain!

- No experience needed
- Morning, sunset, and full moon tours
- Safe, fun, and unforgettable

Visit their official site to book: [kayak.co.za](https://kayak.co.za/)

Highly recommended for beginners and pros alike!
""")

# Footer
st.markdown("---")
st.markdown("""
**Music Source:** 181.fm - Star 90's (non-stop 90s pop hits)  
Built with ❤️ using Streamlit | Voice powered by gTTS  
One click required to enable background music (browser policy).
""")
