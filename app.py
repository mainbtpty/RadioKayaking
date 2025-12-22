import streamlit as st
import requests
from datetime import datetime, timedelta
from gtts import gTTS
from io import BytesIO
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Cape Kayak Adventure Radio FM", layout="wide")

# Refresh every 30 seconds to check for updates
st_autorefresh(interval=30 * 1000, key="data_refresh")

# Reliable 90s pop hits stream
RADIO_STREAM_URL = "https://listen.181fm.com/181-star90s_128k.mp3"

# Session state
if 'muted' not in st.session_state:
    st.session_state.muted = True
if 'last_weather_update' not in st.session_state:
    st.session_state.last_weather_update = datetime.now() - timedelta(minutes=10)  # Force initial update
if 'last_forecast' not in st.session_state:
    st.session_state.last_forecast = datetime.now() - timedelta(minutes=3)  # Force initial on unmute
if 'first_unmute' not in st.session_state:
    st.session_state.first_unmute = False

# Header with Toggle
col1, col2 = st.columns([1, 6])
with col1:
    if st.session_state.muted:
        if st.button("🔇 Sound Off", key="toggle"):
            st.session_state.muted = False
            st.session_state.first_unmute = True
            st.session_state.last_forecast = datetime.now() - timedelta(minutes=3)  # Trigger immediate forecast
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
Click the button to turn on sound. Weather updates every 10 min, spoken forecast every 3 min (DJ style, overlays music).
""")

# Background radio
if not st.session_state.muted:
    st.audio(RADIO_STREAM_URL, format="audio/mp3", autoplay=True)
    st.markdown("<style>audio { display: none; }</style>", unsafe_allow_html=True)

# Weather Section
st.header("🌤️ Current Kayaking Conditions in Three Anchor Bay")
lat, lon = -33.9083, 18.3958

forecast_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,wind_speed_10m,wind_direction_10m"
marine_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,swell_wave_height"

# Update weather if due
now = datetime.now()
if now - st.session_state.last_weather_update >= timedelta(minutes=10):
    try:
        forecast_data = requests.get(forecast_url, timeout=10).json()["current"]
        marine_data = requests.get(marine_url, timeout=10).json()["current"]

        st.session_state.temp = forecast_data.get("temperature_2m", "N/A")
        st.session_state.feels_like = forecast_data.get("apparent_temperature", "N/A")
        st.session_state.wind_speed = forecast_data.get("wind_speed_10m", "N/A")
        st.session_state.wind_dir = forecast_data.get("wind_direction_10m", "N/A")
        st.session_state.wave_height = marine_data.get("wave_height", [1.0])[0] if isinstance(marine_data.get("wave_height"), list) else marine_data.get("wave_height", 1.0)
        st.session_state.swell_height = marine_data.get("swell_wave_height", [0.5])[0] if isinstance(marine_data.get("swell_wave_height"), list) else marine_data.get("swell_wave_height", 0.5)

        wind_speed_val = st.session_state.wind_speed if isinstance(st.session_state.wind_speed, (int, float)) else 0
        wave_height_val = st.session_state.wave_height
        if wind_speed_val > 25 or wave_height_val > 1.5:
            st.session_state.assessment = "Poor conditions – strong winds or high waves. Avoid paddling, especially beginners."
            st.session_state.color = "🔴"
        elif wind_speed_val > 15 or wave_height_val > 1:
            st.session_state.assessment = "Moderate conditions – caution advised. Experienced paddlers only."
            st.session_state.color = "🟡"
        else:
            st.session_state.assessment = "Good conditions – calm and ideal for all levels!"
            st.session_state.color = "🟢"

        st.session_state.last_weather_update = now

    except Exception:
        st.warning("Weather update failed – using last data.")

# Display weather from session
if 'temp' in st.session_state:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Temperature", f"{st.session_state.temp}°C" if st.session_state.temp != "N/A" else "N/A", f"Feels {st.session_state.feels_like}°C")
    with col2:
        st.metric("Wind Speed", f"{st.session_state.wind_speed} km/h" if st.session_state.wind_speed != "N/A" else "N/A", f"Dir: {st.session_state.wind_dir}°")
    with col3:
        st.metric("Wave Height", f"{st.session_state.wave_height:.1f} m", f"Swell: {st.session_state.swell_height:.1f} m")

    st.subheader("Kayaking Suitability")
    st.markdown(f"**{st.session_state.color} {st.session_state.assessment}**")
    st.write(f"Updated: {st.session_state.last_weather_update.strftime('%Y-%m-%d %H:%M')}")

    # DJ-style forecast text
    forecast_text = f"Hey paddlers, this is your Cape Kayak Adventure Radio DJ with the latest forecast for Three Anchor Bay! Temperature's at {st.session_state.temp} degrees, feeling like {st.session_state.feels_like}. Winds blowing at {st.session_state.wind_speed} km/h from {st.session_state.wind_dir} degrees. Waves are {st.session_state.wave_height:.1f} meters high. Overall, {st.session_state.assessment.lower()} Stay safe out there and keep those 90s vibes rolling!"

    # Auto-speak forecast if due and radio on
    if not st.session_state.muted and (st.session_state.first_unmute or now - st.session_state.last_forecast >= timedelta(minutes=3)):
        with st.spinner("Broadcasting DJ forecast..."):
            tts = gTTS(text=forecast_text, lang='en')
            audio_bytes = BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)

        # JS to lower/restore music volume during forecast
        js_script = """
        <script>
        function fadeVolume(audio, targetVol, duration) {
            let currentVol = audio.volume;
            let step = (targetVol - currentVol) / (duration / 100);
            let interval = setInterval(() => {
                currentVol += step;
                audio.volume = Math.max(0, Math.min(1, currentVol));
                if (Math.abs(currentVol - targetVol) < Math.abs(step)) {
                    audio.volume = targetVol;
                    clearInterval(interval);
                }
            }, 100);
        }

        const audios = document.getElementsByTagName('audio');
        if (audios.length >= 2) {
            const music = audios[0];
            const forecast = audios[1];
            forecast.addEventListener('play', () => fadeVolume(music, 0.3, 2000));  // Fade down over 2 sec
            forecast.addEventListener('ended', () => fadeVolume(music, 1.0, 2000));  // Fade up over 2 sec
        }
        </script>
        """
        st.components.v1.html(js_script, height=0)

        st.session_state.last_forecast = now
        st.session_state.first_unmute = False  # Reset after first

    # Manual button
    if st.button("🔊 Speak Full Weather Forecast (DJ Style)"):
        tts = gTTS(text=forecast_text, lang='en')
        audio = BytesIO()
        tts.write_to_fp(audio)
        audio.seek(0)
        st.audio(audio, format="audio/mp3", autoplay=True)

# Safety Tips & Guided Tours (unchanged)
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
**Music:** 181.fm Star 90's | **Voice:** gTTS | Built with ❤️ Streamlit  
Developer: Oni Charles – LinkedIn: [linkedin.com/in/charles-oni-b45a91253](https://www.linkedin.com/in/charles-oni-b45a91253/)
Note: Add 'streamlit-autorefresh' to requirements.txt for auto-updates.
""")
