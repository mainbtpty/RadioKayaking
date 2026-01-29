import streamlit as st
import requests
from datetime import datetime, timedelta
from gtts import gTTS
from io import BytesIO

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

st.markdown("Non-stop 90s hits + real-time + forecast weather for safe kayaking in Three Anchor Bay!")

# Background radio
if not st.session_state.muted:
    st.audio(RADIO_STREAM_URL, format="audio/mp3", autoplay=True)
    st.markdown("<style>audio { display: none; }</style>", unsafe_allow_html=True)

# Fetch / update weather
now = datetime.now()
if now - st.session_state.last_weather_update >= timedelta(minutes=10):
    try:
        current_url = "https://api.open-meteo.com/v1/forecast?latitude=-33.9083&longitude=18.3958&current=temperature_2m,apparent_temperature,wind_speed_10m,wind_direction_10m,visibility,cloud_cover_low,wave_height,swell_wave_height,weather_code&timezone=auto"
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
        st.metric("Wave Height", f"{data.get('wave_height', 'N/A')} m", f"Swell: {data.get('swell_wave_height', 'N/A')} m")
    with col4:
        st.metric("Visibility", f"{data.get('visibility', 'N/A')} m")
        vis = data.get('visibility', 10000)
        if vis < 1000:
            st.error("Heavy Fog – Very Low Visibility! Do not launch.")
        elif vis < 5000:
            st.warning("Foggy – Reduced Visibility. Caution advised.")
        else:
            st.success("Good Visibility")

    # Suitability (wind + wave + fog/visibility)
    wind_val = data.get('wind_speed_10m', 0)
    wave_val = data.get('wave_height', 0)
    vis_val = data.get('visibility', 10000)
    low_cloud = data.get('cloud_cover_low', 0)
    if wind_val > 25 or wave_val > 1.5 or vis_val < 1000 or low_cloud > 80:
        assessment = "Poor – high wind, waves, fog, or low visibility. No go today."
        color = "🔴"
    elif wind_val > 15 or wave_val > 1 or vis_val < 5000 or low_cloud > 50:
        assessment = "Moderate – caution for wind, waves or fog. Experienced only."
        color = "🟡"
    else:
        assessment = "Good – calm, clear, and ideal for paddling!"
        color = "🟢"

    st.subheader("Kayaking Suitability (incl. Waves & Fog/Visibility)")
    st.markdown(f"**{color} {assessment}**")
    st.write(f"Updated: {datetime.fromisoformat(data['time']).strftime('%Y-%m-%d %H:%M')} SAST")

    # DJ forecast text
    forecast_text = f"Hey paddlers! Cape Kayak Adventure Radio DJ here with the latest for Three Anchor Bay: Temp {data.get('temperature_2m')}°C (feels {data.get('apparent_temperature')}°C), wind {data.get('wind_speed_10m')} km/h from {data.get('wind_direction_10m')}°. Waves {data.get('wave_height')} m. Visibility {data.get('visibility')} m – watch for fog if low! {assessment.lower()} Stay safe and keep vibing!"

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
if 'daily' in st.session_state.weather_data and len(st.session_state.weather_data['daily'].get('time', [])) >= 3:
    daily_times = st.session_state.weather_data['daily']['time']
    daily_codes = st.session_state.weather_data['daily']['weather_code']
    daily_max_temp = st.session_state.weather_data['daily']['temperature_2m_max']
    daily_min_temp = st.session_state.weather_data['daily']['temperature_2m_min']
    daily_max_wind = st.session_state.weather_data['daily']['wind_speed_10m_max']
    daily_precip_prob = st.session_state.weather_data['daily']['precipitation_probability_max']

    for day_offset, label in [(1, "Tomorrow"), (2, "Day After")]:
        with st.expander(f"{label} – {daily_times[day_offset]}"):
            colA, colB, colC = st.columns(3)
            with colA:
                st.metric("Max / Min Temp", f"{daily_max_temp[day_offset]}°C / {daily_min_temp[day_offset]}°C")
            with colB:
                st.metric("Max Wind", f"{daily_max_wind[day_offset]} km/h")
            with colC:
                st.metric("Precip Probability", f"{daily_precip_prob[day_offset]}%")
            st.info(f"Weather code: {daily_codes[day_offset]} (check WMO codes for details)")
            st.caption("Fog/visibility and waves not available in daily forecast – check current/hourly closer to the date.")
else:
    st.info("Daily forecast loading...")

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

# Guided Tours (full from your document)
st.header("🛶 Cape Kayak Adventure Guided Tours")
st.markdown("""
Experience the best views of Cape Town and get up close and personal with ocean life during our guided kayak trips.

## Explore Table Mountain National Marine Park

Cape Kayak Adventures has been operating fun and safe kayak tours since 1995 on the Atlantic Seaboard. We are based in the heart of the Marine Protected Area of the Table Mountain National Park in Cape Town, South Africa. We offer guided kayak adventures in the morning, at sunset and under the glorious full moon, weather permitting. Come and explore the rich diversity of marine life, the kelp forests and a refreshing perspective of Cape Town and Table Mountain. Our experienced and knowledgeable guides will teach you the basics of kayaking and lead you on a safe and enjoyable tour of the Cape Town coastline. We love sharing our passion with our guests!

Top rated on Trip Advisor

## Journey into nature

On our kayak tours, you’ll embark on a journey through Cape Town’s iconic landmarks, paddling past Table Mountain, Robben Island, and the majestic Twelve Apostles. As you explore, you’ll encounter well-known shipwrecks and the chance to spot marine mammals like Heaviside’s dolphins, seals, whales, and even the occasional sunfish. With every stroke, the ocean reveals its secrets, offering unforgettable surprises and a truly immersive experience.

## Types of tours

### Morning tours

Although there are no guarantees (they remain wild and free), we are often graced with marine wildlife sightings on these tours.

### Sunset tours

Paddle into the sunset and enjoy picturesque views and a breathtaking sunset from the water.

### Moonrise tours

Enjoy the tranquillity of the golden hour while we watch the moon rise over Table Bay and observe the glowing city lights.

### Guide training

Got dreams of becoming a kayak guide? We can help you make those dreams come true. Reach out to us via our contact form.

## Our clients say it best

## Got questions?

Feel free to explore our FAQ page for commonly asked questions or reach out to us directly using the form below, we’d love to assist you.

## Meeting details

#### Three Anchor Bay Beach

We meet at the Beach Shed.

 Location Map

 Call us

Book now: [kayak.co.za](https://kayak.co.za/)
""")

# Footer
st.markdown("---")
st.markdown("""
**Music:** 181.fm Star 90's | **Voice:** gTTS | Built with ❤️ Streamlit  
Developer: Oni Charles – LinkedIn: [linkedin.com/in/charles-oni-b45a91253](https://www.linkedin.com/in/charles-oni-b45a91253/)  
Data from Open-Meteo – real-time, but model runs may have slight delay.
""")
