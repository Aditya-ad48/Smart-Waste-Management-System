#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Servo.h>
#include <ArduinoJson.h>

const char* ssid = "Your Wifi name ";
const char* password = "Your Wifi Password";
const char* mqtt_server = "IP Address";
WiFiClient espClient;
PubSubClient client(espClient);

Servo servoRecyclable;
Servo servoNonRecyclable;

#define SERVO_PIN_RECYCLABLE D5
#define SERVO_PIN_NONRECYCLABLE D6
#define TRIG1 D1
#define ECHO1 D2
#define TRIG2 D7
#define ECHO2 D8

#define SERVO_OPEN_US 2100
#define SERVO_CLOSE_US 900

unsigned long lastPublishTime = 0;
bool wasConnected = false;

void setupUltrasonicSensors() {
  pinMode(TRIG1, OUTPUT);
  pinMode(ECHO1, INPUT);
  pinMode(TRIG2, OUTPUT);
  pinMode(ECHO2, INPUT);
}

long getDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  long duration = pulseIn(echoPin, HIGH, 15000);
  if (duration == 0) return -1;
  return duration * 0.034 / 2;
}

void publishBinLevels() {
  long distance1 = getDistance(TRIG1, ECHO1);
  delay(50);
  long distance2 = getDistance(TRIG2, ECHO2);

  if (distance1 < 0 || distance1 > 100) distance1 = 999;
  if (distance2 < 0 || distance2 > 100) distance2 = 999;

  StaticJsonDocument<64> doc;
  doc["recyclable"] = distance1;
  doc["non_recyclable"] = distance2;
  char payload[64];
  serializeJson(doc, payload);

  Serial.print("Publishing to smartbin/levels: ");
  Serial.println(payload);

  bool success = client.publish("smartbin/levels", payload);
  if (!success) {
    Serial.println("Publish FAILED ❌, retrying...");
    delay(500);
    success = client.publish("smartbin/levels", payload);
  }
  Serial.println(success ? "Publish succeeded ✅" : "Publish FAILED again ❌");
}
void openBin(Servo& servo, int servoPin) {
  servo.attach(servoPin);
  servo.writeMicroseconds(SERVO_OPEN_US);
  delay(5000);  // Changed from 2000 to 5000 for 5 seconds
  servo.writeMicroseconds(SERVO_CLOSE_US);
  delay(500);
  servo.detach();
}

void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.print("Received on waste/classification: ");
  Serial.println(message);

  if (message == "recyclable") {
    Serial.println("Opening recyclable bin ♻️");
    openBin(servoRecyclable, SERVO_PIN_RECYCLABLE);
  } else if (message == "non-recyclable") {
    Serial.println("Opening non-recyclable bin 🚯");
    openBin(servoNonRecyclable, SERVO_PIN_NONRECYCLABLE);
  }
}

void reconnectMQTT() {
  unsigned long start = millis();
  while (!client.connected() && millis() - start < 5000) {
    Serial.println("Connecting to MQTT...");
    String clientId = "ESP8266Client_" + WiFi.macAddress();
    if (client.connect(clientId.c_str())) {
      Serial.println("Connected to MQTT broker!");
      client.subscribe("waste/classification");
      wasConnected = true;
      return;
    }
    Serial.print("Failed, state: ");
    Serial.println(client.state());
    delay(1000);
  }
  Serial.println("MQTT connection timeout");
}

void setup() {
  Serial.begin(115200);
  delay(100);

  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi...");
  unsigned long wifiStart = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - wifiStart < 10000) {
    delay(500);
    Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected ✅ IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\nWiFi connection failed");
  }

  setupUltrasonicSensors();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, reconnecting...");
    WiFi.reconnect();
    unsigned long wifiStart = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - wifiStart < 5000) {
      delay(500);
      Serial.print(".");
    }
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi reconnection failed");
      return;
    }
  }

  if (!client.connected()) {
    wasConnected = false;
    reconnectMQTT();
  } else if (!wasConnected) {
    Serial.println("MQTT connected ✅");
    wasConnected = true;
  }

  client.loop();

  unsigned long now = millis();
  if (now - lastPublishTime > 5000) {
    publishBinLevels();
    lastPublishTime = now;
  }
}