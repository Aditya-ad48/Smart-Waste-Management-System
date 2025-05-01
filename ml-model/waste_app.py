import streamlit as st
import tensorflow as tf
import cv2
import numpy as np
from tensorflow.keras.preprocessing.image import img_to_array
import paho.mqtt.client as mqtt
import json
import threading
import time
import logging
import os
from datetime import datetime
from PIL import Image
import io

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger()

# Constants
MQTT_BROKER = "192.168.45.125"
MQTT_PORT = 1883
LEVEL_TOPIC = "smartbin/levels"
CLASS_TOPIC = "waste/classification"
DATA_FILE = "smartbin_data.json"
CAPTURE_DIR = "./captures"
MAX_CLASSIFICATIONS = 10
MAX_DISTANCE = 22  # cm (empty)
MIN_DISTANCE = 3  # cm (full)
COOLDOWN_PERIOD = 5  # seconds

# Initialize data file
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({
            "recyclable": 0,
            "non_recyclable": 0,
            "classifications": [],
            "last_update": time.time()
        }, f)

# Ensure capture directory exists
os.makedirs(CAPTURE_DIR, exist_ok=True)

# Utility Functions
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
                data = json.load(f)
                if "classifications" not in data:
                    data["classifications"] = []
                return data
        else:
            return {
                "recyclable": 0,
                "non_recyclable": 0,
                "classifications": [],
                "last_update": time.time()
            }
    except Exception as e:
        logger.error(f"Error loading data from file: {e}")
        return {
            "recyclable": 0,
            "non_recyclable": 0,
            "classifications": [],
            "last_update": time.time()
        }

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

def clear_history():
    try:
        current_data = load_data()
        current_data["classifications"] = []
        current_data["last_update"] = time.time()
        save_data(current_data)
        st.session_state.bin_data = current_data
        logger.info("Classification history cleared")
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        st.error(f"Failed to clear history: {e}")

# MQTT Setup
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info("Connected to MQTT broker")
        client.subscribe(LEVEL_TOPIC)
        client.subscribe(CLASS_TOPIC)
    else:
        logger.error(f"Failed to connect to MQTT, code: {rc}")

def on_message(client, userdata, msg, properties=None):
    try:
        payload = msg.payload.decode()
        logger.info(f"Received MQTT message on {msg.topic}: {payload}")
        data = json.loads(payload)
        current_data = load_data()

        if msg.topic == LEVEL_TOPIC:
            if "recyclable" in data:
                dist = data["recyclable"]
                perc = distance_to_percentage(dist)
                current_data["recyclable"] = perc
                logger.info(f"Recyclable fill level: {perc}%")
            if "non_recyclable" in data:
                dist = data["non_recyclable"]
                perc = distance_to_percentage(dist)
                current_data["non_recyclable"] = perc
                logger.info(f"Non-recyclable fill level: {perc}%")
        elif msg.topic == CLASS_TOPIC:
            classification = data.get("classification")
            confidence = data.get("confidence")
            timestamp = data.get("timestamp")
            if classification and confidence is not None and timestamp:
                current_data["classifications"].insert(0, {
                    "classification": classification,
                    "confidence": confidence,
                    "timestamp": timestamp
                })
                current_data["classifications"] = current_data["classifications"][:MAX_CLASSIFICATIONS]

        current_data["last_update"] = time.time()
        save_data(current_data)
        st.session_state.bin_data = current_data

    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}")

def mqtt_thread():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    while True:
        try:
            logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_forever()
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            time.sleep(5)

# Start MQTT thread
if "mqtt_thread_started" not in st.session_state:
    threading.Thread(target=mqtt_thread, daemon=True).start()
    st.session_state.mqtt_thread_started = True
    logger.info("MQTT thread started")

# Initialize MQTT client for publishing
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.loop_start()
    logger.info("MQTT client for publishing connected")
except Exception as e:
    logger.error(f"MQTT publishing client connection failed: {e}")
    st.error(f"Failed to connect to MQTT broker: {e}")
    st.stop()

# Load TensorFlow model
model_path = "/Users/aditya/Desktop/final_model.keras"
try:
    model = tf.keras.models.load_model(model_path)
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Error loading model: {e}")
    st.error(f"Error loading model: {e}")
    st.stop()

