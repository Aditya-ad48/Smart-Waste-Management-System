# Smart Waste Management System ♻️

A smart waste segregation system that combines real-time machine learning with IoT-based automation. The system classifies waste as **recyclable** or **non-recyclable** using a webcam and a deep learning model (EfficientNet), then operates the appropriate bin via an ESP8266 microcontroller and servo motors. Bin levels are monitored using ultrasonic sensors and displayed locally via a **Streamlit web app**.


🌐 Try the Live App
🚀 Click here to use the app[https://smart-waste-management-system-a5e2imccyite8zq97s7rur.streamlit.app/]
---

## 🚀 Features

- Real-time object detection using **EfficientNet**
- **Streamlit-based web interface** for live classification and visualization
- MQTT messaging between ML model and ESP8266
- Automatic lid operation with servo motors
- Bin fill-level detection with HC-SR04 sensors
- Fully offline-capable using **local Mosquitto MQTT broker**

---

## 🧠 Tech Stack

| Component       | Technology Used                 |
|----------------|----------------------------------|
| ML Inference    | TensorFlow, EfficientNet, OpenCV |
| Interface       | Streamlit (local web app)       |
| Microcontroller | ESP8266 (NodeMCU)               |
| Communication   | MQTT (Mosquitto)                |
| Hardware        | Servo motors, HC-SR04 sensors   |
| Languages       | Python, Arduino C++             |

---

## 📁 Project Structure

```
smart-waste-management/
├── README.md
├── waste_bin_controller.ino
├── /ml-model/
│   ├── waste_classifier.py         # Core logic
│   ├── waste_app.py                # Streamlit interface    
│   └── requirements.txt
├── broker_setup_guide.md

```

---

## 🛠️ Setup Instructions

### 1. Clone This Repository

```bash
git clone https://github.com/aditya-ad48/Smart-Waste-Management-System.git
cd Smart-Waste-Management-System
```

---

### 2. Set Up Python Environment

```bash
cd ml-model
pip install -r requirements.txt
```

---

### 3. Run Streamlit App (Local UI)

```bash
streamlit run waste_app.py
```

This app:
- Uses your webcam
- Classifies the object (recyclable / non-recyclable)
- Publishes result to `waste/classification` MQTT topic

---

### 4. Configure & Upload ESP8266 Code

1. Open `waste_bin_controller.ino` in the Arduino IDE.
2. Enter your WiFi SSID, password, and local MQTT broker IP.
3. Connect your hardware:
   - **Servo 1 (Recyclable Bin)** → D5 (GPIO14)
   - **Servo 2 (Non-Recyclable Bin)** → D6 (GPIO12)
   - **Ultrasonic 1** → Trig: D1, Echo: D2
   - **Ultrasonic 2** → Trig: D3, Echo: D4
4. Upload the code to the ESP8266 (NodeMCU).

---

### 5. Run Local Mosquitto Broker

Follow the steps in:

```
mqtt_setup_guide.md
```




---

## 🤝 Contributions Welcome

If you find this project useful, feel free to star ⭐ the repo, suggest improvements, or open a PR!

