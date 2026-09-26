#if defined(__has_include)
#if __has_include(<Arduino.h>)
#include <Arduino.h>
#else
using uint8_t = unsigned char;
enum : uint8_t { LOW = 0, HIGH = 1, OUTPUT = 1 };
void pinMode(uint8_t pin, uint8_t mode);
void digitalWrite(uint8_t pin, uint8_t value);
void delay(unsigned long milliseconds);

class HardwareSerial
{
public:
    void begin(unsigned long baud);
    void println(const char *message);
};

extern HardwareSerial Serial;
#endif
#else
#include <Arduino.h>
#endif

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