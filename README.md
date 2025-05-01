# Smart Waste Management System ♻️

A smart waste segregation system that combines real-time machine learning with IoT-based automation. The system classifies waste as **recyclable** or **non-recyclable** using a webcam and a deep learning model (EfficientNet), then operates the appropriate bin via an ESP8266 microcontroller and servo motors. Bin levels are monitored using ultrasonic sensors and displayed locally via a **Streamlit web app**.

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

