import streamlit as st
import requests
from datetime import datetime, timedelta
from gtts import gTTS
from io import BytesIO

st.set_page_config(page_title="Cape Kayak Adventure Radio FM", layout="wide")

# Stream URL
RADIO_STREAM_URL = "https://listen.181fm.com/181-star90s_128k.mp3"

# Session state
if 'muted' not in st.session_state:
    st.session_state.muted = True
if 'last_weather_update' not in st.session_state:
    st.session_state.last_weather_update = datetime.now() - timedelta(minutes=10)
if 'last_forecast' not in st.session_state:
    st.session_state.last_forecast = datetime.now() - timedelta(minutes=3)
if 'first_unmute' not in st.session_state:
    st.session_state.first_unmute = True
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = {}

# Header & Toggle
col1, col2 = st.columns([1, 6])
with col1:
    if st.session_state.muted:
        if st.button("🔇 Sound Off", key="toggle"):
            st.session_state.muted = False
            st.session_state.first_unmute = True
            st.session_state.last_forecast = datetime.now() - timedelta(minutes=3)
            st.rerun()
    else:
        if st.button("🔊 Sound On", key="toggle"):
            st.session_state.muted = True
            st.rerun()

with col2:
    status = "🔇 (click to turn on)" if st.session_state.muted else "🔊"
    st.title(f"🌊 Cape Kayak Adventure Radio FM  {status}")

st.markdown("Non-stop 90s hits + real-time + forecast weather for safe kayaking in Three Anchor Bay!")

# Background radio
if not st.session_state.muted:
    st.audio(RADIO_STREAM_URL, format="audio/mp3", autoplay=True)
    st.markdown("<style>audio { display: none; }</style>", unsafe_allow_html=True)

# Fetch / update weather
now = datetime.now()
if now - st.session_state.last_weather_update >= timedelta(minutes=10):
    try:
        # Current + hourly for visibility/fog
        current_url = "https://api.open-meteo.com/v1/forecast?latitude=-33.9083&longitude=18.3958&current=temperature_2m,apparent_temperature,wind_speed_10m,wind_direction_10m,visibility,cloud_cover_low,weather_code&hourly=visibility,cloud_cover_low&timezone=auto"
        daily_url = "https://api.open-meteo.com/v1/forecast?latitude=-33.9083&longitude=18.3958&daily=weather_code,temperature_2m_max,temperature_2m_min,wind_speed_10m_max,precipitation_probability_max&timezone=auto&forecast_days=3"

        current_resp = requests.get(current_url, timeout=10).json()
        daily_resp = requests.get(daily_url, timeout=10).json()

        st.session_state.weather_data = {
            'current': current_resp['current'],
            'daily': daily_resp['daily']
        }
        st.session_state.last_weather_update = now

    except Exception as e:
        st.warning(f"Update failed: {str(e)}. Using last data or refresh.")

data = st.session_state.weather_data.get('current', {})
daily = st.session_state.weather_data.get('daily', {})

