import streamlit as st
import paho.mqtt.client as mqtt
import json
import threading
import time
import logging
import os

# ---- Logging Setup ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger()

# ---- Constants ----
MAX_DISTANCE = 22  # cm (empty)
MIN_DISTANCE = 3  # cm (full)

# ---- Data File Path ----
# Using a file to persist data between Streamlit refreshes
DATA_FILE = "smartbin_data.json"

# Initialize data file if it doesn't exist
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({
            "recyclable": 0,
            "non_recyclable": 0,
            "last_update": time.time()
        }, f)


# ---- Utility Functions ----
def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Error saving data to file: {e}")


def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        else:
            return {
                "recyclable": 0,
                "non_recyclable": 0,
                "last_update": time.time()
            }
    except Exception as e:
        logger.error(f"Error loading data from file: {e}")
        return {
            "recyclable": 0,
            "non_recyclable": 0,
            "last_update": time.time()
        }


# ---- Streamlit Config ----
st.set_page_config(
    page_title="Smart Waste Bin Dashboard",
    layout="wide",
    page_icon="🧠"
)

# ---- Dark Theme Styling ----
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: white;
    }
    .debug-info {
        font-size: 12px;
        color: #888;
        margin-top: 40px;
        padding: 10px;
        background-color: #1E1E1E;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)


# ---- Utility: Distance to Percentage ----
def distance_to_percentage(distance):
    try:
        distance = float(distance)
        if distance >= 999:
            return 0
        distance = min(max(distance, MIN_DISTANCE), MAX_DISTANCE)
        percentage = int(((MAX_DISTANCE - distance) / (MAX_DISTANCE - MIN_DISTANCE)) * 100)
        return max(0, min(100, percentage))
    except:
        return 0


# ---- MQTT Callbacks ----
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info("Connected to MQTT broker")
        client.subscribe("smartbin/levels")
    else:
        logger.error(f"Failed to connect to MQTT, code: {rc}")


def on_message(client, userdata, msg, properties=None):
    try:
        payload = msg.payload.decode()
        logger.info(f"Received MQTT message: {payload}")
        data = json.loads(payload)

        # Load current data
        current_data = load_data()

        # Update with new values
        if "recyclable" in data:
            dist = data["recyclable"]
            logger.info(f"Raw recyclable distance: {dist}cm")
            perc = distance_to_percentage(dist)
            logger.info(f"Calculated recyclable fill level: {perc}%")
            current_data["recyclable"] = perc

        if "non_recyclable" in data:
            dist = data["non_recyclable"]
            logger.info(f"Raw non_recyclable distance: {dist}cm")
            perc = distance_to_percentage(dist)
            logger.info(f"Calculated non_recyclable fill level: {perc}%")
            current_data["non_recyclable"] = perc

        current_data["last_update"] = time.time()
        logger.info(f"Updated data: {current_data}")

        # Save the updated data
        save_data(current_data)

    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}")


# ---- MQTT Thread ----
def mqtt_thread():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            logger.info("Attempting to connect to MQTT broker at 192.168.174.125:1883")
            client.connect("192.168.112.125", 1883, keepalive=60)
            client.loop_forever()
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            time.sleep(5)


# ---- Start MQTT Thread Once ----
if "mqtt_thread_started" not in st.session_state:
    threading.Thread(target=mqtt_thread, daemon=True).start()
    st.session_state.mqtt_thread_started = True
    logger.info("MQTT thread started")

# ---- UI ----
st.title("🧠 Smart Waste Bin Dashboard")
st.markdown("Real-time fill level tracking for Recyclable ♻️ and Non-Recyclable 🗑️ bins")

# ---- Get Latest Data ----
bin_data = load_data()
recyclable_level = bin_data.get("recyclable", 0)
non_recyclable_level = bin_data.get("non_recyclable", 0)
last_update = bin_data.get("last_update", time.time())

# ---- Layout ----
col1, col2 = st.columns(2)

with col1:
    st.markdown("### ♻️ Recyclable Bin")
    st.progress(recyclable_level / 100)
    st.metric("Fill Level", f"{recyclable_level}%")

with col2:
    st.markdown("### 🗑️ Non-Recyclable Bin")
    st.progress(non_recyclable_level / 100)
    st.metric("Fill Level", f"{non_recyclable_level}%")

# ---- Last Update ----
elapsed = int(time.time() - last_update)
st.markdown(f"🕒 Last updated: `{elapsed} seconds ago`")

# ---- Debug Information ----
if st.checkbox("Show Debug Info"):
    st.markdown(f"""
    <div class="debug-info">
    Raw bin data: {json.dumps(bin_data)}<br>
    Data file: {os.path.abspath(DATA_FILE)}<br>
    </div>
    """, unsafe_allow_html=True)

# ---- Refresh Controls ----
col1, col2 = st.columns([3, 1])
with col1:
    # Auto-refresh timer
    refresh_interval = st.slider("Auto-refresh interval (seconds)", min_value=1, max_value=30, value=5)
    st.info(f"Dashboard will auto-refresh every {refresh_interval} seconds")

with col2:
    if st.button("Refresh Now", use_container_width=True):
        st.rerun()

# ---- Auto Refresh ----
time.sleep(refresh_interval)
st.rerun()