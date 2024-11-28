#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <Servo.h>
#include <DHT.h>
#include <WiFiClientSecure.h>
#define PIR_PIN D0
#define DHTPIN D6
#define BUZZER_PIN D9
#define DHTTYPE DHT11
#define MQ135_PIN A0   // Gas sensor connected to A0 of ESP8266
float R0 = 10.0;       // Calibrated R0 value for the sensor
unsigned long lastMotionTime = 0; // Thời điểm lần cuối gửi thông báo chuyển động
const unsigned long motionInterval = 10000; // Khoảng thời gian chờ 10 giây (10000 ms)
const char* ssid = "quetran";
const char* password = "12345678";
ESP8266WebServer server(80);
WiFiClientSecure client;

int ledPin1 = D1;
int ledPin2 = D2;
int fanPin3 = D3;
int ledPin4 = D5;
int ledPin5 = D8;
int motionSensorPin = D0;
Servo myServo;
int servoPin = D4;
bool led1State = false;
bool led2State = false;
bool fan3State = false;
bool led4State = false;
bool led5State = false;

DHT dht(DHTPIN, DHTTYPE);
unsigned long previousMillis = 0;
const long interval = 1000;

// Rain sensor pin
int rainSensorPin = D7;  // Digital pin connected to rain sensor

// Telegram bot token and chat ID
const char* telegramBotToken = "7837480809:AAH538Eptco2p08H_j0C_M-_86mO_teXLsM";
const char* telegramChatID = "-1002384540377";

// Function to send a message to Telegram
void sendTelegramMessage(const String &message) {
  if (client.connect("api.telegram.org", 443)) {
    String url = "/bot" + String(telegramBotToken) + "/sendMessage?chat_id=" + String(telegramChatID) + "&text=" + message;
    client.print(String("GET ") + url + " HTTP/1.1\r\n" +
                 "Host: api.telegram.org\r\n" +
                 "Connection: close\r\n\r\n");
  }
}

