import streamlit as st
import requests
from datetime import datetime
from gtts import gTTS
from io import BytesIO

st.set_page_config(page_title="Three Anchor Bay Kayak Radio", layout="wide")

# YouTube Video ID from your link
YOUTUBE_VIDEO_ID = "_wYENnYaboM"

# Hidden YouTube embed HTML with autoplay and loop
youtube_embed = f"""
<iframe id="ytplayer" type="text/html" width="0" height="0"
  src="https://www.youtube.com/embed/{YOUTUBE_VIDEO_ID}?autoplay=1&loop=1&playlist={YOUTUBE_VIDEO_ID}&controls=0&showinfo=0&rel=0"
  frameborder="0" allowfullscreen style="display:none"></iframe>
"""

# Session state for mute toggle
if 'muted' not in st.session_state:
    st.session_state.muted = False  # Start with sound ON

# Header with Radio Toggle Button
col1, col2 = st.columns([1, 6])
with col1:
    if st.session_state.muted:
        if st.button("🔇 Radio Off", key="toggle"):
            st.session_state.muted = False
            st.rerun()
        status_emoji = "🔇"
        status_text = "Radio Off"
    else:
        if st.button("🔊 Radio On", key="toggle"):
            st.session_state.muted = True
            st.rerun()
        status_emoji = "🔊"
        status_text = "Radio On"

with col2:
    st.title(f"🌊 Three Anchor Bay Kayak Radio  {status_emoji}")

st.markdown("""
Welcome to your AI-powered kayaking companion radio!  
90s hits play in the background while you check conditions and safety tips for Three Anchor Bay, Cape Town.  
Use the button above to mute or unmute the music anytime.
""")

# Inject hidden YouTube player + JavaScript to control volume
st.components.v1.html(
    f"""
    {youtube_embed if not st.session_state.muted else ''}
    <script>
        function toggleMute(muted) {{
            const iframe = document.getElementById('ytplayer');
            if (iframe) {{
                iframe.contentWindow.postMessage(
                    JSON.stringify({{event: 'command', func: 'setVolume', args: [muted ? 0 : 100]}}),
                    '*'
                );
            }}
        }}
        // Initial mute state
        toggleMute({str(st.session_state.muted).lower()});
    </script>
    """,
    height=0
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
    st.write(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Voice narration
    narration_text = f"Current kayaking conditions in Three Anchor Bay: Temperature {temp} degrees Celsius, feels like {feels_like}. Wind speed {wind_speed} kilometers per hour from {wind_dir} degrees. Wave height {wave_height} meters. {assessment}"

    if st.button("🔊 Speak Updates"):
        with st.spinner("Generating voice..."):
            tts = gTTS(text=narration_text, lang='en')
            audio_bytes = BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)

except Exception:
    st.error("Weather data temporarily unavailable. Check back soon!")

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

# Footer with source credit
st.markdown("---")
st.markdown("""
**Music Source:** 90s Hits Live Radio by *Best of Nostalgia* on YouTube  
Built with ❤️ using Streamlit | Voice powered by gTTS
""")
