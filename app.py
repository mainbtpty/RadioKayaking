import streamlit as st
import requests
from datetime import datetime, timedelta
from gtts import gTTS
from io import BytesIO
import pandas as pd

st.set_page_config(page_title="Cape Kayak Adventure Radio FM", layout="wide")

# Reliable 90s stream
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

st.markdown("""
Welcome to **Cape Kayak Adventure Radio FM** – non-stop 90s hits + real-time & hourly forecast for safe kayaking in Three Anchor Bay!
""")

# Background radio
if not st.session_state.muted:
    st.audio(RADIO_STREAM_URL, format="audio/mp3", autoplay=True)
    st.markdown("<style>audio { display: none; }</style>", unsafe_allow_html=True)

# Weather update every 10 minutes
now = datetime.now()
if now - st.session_state.last_weather_update >= timedelta(minutes=10):
    try:
        # Current + hourly (incl. wave_height)
        forecast_url = (
            "https://api.open-meteo.com/v1/forecast?latitude=-33.9083&longitude=18.3958"
            "&current=temperature_2m,apparent_temperature,wind_speed_10m,wind_direction_10m,visibility"
            "&hourly=temperature_2m,apparent_temperature,wind_speed_10m,wind_direction_10m,visibility,wave_height"
            "&timezone=auto"
        )
        marine_url = (
            "https://marine-api.open-meteo.com/v1/marine?latitude=-33.9083&longitude=18.3958"
            "&current=wave_height,swell_wave_height"
        )

        forecast_resp = requests.get(forecast_url, timeout=10).json()
        marine_resp = requests.get(marine_url, timeout=10).json()

        st.session_state.weather_data = {
            'current': forecast_resp['current'],
            'hourly': forecast_resp['hourly'],
            'marine_current': marine_resp['current']
        }
        st.session_state.last_weather_update = now

    except Exception as e:
        st.warning(f"Update failed: {str(e)}. Using last data or refresh.")

data = st.session_state.weather_data.get('current', {})
hourly = st.session_state.weather_data.get('hourly', {})
marine_current = st.session_state.weather_data.get('marine_current', {})

# Current Conditions
st.header("🌤️ Current Kayaking Conditions – Three Anchor Bay")
if data:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Temperature", f"{data.get('temperature_2m', 'N/A')}°C", f"Feels {data.get('apparent_temperature', 'N/A')}°C")
    with col2:
        st.metric("Wind", f"{data.get('wind_speed_10m', 'N/A')} km/h", f"from {data.get('wind_direction_10m', 'N/A')}°")
    with col3:
        wave_h = marine_current.get('wave_height')
        swell_h = marine_current.get('swell_wave_height')
        wave_display = f"{wave_h:.1f} m" if wave_h is not None else "N/A"
        swell_display = f"{swell_h:.1f} m" if swell_h is not None else "N/A"
        st.metric("Wave Height", wave_display, f"Swell: {swell_display}")
    with col4:
        vis = data.get('visibility', 10000)
        vis_display = f"{vis} m" if vis is not None else "N/A"
        st.metric("Visibility", vis_display)
        if vis is not None and vis < 1000:
            st.error("Heavy Fog – Very Low Visibility! Do not launch.")
        elif vis is not None and vis < 5000:
            st.warning("Foggy – Reduced Visibility. Caution advised.")
        elif vis is not None:
            st.success("Good Visibility")

    # Suitability (incl. wave & fog/visibility)
    wind_val = data.get('wind_speed_10m') or 0
    wave_val = marine_current.get('wave_height') or 0.0
    vis_val = data.get('visibility') or 10000

    if wind_val > 25 or wave_val > 1.5 or vis_val < 1000:
        assessment = "Poor – high wind, waves, fog, or low visibility. No go today."
        color = "🔴"
    elif wind_val > 15 or wave_val > 1 or vis_val < 5000:
        assessment = "Moderate – caution for wind, waves or fog. Experienced only."
        color = "🟡"
    else:
        assessment = "Good – calm, clear, and ideal for paddling!"
        color = "🟢"

    st.subheader("Kayaking Suitability (incl. Waves & Fog/Visibility)")
    st.markdown(f"**{color} {assessment}**")
    st.write(f"Updated: {datetime.fromisoformat(data['time']).strftime('%Y-%m-%d %H:%M')} SAST")

    # DJ forecast text
    wave_text = f"{wave_val:.1f} m" if wave_val > 0 else "N/A"
    forecast_text = f"Hey paddlers! Cape Kayak Adventure Radio DJ here with the latest for Three Anchor Bay: Temp {data.get('temperature_2m')}°C (feels {data.get('apparent_temperature')}°C), wind {data.get('wind_speed_10m')} km/h from {data.get('wind_direction_10m')}°. Waves {wave_text}. Visibility {vis_display} – watch for fog if low! {assessment.lower()} Stay safe and keep vibing!"

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

# Concise Hourly Table with Full Row Coloring
st.header("⏰ Hourly Forecast – Next 24 Hours")
if 'hourly' in st.session_state:
    hourly = st.session_state.hourly
    times = hourly['time'][:24]
    temps = hourly['temperature_2m'][:24]
    winds = hourly['wind_speed_10m'][:24]
    viss = hourly['visibility'][:24]
    waves = hourly.get('wave_height', [None] * len(times))[:24]

    df_data = []
    row_colors = []

    for i in range(len(times)):
        t_str = datetime.fromisoformat(times[i]).strftime('%H:%M')
        temp_str = f"{temps[i]}°"
        wind_str = f"{winds[i]}"
        vis_km = viss[i] / 1000 if viss[i] is not None else None
        vis_str = f"{vis_km:.1f} km" if vis_km is not None else "N/A"
        wave_str = f"{waves[i]:.1f}" if waves[i] is not None else "N/A"

        wind_v = winds[i]
        wave_v = waves[i] if waves[i] is not None else 0.0
        vis_v = viss[i] if viss[i] is not None else 10000

        if wind_v > 25 or wave_v > 1.5 or vis_v < 1000:
            suit_text = "Poor"
            bg_color = "#ffcccc"
        elif wind_v > 15 or wave_v > 1 or vis_v < 5000:
            suit_text = "Mod"
            bg_color = "#fff3cd"
        else:
            suit_text = "Good"
            bg_color = "#d4edda"

        df_data.append([t_str, temp_str, wind_str, vis_str, wave_str, suit_text])
        row_colors.append(bg_color)

    df = pd.DataFrame(df_data, columns=["Time", "Temp", "Wind", "Vis", "Wave", "Suit"])

    def row_color(row):
        color = row_colors[row.name]
        return [f'background-color: {color}' for _ in row]

    styled_df = df.style.apply(row_color, axis=1)

    # Show first 12 hours + expander for full
    st.dataframe(styled_df.head(12), use_container_width=True, hide_index=True)
    with st.expander("Show full 24 hours"):
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

else:
    st.info("Hourly data loading...")

# Daily Forecasts (Tomorrow & Day After) – keep as before

# Safety Tips, Guided Tours, Footer – keep your existing sections
