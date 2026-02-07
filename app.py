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
Welcome to **Cape Kayak Adventure Radio FM** – non-stop 90s hits for kayakers in Three Anchor Bay, Cape Town!  
Weather updates every 10 min • DJ forecast every 3 min (auto-plays over music with volume ducking).
""")

# Background radio
if not st.session_state.muted:
    st.audio(RADIO_STREAM_URL, format="audio/mp3", autoplay=True)
    st.markdown("<style>audio { display: none; }</style>", unsafe_allow_html=True)

# Weather update every 10 minutes
now = datetime.now()
if now - st.session_state.last_weather_update >= timedelta(minutes=10):
    try:
        # Current conditions (including visibility)
        forecast_data = requests.get(
            "https://api.open-meteo.com/v1/forecast?latitude=-33.9083&longitude=18.3958&current=temperature_2m,apparent_temperature,wind_speed_10m,wind_direction_10m,visibility",
            timeout=10
        ).json()["current"]

        # Marine data (wave & swell) - use slightly offshore coords from document for better data
        marine_data = requests.get(
            "https://marine-api.open-meteo.com/v1/marine?latitude=-33.875&longitude=18.291672&current=wave_height,swell_wave_height",
            timeout=10
        ).json()["current"]

        # Hourly forecast (from forecast API)
        hourly_data = requests.get(
            "https://api.open-meteo.com/v1/forecast?latitude=-33.9083&longitude=18.3958&hourly=temperature_2m,apparent_temperature,wind_speed_10m,wind_direction_10m,visibility&timezone=auto",
            timeout=10
        ).json()["hourly"]

        # Hourly marine (wave height) - use offshore coords
        hourly_marine = requests.get(
            "https://marine-api.open-meteo.com/v1/marine?latitude=-33.875&longitude=18.291672&hourly=wave_height,swell_wave_height&timezone=auto",
            timeout=10
        ).json()["hourly"]

        # Daily forecast
        daily_data = requests.get(
            "https://api.open-meteo.com/v1/forecast?latitude=-33.9083&longitude=18.3958&daily=weather_code,temperature_2m_max,temperature_2m_min,wind_speed_10m_max,precipitation_probability_max&timezone=auto&forecast_days=3",
            timeout=10
        ).json()["daily"]

        st.session_state.temp = forecast_data.get("temperature_2m", "N/A")
        st.session_state.feels_like = forecast_data.get("apparent_temperature", "N/A")
        st.session_state.wind_speed = forecast_data.get("wind_speed_10m", "N/A")
        st.session_state.wind_dir = forecast_data.get("wind_direction_10m", "N/A")
        st.session_state.visibility = forecast_data.get("visibility", "N/A")
        st.session_state.wave_height = marine_data.get("wave_height", [1.0])[0] if isinstance(marine_data.get("wave_height"), list) else marine_data.get("wave_height", 1.0)
        st.session_state.swell_height = marine_data.get("swell_wave_height", [0.5])[0] if isinstance(marine_data.get("swell_wave_height"), list) else marine_data.get("swell_wave_height", 0.5)
        st.session_state.hourly = hourly_data
        st.session_state.hourly_marine = hourly_marine
        st.session_state.daily = daily_data

        wind_val = st.session_state.wind_speed if isinstance(st.session_state.wind_speed, (int, float)) else 0
        wave_val = st.session_state.wave_height
        vis_val = st.session_state.visibility if isinstance(st.session_state.visibility, (int, float)) else 10000

        if wind_val > 25 or wave_val > 1.5 or vis_val < 1000:
            st.session_state.assessment = "Poor conditions – strong winds, high waves, or low visibility/fog. Avoid paddling today."
            st.session_state.color = "🔴"
        elif wind_val > 15 or wave_val > 1 or vis_val < 5000:
            st.session_state.assessment = "Moderate conditions – caution advised for wind, waves or fog. Experienced paddlers only."
            st.session_state.color = "🟡"
        else:
            st.session_state.assessment = "Good conditions – calm and perfect for kayaking!"
            st.session_state.color = "🟢"

        st.session_state.last_weather_update = now

    except Exception:
        if 'temp' not in st.session_state:
            st.session_state.temp = "N/A"
            st.session_state.assessment = "Data unavailable"
            st.session_state.color = "⚪"

# Display current weather
st.header("🌤️ Current Kayaking Conditions in Three Anchor Bay")
if 'temp' in st.session_state:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Temperature", f"{st.session_state.temp}°C", f"Feels {st.session_state.feels_like}°C")
    with col2:
        st.metric("Wind Speed", f"{st.session_state.wind_speed} km/h", f"Dir: {st.session_state.wind_dir}°")
    with col3:
        st.metric("Wave Height", f"{st.session_state.wave_height:.1f} m", f"Swell: {st.session_state.swell_height:.1f} m")
    with col4:
        vis_val = st.session_state.visibility
        vis_display = f"{vis_val} m" if isinstance(vis_val, (int, float)) else "N/A"
        st.metric("Visibility", vis_display)
        if isinstance(vis_val, (int, float)):
            if vis_val < 1000:
                st.error("Heavy Fog – Very Low Visibility! Do not launch.")
            elif vis_val < 5000:
                st.warning("Foggy – Reduced Visibility. Caution advised.")
            else:
                st.success("Good Visibility")

    st.subheader("Kayaking Suitability (incl. Waves & Fog/Visibility)")
    st.markdown(f"**{st.session_state.color} {st.session_state.assessment}**")
    st.write(f"Updated: {st.session_state.last_weather_update.strftime('%Y-%m-%d %H:%M')}")

    # DJ forecast text (includes visibility)
    forecast_text = f"Hey paddlers, this is your Cape Kayak Adventure Radio DJ with the latest from Three Anchor Bay! We're sitting at {st.session_state.temp} degrees, feeling like {st.session_state.feels_like}. Winds at {st.session_state.wind_speed} km/h from {st.session_state.wind_dir} degrees. Waves running {st.session_state.wave_height:.1f} meters. Visibility {vis_display} – watch for fog if low! Bottom line: {st.session_state.assessment.lower()} Keep those paddles ready and enjoy the 90s vibes!"

    # Auto forecast if due
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
                const origVol = music.volume || 1.0;
                speech.onplay = () => music.volume = 0.3;
                speech.onended = () => music.volume = origVol;
            }
            </script>
            """,
            height=0
        )

        st.session_state.last_forecast = now
        if st.session_state.first_unmute:
            st.session_state.first_unmute = False

    # Manual button
    if st.button("🔊 Speak Forecast (DJ Style)"):
        tts = gTTS(text=forecast_text, lang='en')
        audio = BytesIO()
        tts.write_to_fp(audio)
        audio.seek(0)
        st.audio(audio, format="audio/mp3", autoplay=True)