# Current Conditions Layout
st.header("🌤️ Current Kayaking Conditions – Three Anchor Bay")
if data:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Temperature", f"{data.get('temperature_2m', 'N/A')}°C", f"Feels {data.get('apparent_temperature', 'N/A')}°C")
    with col2:
        st.metric("Wind", f"{data.get('wind_speed_10m', 'N/A')} km/h", f"from {data.get('wind_direction_10m', 'N/A')}°")
    with col3:
        st.metric("Visibility", f"{data.get('visibility', 'N/A')} m")
        vis = data.get('visibility', 10000)
        if vis < 1000:
            st.error("Heavy Fog – Very Low Visibility! Do not launch.")
        elif vis < 5000:
            st.warning("Foggy – Reduced Visibility. Caution advised.")
        else:
            st.success("Good Visibility")
    with col4:
        st.metric("Low Clouds/Fog Risk", f"{data.get('cloud_cover_low', 'N/A')}%")

    # Suitability with fog factor
    wind_val = data.get('wind_speed_10m', 0)
    vis_val = data.get('visibility', 10000)
    low_cloud = data.get('cloud_cover_low', 0)
    if wind_val > 25 or vis_val < 1000 or low_cloud > 80:
        assessment = "Poor – high wind, fog, or low visibility. No go today."
        color = "🔴"
    elif wind_val > 15 or vis_val < 5000 or low_cloud > 50:
        assessment = "Moderate – caution for wind/fog. Experienced only."
        color = "🟡"
    else:
        assessment = "Good – calm and clear. Perfect for paddling!"
        color = "🟢"

    st.subheader("Kayaking Suitability (incl. Fog/Visibility)")
    st.markdown(f"**{color} {assessment}**")
    st.write(f"Updated: {datetime.fromisoformat(data['time']).strftime('%Y-%m-%d %H:%M')} SAST")

    # DJ forecast text (current)
    forecast_text = f"Hey paddlers! Cape Kayak Adventure Radio DJ here with the latest for Three Anchor Bay: Temp {data.get('temperature_2m')}°C (feels {data.get('apparent_temperature')}°C), wind {data.get('wind_speed_10m')} km/h from {data.get('wind_direction_10m')}°. Visibility {data.get('visibility')} m – watch for fog if low! {assessment.lower()} Stay safe and keep vibing!"

    # Auto DJ forecast
    if not st.session_state.muted and (st.session_state.first_unmute or now - st.session_state.last_forecast >= timedelta(minutes=3)):
        tts = gTTS(text=forecast_text, lang='en')
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)

        st.components.v1.html(
            """
            <script>
            const audios = document.getElementsByTagName('audio');
            if (audios.length >= 2) {
                const music = audios[0];
                const speech = audios[1];
                speech.onplay = () => music.volume = 0.3;
                speech.onended = () => music.volume = 1.0;
            }
            </script>
            """,
            height=0
        )

        st.session_state.last_forecast = now
        st.session_state.first_unmute = False

    if st.button("🔊 Hear DJ Forecast Now"):
        tts = gTTS(text=forecast_text, lang='en')
        audio = BytesIO()
        tts.write_to_fp(audio)
        audio.seek(0)
        st.audio(audio, format="audio/mp3", autoplay=True)

else:
    st.info("Loading weather... refresh if empty.")

# Next-Day & Day-After Forecasts
st.header("📅 Forecast – Tomorrow & Day After")
if 'daily' in st.session_state.weather_data:
    daily_times = daily.get('time', [])
    daily_codes = daily.get('weather_code', [])
    daily_max_temp = daily.get('temperature_2m_max', [])
    daily_min_temp = daily.get('temperature_2m_min', [])
    daily_max_wind = daily.get('wind_speed_10m_max', [])
    daily_precip_prob = daily.get('precipitation_probability_max', [])

    if len(daily_times) >= 3:
        # Tomorrow (index 1), Day After (index 2)
        for day_offset, label in [(1, "Tomorrow"), (2, "Day After")]:
            with st.expander(f"{label} – {daily_times[day_offset]}"):
                st.metric("Max / Min Temp", f"{daily_max_temp[day_offset]}°C / {daily_min_temp[day_offset]}°C")
                st.metric("Max Wind", f"{daily_max_wind[day_offset]} km/h")
                st.metric("Precip Probability", f"{daily_precip_prob[day_offset]}%")
                st.write(f"Weather Code: {daily_codes[day_offset]} (check WMO codes for details)")
                # Simple fog note
                st.info("Fog risk: Not directly forecasted daily – rely on hourly visibility when closer to date.")
    else:
        st.info("Daily forecast loading...")

# Safety Tips & Guided Tours (unchanged, full from your doc)
st.header("🛶 Safety Tips for Three Anchor Bay Kayaking")
# ... paste your expanders here as before

st.header("🛶 Cape Kayak Adventure Guided Tours")
# ... paste the full markdown from your document as in previous code

# Footer
st.markdown("---")
st.markdown("""
**Music:** 181.fm Star 90's | **Voice:** gTTS | Built with ❤️ Streamlit  
Developer: Oni Charles – LinkedIn: [linkedin.com/in/charles-oni-b45a91253](https://www.linkedin.com/in/charles-oni-b45a91253/)
Data from Open-Meteo – real-time, but model runs may have slight delay.
""")