# Streamlit Config
st.set_page_config(
    page_title="Smart Waste Bin Dashboard",
    layout="wide",
    page_icon="🧠"
)

# Dark Theme Styling
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
    .classification-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }
    .classification-table th, .classification-table td {
        border: 1px solid #444;
        padding: 8px;
        text-align: left;
    }
    .classification-table th {
        background-color: #2E2E2E;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "bin_data" not in st.session_state:
    st.session_state.bin_data = load_data()
if "capture_count" not in st.session_state:
    st.session_state.capture_count = 0
if "last_sent_time" not in st.session_state:
    st.session_state.last_sent_time = 0

# Process Image
def process_image(image, model, capture_count):
    try:
        # Convert PIL Image to OpenCV format
        frame = np.array(image)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        height, width = frame.shape[:2]
        roi_x = int(width * 0.25)
        roi_y = int(height * 0.25)
        roi_w = int(width * 0.5)
        roi_h = int(height * 0.5)
        roi = frame[roi_y:roi_y + roi_h, roi_x:roi_x + roi_w]
        frame_copy = frame.copy()
        roi_copy = roi.copy()

        # Contour detection
        gray = cv2.cvtColor(roi_copy, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        _, otsu_thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        adaptive_thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                               cv2.THRESH_BINARY_INV, 11, 2)
        thresh = cv2.bitwise_or(otsu_thresh, adaptive_thresh)
        kernel = np.ones((5, 5), np.uint8)
        thresh = cv2.erode(thresh, kernel, iterations=1)
        thresh = cv2.dilate(thresh, kernel, iterations=2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best_contour = None
        max_area = 0
        logger.info(f"Capture {capture_count}: Contours found: {len(contours)}")

        # Save debug images
        cv2.imwrite(f"{CAPTURE_DIR}/gray_{capture_count:04d}.png", gray)
        cv2.imwrite(f"{CAPTURE_DIR}/thresh_{capture_count:04d}.png", thresh)
        contour_img = roi_copy.copy()
        cv2.drawContours(contour_img, contours, -1, (0, 255, 0), 2)
        cv2.imwrite(f"{CAPTURE_DIR}/contours_{capture_count:04d}.png", contour_img)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 10:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h
                if 0.3 < aspect_ratio < 3.0 and area > max_area:
                    max_area = area
                    best_contour = contour

        if best_contour is not None:
            x, y, w, h = cv2.boundingRect(best_contour)
            x += roi_x
            y += roi_y
            object_img = frame[y:y + h, x:x + w]
            logger.info(
                f"Capture {capture_count}: Detected object - Area: {max_area:.0f}, Aspect Ratio: {float(w) / h:.2f}")
        else:
            logger.info(f"Capture {capture_count}: No object detected. Using ROI.")
            object_img = roi_copy
            x, y = roi_x, roi_y

        # Prepare image for model
        object_img = cv2.cvtColor(object_img, cv2.COLOR_BGR2RGB)
        object_img = cv2.resize(object_img, (380, 380))
        object_img = img_to_array(object_img) / 255.0
        object_img = np.expand_dims(object_img, axis=0)
        logger.info(f"Capture {capture_count}: Input range: {object_img.min():.2f}, {object_img.max():.2f}")

        # Predict
        predictions = model.predict(object_img, verbose=0)
        raw_output = predictions[0][0]
        logger.info(f"Capture {capture_count}: Raw prediction: {raw_output:.4f}")

        class_labels = ["non-recyclable", "recyclable"]
        if raw_output > 0.5:
            predicted_label = class_labels[1]
            confidence = raw_output
        else:
            predicted_label = class_labels[0]
            confidence = 1 - raw_output

        # Publish to MQTT if cooldown allows
        current_time = time.time()
        if current_time - st.session_state.last_sent_time > COOLDOWN_PERIOD:
            payload = json.dumps({
                "classification": predicted_label,
                "confidence": float(confidence),
                "timestamp": current_time
            })
            mqtt_client.publish(CLASS_TOPIC, payload)
            logger.info(f"Capture {capture_count}: [MQTT] Sent: {payload}")
            st.session_state.last_sent_time = current_time

        # Save annotated image
        cv2.rectangle(frame_copy, (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h), (0, 255, 255), 2)
        if best_contour is not None:
            cv2.rectangle(frame_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = f"{predicted_label} ({confidence:.4f})"
        cv2.putText(frame_copy, text, (x, max(20, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        output_path = os.path.join(CAPTURE_DIR, f"capture_{capture_count:04d}.png")
        cv2.imwrite(output_path, frame_copy)
        logger.info(f"Capture {capture_count}: Saved: {output_path}")

        # Convert back to PIL for display
        frame_copy = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2RGB)
        return frame_copy, predicted_label, confidence

    except Exception as e:
        logger.error(f"Capture {capture_count}: Error during prediction: {e}")
        return frame, None, None

# UI
st.title("🧠 Smart Waste Bin Dashboard")
st.markdown("Capture waste images for classification and monitor bin levels in real-time.")

# Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📷 Waste Classification")
    st.markdown("Capture an image to classify waste as recyclable ♻️ or non-recyclable 🗑️.")
    image = st.camera_input("Take a picture", help="Place the object in the center and click to capture.")

    if image:
        st.session_state.capture_count += 1
        capture_count = st.session_state.capture_count
        logger.info(f"Capturing image {capture_count}")

        # Process the image
        img = Image.open(image)
        annotated_frame, predicted_label, confidence = process_image(img, model, capture_count)

        # Display result
        st.image(annotated_frame, caption="Processed Image", use_container_width=True)
        if predicted_label:
            st.success(f"Classification: {predicted_label.capitalize()} (Confidence: {confidence:.4f})")
        else:
            st.error("Error processing image.")

with col2:
    st.header("📊 Bin Status")
    bin_data = st.session_state.bin_data
    recyclable_level = bin_data.get("recyclable", 0)
    non_recyclable_level = bin_data.get("non_recyclable", 0)

    st.markdown("### ♻️ Recyclable Bin")
    st.progress(recyclable_level / 100)
    st.metric("Fill Level", f"{recyclable_level}%")

    st.markdown("### 🗑️ Non-Recyclable Bin")
    st.progress(non_recyclable_level / 100)
    st.metric("Fill Level", f"{non_recyclable_level}%")

# Classification History
st.header("📜 Classification History")
col_history1, col_history2 = st.columns([3, 1])
with col_history1:
    if st.button("Clear History", use_container_width=True):
        clear_history()
        st.rerun()
with col_history2:
    pass  # Empty column for layout balance

classifications = bin_data.get("classifications", [])
if classifications:
    table_html = '<table class="classification-table"><tr><th>Time</th><th>Classification</th><th>Confidence</th></tr>'
    for entry in classifications:
        timestamp = datetime.fromtimestamp(entry["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        classification = entry["classification"].capitalize()
        confidence = f"{entry['confidence']:.4f}"
        table_html += f"<tr><td>{timestamp}</td><td>{classification}</td><td>{confidence}</td></tr>"
    table_html += '</table>'
    st.markdown(table_html, unsafe_allow_html=True)
else:
    st.markdown("No classifications recorded yet.")

# Last Update
last_update = bin_data.get("last_update", time.time())
elapsed = int(time.time() - last_update)
st.markdown(f"🕒 Last updated: `{elapsed} seconds ago`")

# Debug Information
if st.checkbox("Show Debug Info"):
    st.markdown(f"""
    <div class="debug-info">
    Raw bin data: {json.dumps(bin_data)}<br>
    Data file: {os.path.abspath(DATA_FILE)}<br>
    Capture count: {st.session_state.capture_count}<br>
    </div>
    """, unsafe_allow_html=True)

# Refresh Controls
col1, col2 = st.columns([3, 1])
with col1:
    refresh_interval = st.slider("Auto-refresh interval (seconds)", min_value=1, max_value=30, value=5)
    st.info(f"Dashboard will auto-refresh every {refresh_interval} seconds")
with col2:
    if st.button("Refresh Now", use_container_width=True):
        st.rerun()

# Auto Refresh
time.sleep(refresh_interval)
st.rerun()

# Cleanup
mqtt_client.loop_stop()
mqtt_client.disconnect()