# Hourly Forecast (next 24 hours)
st.header("⏰ Hourly Forecast – Next 24 Hours")
if 'hourly' in st.session_state:
    hourly = st.session_state.hourly
    hourly_marine = st.session_state.hourly_marine
    times = hourly['time'][:24]
    temps = hourly['temperature_2m'][:24]
    feels = hourly['apparent_temperature'][:24]
    winds = hourly['wind_speed_10m'][:24]
    dirs = hourly['wind_direction_10m'][:24]
    viss = hourly['visibility'][:24]
    waves = hourly_marine['wave_height'][:24]
    swells = hourly_marine['swell_wave_height'][:24]

    # Display as table
    st.markdown("**Time | Temp (°C) | Feels (°C) | Wind (km/h) | Dir (°) | Vis (m) | Wave (m) | Swell (m)**")
    for i in range(len(times)):
        time_str = datetime.fromisoformat(times[i]).strftime('%H:%M')
        temp_str = f"{temps[i]}"
        feels_str = f"{feels[i]}"
        wind_str = f"{winds[i]}"
        dir_str = f"{dirs[i]}"
        vis_str = f"{viss[i]}" if viss[i] is not None else "N/A"
        wave_str = f"{waves[i]:.1f}" if waves[i] is not None else "N/A"
        swell_str = f"{swells[i]:.1f}" if swells[i] is not None else "N/A"
        st.markdown(f"{time_str} | {temp_str} | {feels_str} | {wind_str} | {dir_str} | {vis_str} | {wave_str} | {swell_str}")

else:
    st.info("Hourly data loading...")

# Daily Forecast – Tomorrow & Day After
st.header("📅 Forecast – Tomorrow & Day After")
if 'daily' in st.session_state:
    daily_times = st.session_state.daily['time'][1:3]  # tomorrow and day after
    daily_codes = st.session_state.daily['weather_code'][1:3]
    daily_max_temp = st.session_state.daily['temperature_2m_max'][1:3]
    daily_min_temp = st.session_state.daily['temperature_2m_min'][1:3]
    daily_max_wind = st.session_state.daily['wind_speed_10m_max'][1:3]
    daily_precip = st.session_state.daily['precipitation_probability_max'][1:3]

    for i, label in enumerate(["Tomorrow", "Day After"]):
        with st.expander(label):
            st.metric("Max / Min Temp", f"{daily_max_temp[i]}°C / {daily_min_temp[i]}°C")
            st.metric("Max Wind", f"{daily_max_wind[i]} km/h")
            st.metric("Precip Probability", f"{daily_precip[i]}%")
            st.caption("Weather code: {daily_codes[i]} (check WMO codes for details)")
            st.caption("Note: Wave & visibility not available in daily forecast – check hourly.")

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
""")
``` st.markdown
