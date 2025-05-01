import streamlit as st
import numpy as np
import logging
import os
import json
import time
from datetime import datetime

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DATA_FILE = "smartbin_data.json"
CAPTURE_DIR = "./captures"

# Ensure directories exist
os.makedirs(CAPTURE_DIR, exist_ok=True)

# Initialize data file if it doesn't exist
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({
            "recyclable": 0,
            "non_recyclable": 0,
            "classifications": [],
            "last_update": time.time()
        }, f)

# Streamlit Config
st.set_page_config(
    page_title="Smart Waste Bin Dashboard",
    layout="wide",
    page_icon="🧠"
)

# Utility Functions
def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Error saving data to file: {e}")
        st.session_state.bin_data = data

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
        return st.session_state.get("bin_data", {
            "recyclable": 0,
            "non_recyclable": 0,
            "classifications": [],
            "last_update": time.time()
        })

# Sample model load function (placeholder)
@st.cache_resource
def load_model():
    try:
        logger.info("Loading placeholder model")
        # In a real app this would load a model
        return "model_placeholder"
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        st.error(f"Failed to load model: {e}")
        return None

# Dark Theme Styling
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "bin_data" not in st.session_state:
    st.session_state.bin_data = load_data()

# Main UI
st.title("🧠 Smart Waste Bin Dashboard - Simple Version")
st.info("This is a simplified version to test deployment.")

# Load "model" (in real app, this would be TensorFlow)
model = load_model()
if model:
    st.success("Model placeholder loaded successfully.")

# Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📷 Waste Classification")
    st.markdown("Capture an image to classify waste as recyclable ♻️ or non-recyclable 🗑️.")
    
    if st.button("Simulate Capture"):
        prediction = np.random.choice(["recyclable", "non-recyclable"])
        confidence = np.random.uniform(0.7, 0.99)
        st.success(f"Simulated Classification: {prediction.capitalize()} (Confidence: {confidence:.4f})")
        
        # Add to history
        current_data = st.session_state.bin_data
        current_data["classifications"].insert(0, {
            "classification": prediction,
            "confidence": confidence,
            "timestamp": time.time()
        })
        current_data["classifications"] = current_data["classifications"][:10]
        save_data(current_data)

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
    
    if st.button("Simulate Level Change"):
        bin_data["recyclable"] = min(100, bin_data["recyclable"] + np.random.randint(5, 15))
        bin_data["non_recyclable"] = min(100, bin_data["non_recyclable"] + np.random.randint(5, 15))
        save_data(bin_data)
        st.rerun()

# Classification History
st.header("📜 Classification History")
classifications = bin_data.get("classifications", [])
if classifications:
    for i, entry in enumerate(classifications):
        timestamp = datetime.fromtimestamp(entry["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        classification = entry["classification"].capitalize()
        confidence = f"{entry['confidence']:.4f}"
        st.text(f"{i+1}. {timestamp} - {classification} (Confidence: {confidence})")
else:
    st.markdown("No classifications recorded yet.")

# Add system info for debugging
st.header("System Information")
st.text(f"Python version: {os.sys.version}")
st.text(f"Current working directory: {os.getcwd()}")
st.text(f"Files in directory: {os.listdir('.')}")

# Show packages
st.subheader("Installed Packages")
import pkg_resources
packages = [f"{pkg.key}=={pkg.version}" for pkg in pkg_resources.working_set]
st.code("\n".join(packages))
