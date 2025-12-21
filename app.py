import streamlit as st
import requests
from datetime import datetime, timedelta
from gtts import gTTS
from io import BytesIO

st.set_page_config(page_title="Cape Kayak Adventure Radio FM", layout="wide")

# Direct 90s radio stream URL (verified active as of Dec 2025 – if issues, try alternative like 'https://listen.181fm.com/181-90sdance_128k.mp3')
RADIO_STREAM_URL = "https://listen.181fm.com/181-star90s_128k.mp3"

# Session state
if 'muted' not in st.session_state:
    st.session_state.muted = True  # Start muted
if 'last_jingle' not in st.session_state:
    st.session_state.last_jingle = datetime.now() - timedelta(minutes=3)  # Force first jingle on unmute

# Header
col1, col2 = st.columns([1, 6])
with col1:
    if st.session_state.muted:
        if st.button("🔇 Sound Off", key="toggle"):
            st.session_state.muted = False
            st.session_state.last_jingle = datetime.now() - timedelta(minutes=3)  # Ready for jingle
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
Click the button to turn on sound (one click required). The station jingle plays on start and every few minutes.
""")

# Background music (hidden)
if not st.session_state.muted:
    st.audio(RADIO_STREAM_URL, format="audio/mp3", autoplay=True, start_time=0)
    st.markdown("<style>audio { display: none; }</style>", unsafe_allow_html=True)

    # Jingle logic: Play on unmute + every ~3 minutes
    now = datetime.now()
    if now - st.session_state.last_jingle >= timedelta(minutes=3):
        jingle_text = "You're listening to Cape Kayak Adventure Radio FM in Three Anchor Bay – your soundtrack for Atlantic paddling adventures!"
        with st.spinner("Playing station jingle..."):
            tts = gTTS(text=jingle_text, lang='en')
            jingle_audio = BytesIO()
            tts.write_to_fp(jingle_audio)
            jingle_audio.seek(0)
            st.audio(jingle_audio, format="audio/mp3", autoplay=True)
        st.session_state.last_jingle = now

# Weather Section
st.header("🌤️ Current Kayaking Conditions in Three Anchor Bay")
lat, lon = -33.9083, 18.3958

forecast_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,wind_speed_10m,wind_direction_10m"
marine_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,wave_period,wind_wave_height,swell_wave_height"

try:
    forecast_response = requests.get(forecast_url)
    forecast_response.raise_for_status()  # Raise error if request fails
    forecast_data = forecast_response.json()["current"]

    marine_response = requests.get(marine_url)
    marine_response.raise_for_status()
    marine_data = marine_response.json()["current"]

    temp = forecast_data.get("temperature_2m", "N/A")
    feels_like = forecast_data.get("apparent_temperature", "N/A")
    wind_speed = forecast_data.get("wind_speed_10m", "N/A")
    wind_dir = forecast_data.get("wind_direction_10m", "N/A")
    wave_height = marine_data.get("wave_height", 1.0) if not isinstance(marine_data.get("wave_height"), list) else marine_data.get("wave_height", [1.0])[0]
    swell_height = marine_data.get("swell_wave_height", 0.5) if not isinstance(marine_data.get("swell_wave_height"), list) else marine_data.get("swell_wave_height", [0.5])[0]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Temperature", f"{temp}°C" if temp != "N/A" else "N/A", f"Feels like {feels_like}°C")
    with col2:
        st.metric("Wind Speed", f"{wind_speed} km/h" if wind_speed != "N/A" else "N/A", f"Direction: {wind_dir}°")
    with col3:
        st.metric("Wave Height", f"{wave_height} m", f"Swell: {swell_height} m")

    if wind_speed == "N/A" or (isinstance(wind_speed, (int, float)) and wind_speed > 25) or wave_height > 1.5:
        assessment = "Poor conditions – strong winds or high waves. Avoid paddling today."
        color = "🔴"
    elif (isinstance(wind_speed, (int, float)) and wind_speed > 15) or wave_height > 1:
        assessment = "Moderate conditions – caution advised. Experienced paddlers only."
        color = "🟡"
    else:
        assessment = "Good conditions – calm and perfect for kayaking!"
        color = "🟢"

    st.subheader("Kayaking Suitability")
    st.markdown(f"**{color} {assessment}**")
    st.write(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    forecast_text = f"Weather update for Three Anchor Bay kayaking: Temperature {temp} degrees, feels like {feels_like}. Wind {wind_speed} kilometers per hour from {wind_dir} degrees. Waves {wave_height} meters. {assessment.replace(' – ', '. ')} Paddle safe!"

    if st.button("🔊 Speak Full Weather Forecast"):
        with st.spinner("Speaking forecast..."):
            tts = gTTS(text=forecast_text, lang='en')
            audio_bytes = BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)

except Exception as e:
    st.warning(f"Weather API issue: {str(e)} – Refresh to retry or check connection.")
    # Fallback metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Temperature", "N/A")
    with col2:
        st.metric("Wind Speed", "N/A")
    with col3:
        st.metric("Wave Height", "N/A")
    st.subheader("Kayaking Suitability: Data unavailable – try again soon.")

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
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)

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
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)

st.markdown("Sources: Local guides like Kaskazi Kayaks & general ocean safety best practices.")

# Guided Tours Section
st.header("🛶 Cape Kayak Adventure Guided Tours")
st.markdown("""
The original and best since 1995 – right here in Three Anchor Bay!

**Cape Kayak Adventures** offers incredible guided trips in the Table Mountain National Marine Protected Area. Spot seals, dolphins, whales (in season), and paddle with epic views.

- No experience required
- Morning, sunset & full moon tours
- Expert guides for safety & fun

Book now: [kayak.co.za](https://kayak.co.za/)
""")

# Footer
st.markdown("---")
st.markdown("""
**Music:** 181.fm Star 90's | Voice: gTTS | Built with ❤️ Streamlit  
Developer : Oni Charles linkedIn https://www.linkedin.com/in/charles-oni-b45a91253/
Note: If radio doesn't play, check browser permissions or try a different browser. Stream is active.
""")
