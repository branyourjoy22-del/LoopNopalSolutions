/*
  Llenado de tinaco — ESP32-C3
  Proyecto: Loop Nopal Solutions

  Lógica (ver diagrama de flujo):
    1. El solenoide arranca ABIERTO.
    2. Se cuentan los pulsos del sensor de flujo (ZJ-S201C) y se
       convierten a litros acumulados.
    3. En cuanto el acumulado llega al límite definido (nivel medio
       deseado del tinaco), se cierra el solenoide de inmediato.
    4. Se espera un tiempo de reposo, se resetea el contador de
       pulsos, y se vuelve a abrir el solenoide para reiniciar el ciclo.

  Hardware:
    - Sensor de flujo ZJ-S201C: salida NPN por pulsos, 1-30 L/min,
      alimentación 3.5-24V (se recomienda alimentar aparte a 5V,
      NO desde el pin 3V3 del ESP32-C3).
    - Solenoide 12V controlado por MOSFET IRLZ44N: gate al pin del
      ESP32 (a través de resistencia de compuerta), drain al negativo
      del solenoide, source a tierra común con el ESP32.

  IMPORTANTE — calibración:
    El valor PULSOS_POR_LITRO varía según el sensor específico y la
    presión de tu línea. El valor de abajo es un punto de partida
    tomado de la hoja de datos; para tu proyecto, mide cuántos pulsos
    da tu sensor real al pasar exactamente 1 litro (por ejemplo,
    llenando una garrafa conocida) y ajusta esta constante antes de
    confiar en el volumen calculado.
*/

#if __has_include(<Arduino.h>)
#include <Arduino.h>
#else
// Fallback declarations for editors that are not configured with the
// Arduino/ESP32 include path. The Arduino build uses Arduino.h above.
#ifndef IRAM_ATTR
#define IRAM_ATTR
#endif

constexpr int HIGH = 1;
constexpr int LOW = 0;
constexpr int INPUT_PULLUP = 2;
constexpr int OUTPUT = 1;
constexpr int FALLING = 2;

using byte = unsigned char;
using boolean = bool;

unsigned long millis();
void delay(unsigned long);
void pinMode(int, int);
void digitalWrite(int, int);
int digitalPinToInterrupt(int);
void attachInterrupt(int, void (*)(), int);
void noInterrupts();
void interrupts();

struct SerialStub {
  void begin(unsigned long);
  void print(const char *, int = 0);
  void print(float, int = 2);
  void println(const char * = "");
};
extern SerialStub Serial;
#endif

// ---------- Configuración de pines ----------
const int PIN_SENSOR_FLUJO = 4;   // pin digital con soporte de interrupción
const int PIN_SOLENOIDE    = 5;   // pin digital -> gate del IRLZ44N

// ---------- Configuración del solenoide ----------
// Ajusta según cómo esté cableado tu MOSFET:
// si el solenoide se energiza con el pin en HIGH, deja esto como está.
const int SOLENOIDE_ABIERTO = HIGH;
const int SOLENOIDE_CERRADO = LOW;

// ---------- Calibración del sensor ----------
// Punto de partida de hoja de datos — CALIBRAR con tu sensor real.
const float PULSOS_POR_LITRO = 300.0;

// ---------- Parámetros del ciclo ----------
// Volumen que define "nivel medio" del tinaco. Ajusta según la
// capacidad de tu tinaco y qué tan lleno quieres que quede cada ciclo.
const float LIMITE_LITROS = 150.0;

// Tiempo que el solenoide permanece cerrado antes de reabrir,
// para no encadenar ciclos de apertura/cierre demasiado seguidos.
const unsigned long TIEMPO_REPOSO_MS = 5UL * 60UL * 1000UL; // 5 minutos

// ---------- Variables del contador de pulsos ----------
volatile unsigned long contadorPulsos = 0;

void IRAM_ATTR isrContarPulso() {
  contadorPulsos++;
}

// ---------- Estado del ciclo ----------
enum EstadoCiclo { LLENANDO, EN_REPOSO };
EstadoCiclo estado = LLENANDO;
unsigned long inicioReposo = 0;

void setup() {
  Serial.begin(115200);
  delay(200);

  pinMode(PIN_SENSOR_FLUJO, INPUT_PULLUP);
  pinMode(PIN_SOLENOIDE, OUTPUT);

  // Arranca con el solenoide abierto (inicio del ciclo)
  digitalWrite(PIN_SOLENOIDE, SOLENOIDE_ABIERTO);
  estado = LLENANDO;

  attachInterrupt(digitalPinToInterrupt(PIN_SENSOR_FLUJO), isrContarPulso, FALLING);

  Serial.println("Sistema iniciado. Solenoide ABIERTO. Contando pulsos...");
}

void loop() {
  switch (estado) {

    case LLENANDO: {
      // Lectura segura del contador (se modifica dentro de la interrupción)
      noInterrupts();
      unsigned long pulsos = contadorPulsos;
      interrupts();

      float litrosAcumulados = pulsos / PULSOS_POR_LITRO;

      // Reporte periódico simple (cada ~2s aprox, sin bloquear)
      static unsigned long ultimoReporte = 0;
      if (millis() - ultimoReporte > 2000) {
        Serial.print("Volumen acumulado: ");
        Serial.print(litrosAcumulados, 2);
        Serial.println(" L");
        ultimoReporte = millis();
      }

      if (litrosAcumulados >= LIMITE_LITROS) {
        // Cierre inmediato
        digitalWrite(PIN_SOLENOIDE, SOLENOIDE_CERRADO);
        Serial.println(">> Límite alcanzado. Solenoide CERRADO. Iniciando reposo...");

        inicioReposo = millis();
        estado = EN_REPOSO;
      }
      break;
    }

    case EN_REPOSO: {
      if (millis() - inicioReposo >= TIEMPO_REPOSO_MS) {
        // Resetea el contador y reabre el solenoide
        noInterrupts();
        contadorPulsos = 0;
        interrupts();

        digitalWrite(PIN_SOLENOIDE, SOLENOIDE_ABIERTO);
        Serial.println(">> Reposo terminado. Contador reseteado. Solenoide ABIERTO.");

        estado = LLENANDO;
      }
      break;
    }
  }
}
