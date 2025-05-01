# 📡 MQTT Broker Setup Guide

## Install Mosquitto Broker (Linux/macOS)

### On Ubuntu/Debian:

```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

###On macOS (with Homebrew):

```bash
brew install mosquitto
brew services start mosquitto
```

##Test the MQTT Broker

Open two terminal windows:

###Terminal 1 – Subscribe to a topic:

```bash
mosquitto_sub -h localhost -t "waste/classification"
```
###Terminal 2 – Publish a message:

```bash
mosquitto_pub -h localhost -t "waste/classification" -m "recyclable"
```
You should see recyclable printed in the first terminal.