void setup() {
  Serial.begin(115200);
  
  pinMode(ledPin1, OUTPUT);
  pinMode(ledPin2, OUTPUT);
  pinMode(fanPin3 , OUTPUT);
  pinMode(ledPin4, OUTPUT);
  pinMode(ledPin5, OUTPUT);
  pinMode(rainSensorPin, INPUT);  // Set rain sensor pin as input
  pinMode(motionSensorPin, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(D9, OUTPUT);  // Đặt chân D9 là output
  digitalWrite(BUZZER_PIN, LOW);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to Wi-Fi");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  myServo.attach(servoPin);
  dht.begin();
  client.setInsecure();  // Disable SSL verification for Telegram API

  server.on("/led1/on", []() {
    digitalWrite(ledPin1, HIGH);
    led1State = true;
    server.send(200, "text/plain", "LED 1 ON");
  });
  server.on("/led1/off", []() {
    digitalWrite(ledPin1, LOW);
    led1State = false;
    server.send(200, "text/plain", "LED 1 OFF");
  });

  server.on("/led2/on", []() {
    digitalWrite(ledPin2, HIGH);
    led2State = true;
    server.send(200, "text/plain", "LED 2 ON");
  });
  server.on("/led2/off", []() {
    digitalWrite(ledPin2, LOW);
    led2State = false;
    server.send(200, "text/plain", "LED 2 OFF");
  });

  server.on("/fan3/on", []() {
    digitalWrite(fanPin3 , HIGH);
    fan3State = true;
    server.send(200, "text/plain", "FAN 3 ON");
  });
  server.on("/fan3/off", []() {
    digitalWrite(fanPin3 , LOW);
    fan3State = false;
    server.send(200, "text/plain"," Fan 3 OFF");
  });

  server.on("/led4/on", []() {
    digitalWrite(ledPin4, HIGH);
    led4State = true;
    server.send(200, "text/plain", "LED 4 ON");
  });
  server.on("/led4/off", []() {
    digitalWrite(ledPin4, LOW);
    led4State = false;
    server.send(200, "text/plain", "LED 4 OFF");
  });
    server.on("/led5/on", []() {
    digitalWrite(ledPin5, HIGH);
    led5State = true;
    server.send(200, "text/plain", "LED 5 ON");
  });
  server.on("/led5/off", []() {
    digitalWrite(ledPin5, LOW);
    led5State = false;
    server.send(200, "text/plain", "LED 45OFF");
  });
  server.on("/servo/180", []() {
    myServo.write(180);
    server.send(200, "text/plain", "Cửa đã mở");
  });
    server.on("/servo/0", []() {
    myServo.write(0);
    server.send(200, "text/plain", "Cửa đã đóng");
  });

  server.on("/servo", []() {
    if (server.hasArg("angle")) {
        int angle = server.arg("angle").toInt();
        angle = constrain(angle, 0, 180);
        myServo.write(angle);
        server.send(200, "text/plain", "Servo moved to angle: " + String(angle));
    } else {
        server.send(400, "text/plain", "Angle not specified");
    }
  });

  server.on("/temperature", []() {
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    if (isnan(temperature) || isnan(humidity)) {
        server.send(500, "text/plain; charset=utf-8", "Failed to read from DHT sensor");
        return;
    }

    String message = "Nhiệt độ: " + String(temperature) + " °C\n";
    message += "Độ ẩm: " + String(humidity) + " %";
    server.send(200, "text/plain; charset=utf-8", message);

    Serial.println("Nhiệt độ: " + String(temperature) + " °C");
    Serial.println("Độ ẩm: " + String(humidity) + " %");
  });

  server.on("/gas", []() {
    int sensorValue = analogRead(MQ135_PIN);
    float RS = ((1023.0 / sensorValue) - 1) * R0;
    float ppmGas = 116.6020682 * pow((RS / R0), -2.769034857);
    float ppmSmoke = 70.0 * pow((RS / R0), -3.2);

    String message = "Nồng độ khí gas (ppm): " + String(ppmGas) + "\n";
    message += "Nồng độ khói (ppm): " + String(ppmSmoke);
    server.send(200, "text/plain; charset=utf-8", message);

    Serial.println("Nồng độ khí gas (ppm): " + String(ppmGas));
    Serial.println("Nồng độ khói (ppm): " + String(ppmSmoke));
  });

  server.begin();
}

void loop() {
  server.handleClient();
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
       if (digitalRead(PIR_PIN) == HIGH) {
      Serial.println("Phát hiện chuyển động!");
      digitalWrite(ledPin5, HIGH);
    } else {
      digitalWrite(ledPin5, LOW);
    }

    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    if (!isnan(temperature) && !isnan(humidity)) {
      Serial.println("Nhiệt độ: " + String(temperature) + " C");
      Serial.println("Độ ẩm: " + String(humidity) + " %");
      
      int sensorValue = analogRead(MQ135_PIN);
      float RS = ((1023.0 / sensorValue) - 1) * R0;
      float ppmGas = 116.6020682 * pow((RS / R0), -2.769034857);
    float ppmSmoke = 70.0 * pow((RS / R0), -3.2);
      Serial.println("Nồng độ khí gas (ppm): " + String(ppmGas));
       Serial.println("Nồng độ khói (ppm): " + String(ppmSmoke));
      // Trigger alert if gas concentration exceeds threshold
      if (ppmGas > 20.0 && (digitalRead(rainSensorPin) == LOW)) {
        digitalWrite(ledPin4, HIGH);
        digitalWrite(BUZZER_PIN, HIGH);  // Turn on LED for alarm 
        myServo.write(180);   
       sendTelegramMessage("Cảnh báo: Phát hiện có khói hoặc khí độc!");
      } else if (ppmGas > 20.0 && (digitalRead(rainSensorPin) == HIGH))  {
        digitalWrite(ledPin4, HIGH);  // Turn off alarm LED
        led4State = true;
        digitalWrite(BUZZER_PIN, HIGH);
sendTelegramMessage("Cảnh báo: Phát hiện có khói hoặc khí độc!");
      }
        else if (ppmGas < 10 && (digitalRead(rainSensorPin) == LOW))  {
         myServo.write(0);  // Move servo to 0 degrees
        sendTelegramMessage("Cảnh báo: Phát hiện mưa cửa đã được đóng!");
    } else {
     digitalWrite(ledPin4, LOW);  // Turn off alarm LED
        led4State = false;
        digitalWrite(BUZZER_PIN, LOW);
    }
  }
}}
