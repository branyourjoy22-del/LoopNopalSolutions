#include <Arduino.h>

#define LED_PIN 8

void setup()
{
    pinMode(LED_PIN, OUTPUT);

    Serial.begin(115200);

    delay(1000);

    Serial.println("ESP32-C3 SuperMini iniciado");
}

void loop()
{
    digitalWrite(LED_PIN, HIGH);
    Serial.println("LED ON");
    delay(1000);

    digitalWrite(LED_PIN, LOW);
    Serial.println("LED OFF");
    delay(1000);
}