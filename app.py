import streamlit as st
import requests
from datetime import datetime
from gtts import gTTS
from io import BytesIO

st.set_page_config(page_title="Three Anchor Bay Kayak Radio", layout="wide")

# Header
st.title("🌊 Three Anchor Bay Kayak Radio")
st.markdown("""
Welcome to your AI-powered kayaking companion! Enjoy non-stop 90s hits while getting real-time weather updates and safety tips for Three Anchor Bay, Cape Town.
Perfect for planning relaxed paddles along the Atlantic seaboard.
""")

# Live Music Stream
st.header("🎶 Live 90s Hits Radio (24/7)")
embed_code = """
<iframe width="100%" height="400" src="https://www.youtube.com/embed/_wYENnYaboM?autoplay=1&mute=0&loop=1&playlist=_wYENnYaboM" 
frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
allowfullscreen></iframe>
"""
st.components.v1.html(embed_code, height=400)

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

    # Simple AI-like safety assessment
    if wind_speed > 25 or wave_height > 1.5:
        assessment = "Poor conditions – Strong winds or high waves. Avoid paddling, especially for beginners."
        color = "🔴"
    elif wind_speed > 15 or wave_height > 1:
        assessment = "Moderate conditions – Caution advised. Suitable for experienced paddlers only."
        color = "🟡"
    else:
        assessment = "Good conditions – Calm and ideal for all levels!"
        color = "🟢"

    st.subheader("Kayaking Suitability")
    st.markdown(f"**{color} {assessment}**")
    st.write(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} (refreshes on reload)")

    # Voice narration for weather assessment
    narration_text = f"Current kayaking conditions in Three Anchor Bay: Temperature {temp} degrees Celsius, feels like {feels_like}. Wind speed {wind_speed} kilometers per hour from {wind_dir} degrees. Wave height {wave_height} meters. {assessment}"

    if st.button("🔊 Speak Updates"):
        with st.spinner("Generating voice..."):
            tts = gTTS(text=narration_text, lang='en')
            audio_bytes = BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)

except Exception as e:
    st.error("Weather data temporarily unavailable. Check back soon!")

# Safety Tips with optional voice
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

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit | Music: Best of Nostalgia 90s Hits Live Stream | Voice powered by gTTS")
