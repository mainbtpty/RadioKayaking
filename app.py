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

# Header & Toggle
col1, col2 = st.columns([1, 6])
with col1:
    if st.session_state.muted:
        if st.button("🔇 Sound Off", key="toggle"):
            st.session_state.muted = False
            st.session_state.first_unmute = True
            st.session_state.last_forecast = datetime.now() - timedelta(minutes=3)  # Trigger forecast now
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
    st.audio(RADIO_STREAM_URL, format="audio/mp3", autoplay=True)
    st.markdown("<style>audio { display: none; }</style>", unsafe_allow_html=True)

# Weather update every 10 minutes
now = datetime.now()
if now - st.session_state.last_weather_update >= timedelta(minutes=10):
    try:
        forecast_data = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude=-33.9083&longitude=18.3958&current=temperature_2m,apparent_temperature,wind_speed_10m,wind_direction_10m",
            timeout=10
        ).json()["current"]
        marine_data = requests.get(
            f"https://marine-api.open-meteo.com/v1/marine?latitude=-33.9083&longitude=18.3958&current=wave_height,swell_wave_height",
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

# Display current weather
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
    st.write(f"Updated: {st.session_state.last_weather_update.strftime('%H:%M')}")

    # DJ-style forecast text
    forecast_text = f"Hey paddlers, this is your Cape Kayak Adventure Radio DJ with the latest from Three Anchor Bay! We're sitting at {st.session_state.temp} degrees, feeling like {st.session_state.feels_like}. Winds at {st.session_state.wind_speed} km/h from {st.session_state.wind_dir} degrees. Waves running {st.session_state.wave_height:.1f} meters. Bottom line: {st.session_state.assessment.lower()} Keep those paddles ready and enjoy the 90s vibes!"

    # Auto-play forecast if radio on and time elapsed
    if not st.session_state.muted and (st.session_state.first_unmute or now - st.session_state.last_forecast >= timedelta(minutes=3)):
        tts = gTTS(text=forecast_text, lang='en')
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)

        # JavaScript to duck music volume during forecast
        st.components.v1.html(
            """
            <script>
            const audios = document.getElementsByTagName('audio');
            if (audios.length >= 2) {
                const music = audios[0];
                const speech = audios[1];
                const originalVolume = music.volume || 1.0;
                
                speech.addEventListener('play', () => {
                    music.volume = 0.3;  // Duck music
                });
                speech.addEventListener('ended', () => {
                    music.volume = originalVolume;  // Restore
                });
            }
            </script>
            """,
            height=0
        )

        st.session_state.last_forecast = now
        if st.session_state.first_unmute:
            st.session_state.first_unmute = False

    # Manual forecast button
    if st.button("🔊 Speak Forecast (DJ Style)"):
        tts = gTTS(text=forecast_text, lang='en')
        audio = BytesIO()
        tts.write_to_fp(audio)
        audio.seek(0)
        st.audio(audio, format="audio/mp3", autoplay=True)

# Safety Tips & Tours (unchanged)
st.header("🛶 Safety Tips for Three Anchor Bay Kayaking")
with st.expander("For Beginners"):
    beginner_tips = "- Always wear a PFD (life jacket)—it's mandatory on the Atlantic. - Paddle with a buddy or join a guided group. - Mornings are often calmer. - Stay close to shore; currents can be strong. - Wear sunscreen, hat, and quick-dry clothes."
    st.markdown(beginner_tips)
    if st.button("🔊 Read Beginner Tips", key="beg"):
        tts = gTTS(beginner_tips.replace("- ", ""), lang='en')
        a = BytesIO(); tts.write_to_fp(a); a.seek(0)
        st.audio(a, format="audio/mp3", autoplay=True)

with st.expander("For Experienced Paddlers"):
    exp_tips = "- Monitor swell and offshore winds—the Southeaster builds fast. - Know escape points along Sea Point. - Dress for immersion. - Avoid solo in high winds/waves. - Tell someone your plan."
    st.markdown(exp_tips)
    if st.button("🔊 Read Experienced Tips", key="exp"):
        tts = gTTS(exp_tips.replace("- ", ""), lang='en')
        a = BytesIO(); tts.write_to_fp(a); a.seek(0)
        st.audio(a, format="audio/mp3", autoplay=True)

st.header("🛶 Cape Kayak Adventure Guided Tours")
st.markdown("""
Since 1995 – based at Three Anchor Bay Beach. Morning, sunset & full moon tours. Spot seals, dolphins, whales (seasonal). No experience needed.

Book: [kayak.co.za](https://kayak.co.za/)
""")

# Footer
st.markdown("---")
st.markdown("""
**Music:** 181.fm Star 90's | **Voice:** gTTS | Built with ❤️ Streamlit  
Developer: Oni Charles – [LinkedIn](https://www.linkedin.com/in/charles-oni-b45a91253/)
""")
