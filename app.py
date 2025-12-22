import streamlit as st
import requests
from datetime import datetime, timedelta
from gtts import gTTS
from io import BytesIO

st.set_page_config(page_title="Cape Kayak Adventure Radio FM", layout="wide")

# Reliable 90s stream
RADIO_STREAM_URL = "https://listen.181fm.com/181-star90s_128k.mp3"

# Session state initialization
if 'muted' not in st.session_state:
    st.session_state.muted = True
if 'last_weather_update' not in st.session_state:
    st.session_state.last_weather_update = datetime.now() - timedelta(minutes=10)
if 'last_forecast' not in st.session_state:
    st.session_state.last_forecast = datetime.now() - timedelta(minutes=3)
if 'first_unmute' not in st.session_state:
    st.session_state.first_unmute = True
if 'forecast_key' not in st.session_state:
    st.session_state.forecast_key = 0  # Unique key for forecast audio

# Header & Toggle
col1, col2 = st.columns([1, 6])
with col1:
    if st.session_state.muted:
        if st.button("🔇 Sound Off", key="toggle"):
            st.session_state.muted = False
            st.session_state.first_unmute = True
            st.session_state.last_forecast = datetime.now() - timedelta(minutes=3)
            st.session_state.forecast_key += 1
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
Weather updates every 10 min • DJ forecast every 3 min (auto-plays over music with volume ducking).
""")

# Background radio (hidden)
if not st.session_state.muted:
    st.audio(RADIO_STREAM_URL, format="audio/mp3", autoplay=True, key="radio_stream")
    st.markdown("<style>audio { display: none; }</style>", unsafe_allow_html=True)

# Weather update every 10 minutes
now = datetime.now()
if now - st.session_state.last_weather_update >= timedelta(minutes=10):
    try:
        forecast_data = requests.get(
            "https://api.open-meteo.com/v1/forecast?latitude=-33.9083&longitude=18.3958&current=temperature_2m,apparent_temperature,wind_speed_10m,wind_direction_10m",
            timeout=10
        ).json()["current"]
        marine_data = requests.get(
            "https://marine-api.open-meteo.com/v1/marine?latitude=-33.9083&longitude=18.3958&current=wave_height,swell_wave_height",
            timeout=10
        ).json()["current"]

        st.session_state.temp = forecast_data.get("temperature_2m", "N/A")
        st.session_state.feels_like = forecast_data.get("apparent_temperature", "N/A")
        st.session_state.wind_speed = forecast_data.get("wind_speed_10m", "N/A")
        st.session_state.wind_dir = forecast_data.get("wind_direction_10m", "N/A")
        st.session_state.wave_height = marine_data.get("wave_height", [1.0])[0] if isinstance(marine_data.get("wave_height"), list) else marine_data.get("wave_height", 1.0)
        st.session_state.swell_height = marine_data.get("swell_wave_height", [0.5])[0] if isinstance(marine_data.get("swell_wave_height"), list) else marine_data.get("swell_wave_height", 0.5)

        wind_val = st.session_state.wind_speed if isinstance(st.session_state.wind_speed, (int, float)) else 0
        wave_val = st.session_state.wave_height
        if wind_val > 25 or wave_val > 1.5:
            st.session_state.assessment = "Poor conditions – strong winds or high waves. Avoid paddling today."
            st.session_state.color = "🔴"
        elif wind_val > 15 or wave_val > 1:
            st.session_state.assessment = "Moderate conditions – caution advised. Experienced paddlers only."
            st.session_state.color = "🟡"
        else:
            st.session_state.assessment = "Good conditions – calm and perfect for kayaking!"
            st.session_state.color = "🟢"

        st.session_state.last_weather_update = now

    except Exception:
        if 'temp' not in st.session_state:
            st.session_state.temp = st.session_state.feels_like = st.session_state.wind_speed = "N/A"
            st.session_state.assessment = "Data unavailable"
            st.session_state.color = "⚪"

# Display weather
st.header("🌤️ Current Kayaking Conditions in Three Anchor Bay")
if 'temp' in st.session_state:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Temperature", f"{st.session_state.temp}°C", f"Feels {st.session_state.feels_like}°C")
    with col2:
        st.metric("Wind Speed", f"{st.session_state.wind_speed} km/h", f"Dir: {st.session_state.wind_dir}°")
    with col3:
        st.metric("Wave Height", f"{st.session_state.wave_height:.1f} m", f"Swell: {st.session_state.swell_height:.1f} m")

    st.subheader("Kayaking Suitability")
    st.markdown(f"**{st.session_state.color} {st.session_state.assessment}**")
    update_time = st.session_state.last_weather_update.strftime("%Y-%m-%d %H:%M")
    st.write(f"Updated: {update_time}")

    # DJ-style forecast text
    forecast_text = f"Hey paddlers, this is your Cape Kayak Adventure Radio DJ with the latest from Three Anchor Bay! We're sitting at {st.session_state.temp} degrees, feeling like {st.session_state.feels_like}. Winds at {st.session_state.wind_speed} km/h from {st.session_state.wind_dir} degrees. Waves running {st.session_state.wave_height:.1f} meters. Bottom line: {st.session_state.assessment.lower()} Keep those paddles ready and enjoy the 90s vibes!"

    # Auto-play forecast if due
    if not st.session_state.muted and (st.session_state.first_unmute or now - st.session_state.last_forecast >= timedelta(minutes=3)):
        tts = gTTS(text=forecast_text, lang='en')
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        st.audio(audio_bytes, format="audio/mp3", autoplay=True, key=f"forecast_{st.session_state.forecast_key}")

        # Volume ducking JavaScript
        st.components.v1.html(
            """
            <script>
            const audios = document.querySelectorAll('audio');
            if (audios.length >= 2) {
                const music = audios[0];
                const speech = audios[1];
                const originalVol = music.volume || 1.0;
                speech.addEventListener('play', () => music.volume = 0.3);
                speech.addEventListener('ended', () => music.volume = originalVol);
            }
            </script>
            """,
            height=0
        )

        st.session_state.last_forecast = now
        if st.session_state.first_unmute:
            st.session_state.first_unmute = False
        st.session_state.forecast_key += 1

    # Manual forecast button
    if st.button("🔊 Speak Forecast (DJ Style)"):
        tts = gTTS(text=forecast_text, lang='en')
        audio = BytesIO()
        tts.write_to_fp(audio)
        audio.seek(0)
        st.audio(audio, format="audio/mp3", autoplay=True, key=f"manual_forecast_{st.session_state.forecast_key}")
        st.session_state.forecast_key += 1

# Safety Tips
st.header("🛶 Safety Tips for Three Anchor Bay Kayaking")

with st.expander("For Beginners"):
    beginner_tips = """
    - Always wear a PFD (life jacket)—it's mandatory on the Atlantic.
    - Paddle with a buddy or join a guided group.
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
    - Avoid solo paddles in winds over 20 km/h or waves over 1.5 meters.
    - Always tell someone your float plan.
    """
    st.markdown(experienced_tips)
    if st.button("🔊 Read Experienced Tips Aloud", key="experienced"):
        tts = gTTS(text=experienced_tips.replace("- ", "").replace("\n", " "), lang='en')
        audio = BytesIO()
        tts.write_to_fp(audio)
        audio.seek(0)
        st.audio(audio, format="audio/mp3", autoplay=True)

st.markdown("Sources: Local guides & general ocean safety best practices.")

# Guided Tours Section (from your document)
st.header("🛶 Cape Kayak Adventure Guided Tours")
st.markdown("""
Experience the best views of Cape Town and get up close and personal with ocean life during our guided kayak trips.

**Cape Kayak Adventures** has been operating fun and safe kayak tours since 1995 on the Atlantic Seaboard. Based in the heart of the Table Mountain National Marine Park.

- Morning, sunset, and full moon tours (weather permitting)
- Explore kelp forests, shipwrecks, and spot seals, Heaviside’s dolphins, whales (in season), sunfish
- No experience needed – expert guides teach basics
- Top rated on TripAdvisor

**Meeting point:** Three Anchor Bay Beach – Beach Shed

Book now: [kayak.co.za](https://kayak.co.za/)
""")

# Footer
st.markdown("---")
st.markdown("""
**Music:** 181.fm Star 90's | **Voice:** gTTS | Built with ❤️ Streamlit  
Developer: Oni Charles – [LinkedIn](https://www.linkedin.com/in/charles-oni-b45a91253/)
""")
