/*
 * =====================================================================================
 *  PROTOTIPO DE PRUEBA: Control de llenado del tinaco por WiFi + OTA
 *  Placa: ESP32-C3 SuperMini (chip ESP32-C3FH4, RISC-V, WiFi 2.4 GHz, E/S de 3.3 V)
 * =====================================================================================
 *
 *  QUÉ HACE
 *   - Abre/cierra una válvula solenoide NC de 12 V a través de un MOSFET IRLZ44N.
 *   - Mide flujo (L/min) y volumen (L) con el sensor de efecto Hall ZJ-S201C.
 *   - Página web en http://tinaco.local  -> botones Abrir / Cerrar / Reiniciar + lecturas.
 *   - Monitor remoto: telnet tinaco.local (puerto 23) -> mismos mensajes que el Serial.
 *   - OTA: reescribir el firmware por WiFi con  pio run -e tinaco-ota -t upload
 *   - Cierres de seguridad LOCALES: funcionan aunque se caiga el WiFi.
 *
 *  PINES DEL SUPERMINI QUE SE USAN (y por qué)
 *   GPIO3  <- pulso del sensor (cable amarillo). Pin "limpio": no es strapping, no es
 *             JTAG ni UART, y acepta interrupción.
 *   GPIO10 -> Gate del MOSFET. Pin "limpio": al encender no hace nada raro, así la
 *             válvula no se abre sola durante el arranque.
 *   GPIO8  -> LED azul integrado (activo en LOW). Es strapping pin, por eso SOLO se
 *             usa como salida del LED que ya trae la placa, nada externo conectado.
 *   GPIO9  <- botón BOOT integrado. También es strapping pin; solo se LEE después de
 *             arrancar (presionarlo al conectar el USB pone la placa en modo descarga).
 *   NO USAR: GPIO2/8/9 (strapping), GPIO20/21 (UART0, sale el log de arranque),
 *            GPIO18/19 (USB), GPIO12-17 (flash interna).
 *
 *  DIAGRAMA DE CONEXIÓN
 *
 *        Fuente 12 V (+) ─────────────┬──────────────┐
 *                                     │              │
 *                               ┌─────┴─────┐   1N4001 (banda/cátodo hacia +12 V)
 *                               │ Solenoide │      ▲
 *                               │  NC 12 V  │      │
 *                               └─────┬─────┘      │
 *                                     ├────────────┘ (ánodo)
 *                                     │
 *                                Drain (pata central)
 *        GPIO10 ──[220 Ω]──┬── Gate     IRLZ44N  (vista de frente: G - D - S)
 *                          │     Source
 *                       [10 kΩ]      │
 *                          │         │
 *        Fuente 12 V (−) ──┴─────────┴────────── GND del SuperMini  (GND COMÚN obligatorio)
 *
 *        ZJ-S201C:  rojo  ── 5V del SuperMini   (el sensor pide mínimo 3.5 V, 3.3 V no alcanza)
 *                   negro ── GND
 *                   amarillo ──[10 kΩ]──┬── GPIO3
 *                                       │
 *                                    [20 kΩ]   (divisor: 5 V × 20/30 ≈ 3.3 V; el ESP32-C3
 *                                       │       NO tolera 5 V en sus pines)
 *                                      GND
 *
 *   Alimentación del ESP32: USB-C de la laptop  -O-  buck 12V→5.0 V al pin 5V.
 *   ¡NUNCA los dos a la vez! (el buck podría inyectar corriente al USB de la PC).
 *   ¡NUNCA 12 V directo al SuperMini!
 *
 *  HIDRÁULICA (manguera de toma doméstica)
 *   Orden: llave de casa -> VÁLVULA -> SENSOR -> salida. Respeta las flechas de ambos.
 *   Con la válvula cerrada, el sensor y la manguera de salida quedan sin presión.
 *   La presión doméstica en MX suele ser de 0.5 a 2 bar (de 0.1 a 0.3 bar si viene por
 *   gravedad desde otro tinaco). Muchas válvulas NC baratas de 1/2" son de diafragma
 *   piloteado y piden mínimo ~0.2 bar (etiqueta "0.02-0.8 MPa"): con menos presión
 *   pueden no abrir bien. El cierre por "sin flujo" detecta ese caso.
 * =====================================================================================
 */

#include <Arduino.h>
#include <WiFi.h>        // WiFi: el ESP32 se une al router de tu casa
#include <WebServer.h>   // servidor de la página web de control
#include <ESPmDNS.h>     // nombre "tinaco.local" en la red, así no necesitas saber la IP
#include <ArduinoOTA.h>  // actualizar el firmware por WiFi

#if __has_include("secrets.h")
#include "secrets.h"     // WIFI_SSID, WIFI_PASS, OTA_PASS (archivo ignorado por git)
#else
#error "Falta include/secrets.h: copia include/secrets.example.h como secrets.h y llena tus datos"
#endif

// ----------------------------------------------------------------------------------
// PINES
// ----------------------------------------------------------------------------------
const uint8_t PIN_SENSOR  = 3;   // GPIO3  <- cable amarillo del sensor (pasa por el divisor 10k/20k)
const uint8_t PIN_VALVULA = 10;  // GPIO10 -> 220 Ω -> Gate del MOSFET. HIGH = válvula abierta
const uint8_t PIN_LED     = 8;   // GPIO8  -> LED azul de la placa. Al revés: LOW = encendido
const uint8_t PIN_BOTON   = 9;   // GPIO9  <- botón BOOT de la placa. LOW = presionado

const char *NOMBRE_RED = "tinaco";   // nombre en la red -> http://tinaco.local

// ----------------------------------------------------------------------------------
// AJUSTES (cámbialos después de tus pruebas)
// ----------------------------------------------------------------------------------
// Ficha del sensor ZJ-S201C: da 7.5 pulsos por segundo por cada L/min -> 7.5 × 60 = 450 por litro.
// Para calibrar: llena un recipiente conocido y pon aquí  pulsos contados ÷ litros reales.
const float PULSOS_POR_LITRO = 450.0f;

const float    LITROS_META               = 5.0f; // litros a llenar en la prueba; al llegar, cierra
const uint32_t SEGUNDOS_MAX_ABIERTA      = 180;  // máximo 3 minutos abierta (para que la bobina no se caliente)
const uint32_t SEGUNDOS_ESPERA_SIN_FLUJO = 8;    // cuántos segundos aguanta abierta sin que pase agua
const float    FLUJO_MINIMO              = 0.5f; // L/min. Menos que esto = "no está pasando agua"
                                                 // (el sensor empieza a medir bien desde ~1 L/min)

// ----------------------------------------------------------------------------------
// VARIABLES DEL SISTEMA
// ----------------------------------------------------------------------------------
volatile uint32_t pulsosNuevos = 0;  // pulsos que llegaron del sensor y aún no se han sumado.
                                     // "volatile" = cambia por la interrupción, sin aviso al loop
portMUX_TYPE candado = portMUX_INITIALIZER_UNLOCKED;  // evita leer pulsosNuevos justo cuando cambia

uint32_t pulsosTotales = 0;      // todos los pulsos desde el último "Reiniciar"
uint32_t pulsosAlAbrir = 0;      // cuántos pulsos había cuando se abrió la válvula esta vez
float    flujo         = 0.0f;   // flujo actual en L/min (se recalcula cada segundo)

bool     valvulaAbierta  = false;   // true = abierta, false = cerrada
uint32_t horaAbrio       = 0;       // millis() en el momento en que se abrió
uint32_t horaUltimoFlujo = 0;       // millis() de la última vez que sí pasaba agua
String   motivoCierre    = "ninguno";  // por qué se cerró la última vez (se ve en la web)

bool redLista = false;   // true cuando ya arrancaron OTA, web y telnet (se hace al conectar WiFi)

WebServer  servidorWeb(80);      // página web en el puerto 80 (el normal de los navegadores)
WiFiServer servidorTelnet(23);   // monitor remoto en el puerto 23 (el normal de telnet)
WiFiClient clienteTelnet;        // la PC conectada por telnet (solo una a la vez)

// ----------------------------------------------------------------------------------
// FUNCIONES DE APOYO (cálculos que se usan en varias partes)
// ----------------------------------------------------------------------------------
float litrosTotales() { return pulsosTotales / PULSOS_POR_LITRO; }                  // desde "Reiniciar"
float litrosEstaVez() { return (pulsosTotales - pulsosAlAbrir) / PULSOS_POR_LITRO; } // desde que se abrió

uint32_t segundosAbierta()  { return valvulaAbierta ? (millis() - horaAbrio) / 1000 : 0; }
uint32_t segundosSinFlujo() { return (millis() - horaUltimoFlujo) / 1000; }  // 0 si ahorita hay agua

// ----------------------------------------------------------------------------------
// INTERRUPCIÓN DEL SENSOR: se ejecuta sola cada vez que el rotor del sensor da un pulso.
// IRAM_ATTR = se guarda en RAM para que corra rapidísimo. Solo suma 1, nada más.
// ----------------------------------------------------------------------------------
void IRAM_ATTR contarPulso()
{
    portENTER_CRITICAL_ISR(&candado);
    pulsosNuevos++;
    portEXIT_CRITICAL_ISR(&candado);
}

// Toma los pulsos nuevos y deja el contador en cero (con candado para no perder ninguno).
uint32_t leerPulsos()
{
    portENTER_CRITICAL(&candado);
    uint32_t pulsos = pulsosNuevos;
    pulsosNuevos = 0;
    portEXIT_CRITICAL(&candado);
    return pulsos;
}

// ----------------------------------------------------------------------------------
// MENSAJES: escribe en el Serial (USB) y también por telnet si hay alguien conectado.
// Se usa igual que printf:  mensaje("Flujo %.2f", flujo);
// ----------------------------------------------------------------------------------
void mensaje(const char *formato, ...)
{
    char texto[160];
    va_list datos;
    va_start(datos, formato);
    vsnprintf(texto, sizeof(texto), formato, datos);
    va_end(datos);

    Serial.println(texto);
    if (clienteTelnet && clienteTelnet.connected())
        clienteTelnet.println(texto);
}

// ----------------------------------------------------------------------------------
// VÁLVULA
// ----------------------------------------------------------------------------------
void abrirValvula(const char *quien)   // quien = "web", "boton" o "comando" (para el registro)
{
    if (valvulaAbierta) return;
    digitalWrite(PIN_VALVULA, HIGH);  // 3.3 V al Gate -> el MOSFET conduce -> 12 V a la bobina -> abre
    valvulaAbierta  = true;
    horaAbrio       = millis();
    horaUltimoFlujo = horaAbrio;      // empieza a contar la espera "sin flujo" desde ahora
    pulsosAlAbrir   = pulsosTotales;
    mensaje(">> VALVULA ABIERTA (por %s)", quien);
}

void cerrarValvula(const char *motivo)
{
    digitalWrite(PIN_VALVULA, LOW);   // 0 V al Gate -> el MOSFET corta -> sin corriente -> el resorte la cierra
    if (!valvulaAbierta) return;
    valvulaAbierta = false;
    motivoCierre   = motivo;
    mensaje(">> VALVULA CERRADA (%s) | %.2f L en esta apertura, %lu s",
            motivo, litrosEstaVez(), (unsigned long)((millis() - horaAbrio) / 1000));
}

// ----------------------------------------------------------------------------------
// SEGURIDAD: se revisa en cada vuelta del loop mientras la válvula está abierta,
// con o sin WiFi. Regresa el motivo para cerrar, o nullptr si todo está bien.
// ----------------------------------------------------------------------------------
const char *revisarSeguridad()
{
    // 1) No está pasando agua (flujo entre 0 y 0.49 L/min)...
    //    ...pero solo cuenta si ya lleva varios segundos así: al abrir, el agua tarda en
    //    llegar y el sensor tarda 1 s en medir. Sin esta espera se cerraría al instante.
    //    Causas típicas: llave de la casa cerrada, poca presión, sensor mal conectado.
    if (flujo < FLUJO_MINIMO && segundosSinFlujo() >= SEGUNDOS_ESPERA_SIN_FLUJO)
        return "sin flujo";

    // 2) Sí hay agua, pero ya lleva demasiado tiempo abierta.
    if (segundosAbierta() >= SEGUNDOS_MAX_ABIERTA)
        return "tiempo maximo";

    // 3) Ya se llenó lo que queríamos. Se usa >= porque los litros avanzan "a saltos"
    //    y pueden pasarse del número exacto.
    if (litrosEstaVez() >= LITROS_META)
        return "meta de litros";

    return nullptr;  // todo bien: sigue abierta
}

// ----------------------------------------------------------------------------------
// COMANDOS (iguales por el monitor Serial USB y por telnet)
//   a = abrir, c = cerrar, r = reiniciar litros, ? = ayuda
// ----------------------------------------------------------------------------------
void mostrarAyuda()
{
    mensaje("Comandos: a=abrir  c=cerrar  r=reiniciar litros  ?=ayuda");
    mensaje("Web: http://%s.local  (IP %s)", NOMBRE_RED, WiFi.localIP().toString().c_str());
}

void reiniciarLitros()
{
    pulsosTotales = 0;
    pulsosAlAbrir = 0;
    mensaje(">> Litros reiniciados");
}

void ejecutarComando(char letra)
{
    switch (letra)
    {
    case 'a': case 'A': abrirValvula("comando");  break;
    case 'c': case 'C': cerrarValvula("comando"); break;
    case 'r': case 'R': reiniciarLitros();        break;
    case '?':           mostrarAyuda();           break;
    default: break;  // ignora Enter, espacios y los bytes extra que manda telnet al conectar
    }
}

// ----------------------------------------------------------------------------------
// PÁGINA WEB (se guarda en la flash; se actualiza sola cada 1 s)
// ----------------------------------------------------------------------------------
const char PAGINA_WEB[] = R"HTML(<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tinaco</title>
<style>
 body{font-family:system-ui,sans-serif;max-width:420px;margin:20px auto;padding:0 16px;background:#f4f6f8;color:#222}
 h1{font-size:1.3em} .card{background:#fff;border-radius:10px;padding:14px;margin:10px 0;box-shadow:0 1px 3px #0002}
 .row{display:flex;justify-content:space-between;padding:4px 0} b{font-variant-numeric:tabular-nums}
 button{width:32%;padding:14px 0;font-size:1em;border:0;border-radius:8px;color:#fff;cursor:pointer}
 #abrir{background:#1e88e5} #cerrar{background:#e53935} #reset{background:#757575}
 .on{color:#1e88e5} .off{color:#e53935}
</style></head><body>
<h1>Control de tinaco (prueba)</h1>
<div class="card">
 <div class="row">Válvula <b id="estado">-</b></div>
 <div class="row">Flujo <b><span id="flujo">-</span> L/min</b></div>
 <div class="row">Litros esta vez <b id="litrosVez">-</b></div>
 <div class="row">Litros totales <b id="litros">-</b></div>
 <div class="row">Tiempo abierta <b><span id="segundos">-</span> s</b></div>
 <div class="row">Último cierre <b id="motivo">-</b></div>
 <div class="row">Señal WiFi <b><span id="senal">-</span> dBm</b></div>
</div>
<div class="card">
 <button id="abrir"  onclick="enviar('abrir')">Abrir</button>
 <button id="cerrar" onclick="enviar('cerrar')">Cerrar</button>
 <button id="reset"  onclick="enviar('reset')">Reiniciar</button>
</div>
<script>
const $=id=>document.getElementById(id);
function enviar(orden){fetch('/'+orden,{method:'POST'}).then(actualizar)}
function actualizar(){fetch('/estado').then(r=>r.json()).then(d=>{
 $('estado').textContent=d.abierta?'ABIERTA':'CERRADA'; $('estado').className=d.abierta?'on':'off';
 $('flujo').textContent=d.flujo.toFixed(2); $('litrosVez').textContent=d.litrosVez.toFixed(2);
 $('litros').textContent=d.litros.toFixed(2); $('segundos').textContent=d.segundos;
 $('motivo').textContent=d.motivo; $('senal').textContent=d.senal;
}).catch(()=>{$('estado').textContent='sin conexión'; $('estado').className='off'})}
setInterval(actualizar,1000); actualizar();
</script></body></html>)HTML";

// Manda el estado actual en formato JSON (lo lee la página cada segundo).
void enviarEstado()
{
    char json[200];
    snprintf(json, sizeof(json),
             "{\"abierta\":%s,\"flujo\":%.2f,\"litros\":%.3f,\"litrosVez\":%.3f,"
             "\"segundos\":%lu,\"senal\":%d,\"motivo\":\"%s\"}",
             valvulaAbierta ? "true" : "false", flujo, litrosTotales(), litrosEstaVez(),
             (unsigned long)segundosAbierta(), WiFi.RSSI(), motivoCierre.c_str());
    servidorWeb.send(200, "application/json", json);
}

void configurarPaginaWeb()
{
    servidorWeb.on("/", HTTP_GET, []() { servidorWeb.send(200, "text/html", PAGINA_WEB); });
    servidorWeb.on("/estado", HTTP_GET, enviarEstado);
    // Las órdenes van por POST (no GET) para que el navegador no abra la válvula
    // por accidente al "precargar" un enlace.
    servidorWeb.on("/abrir",  HTTP_POST, []() { abrirValvula("web");  enviarEstado(); });
    servidorWeb.on("/cerrar", HTTP_POST, []() { cerrarValvula("web"); enviarEstado(); });
    servidorWeb.on("/reset",  HTTP_POST, []() { reiniciarLitros();    enviarEstado(); });
    servidorWeb.onNotFound([]() { servidorWeb.send(404, "text/plain", "No encontrado"); });
}

// ----------------------------------------------------------------------------------
// OTA: actualizar el firmware por WiFi
// ----------------------------------------------------------------------------------
void configurarOTA()
{
    ArduinoOTA.setHostname(NOMBRE_RED);  // también registra tinaco.local
    ArduinoOTA.setPassword(OTA_PASS);    // sin esta clave nadie más en tu red puede reprogramarlo

    ArduinoOTA.onStart([]() {
        cerrarValvula("actualizacion OTA");  // SEGURIDAD: nunca actualizar con la válvula abierta
        mensaje("OTA: iniciando actualizacion...");
    });
    ArduinoOTA.onProgress([](unsigned int enviado, unsigned int total) {
        static uint8_t ultimoPorcentaje = 255;
        uint8_t porcentaje = enviado * 100 / total;
        if (porcentaje % 10 == 0 && porcentaje != ultimoPorcentaje)  // avisa cada 10 %
        {
            ultimoPorcentaje = porcentaje;
            mensaje("OTA: %u%%", porcentaje);
        }
    });
    ArduinoOTA.onEnd([]() { mensaje("OTA: listo, reiniciando"); });
    ArduinoOTA.onError([](ota_error_t error) { mensaje("OTA: error %u", error); });
}

// Se llama una sola vez, la primera vez que conecta el WiFi (estos servicios necesitan red).
void arrancarServiciosDeRed()
{
    configurarOTA();
    ArduinoOTA.begin();                   // arranca OTA + nombre tinaco.local
    MDNS.addService("http", "tcp", 80);   // anuncia la página web en la red
    configurarPaginaWeb();
    servidorWeb.begin();
    servidorTelnet.begin();
    servidorTelnet.setNoDelay(true);      // manda cada línea al instante
    redLista = true;

    mensaje("WiFi OK  IP: %s  Senal: %d dBm", WiFi.localIP().toString().c_str(), WiFi.RSSI());
    mensaje("OTA listo | web: http://%s.local | telnet %s.local", NOMBRE_RED, NOMBRE_RED);
}

// Acepta una PC por telnet (solo una a la vez) y lee las letras que escribe.
void atenderTelnet()
{
    if (servidorTelnet.hasClient())
    {
        if (!clienteTelnet || !clienteTelnet.connected())
        {
            clienteTelnet = servidorTelnet.available();
            clienteTelnet.println("Conectado al tinaco. Escribe ? para ayuda.");
        }
        else
        {
            servidorTelnet.available().stop();  // ya hay alguien conectado: rechaza al segundo
        }
    }
    while (clienteTelnet && clienteTelnet.available())
        ejecutarComando((char)clienteTelnet.read());
}

// ----------------------------------------------------------------------------------
// BOTÓN BOOT (GPIO9): cada vez que lo presionas, abre o cierra.
// "Antirrebote": un botón físico vibra unos milisegundos al presionarlo; solo se acepta
// el cambio si se mantiene estable 50 ms.
// ----------------------------------------------------------------------------------
void atenderBoton()
{
    static bool     estadoBoton  = HIGH;  // estado ya confirmado (HIGH = suelto)
    static bool     lecturaAntes = HIGH;  // lo que se leyó la vuelta pasada
    static uint32_t horaCambio   = 0;     // cuándo cambió la lectura por última vez

    bool lectura = digitalRead(PIN_BOTON);
    if (lectura != lecturaAntes)
    {
        horaCambio   = millis();
        lecturaAntes = lectura;
    }

    if (millis() - horaCambio > 50 && lectura != estadoBoton)
    {
        estadoBoton = lectura;
        if (estadoBoton == LOW)  // solo al presionar, no al soltar
        {
            if (valvulaAbierta) cerrarValvula("boton");
            else                abrirValvula("boton");
        }
    }
}

// ----------------------------------------------------------------------------------
// SETUP: se ejecuta una vez al encender
// ----------------------------------------------------------------------------------
void setup()
{
    // 1) Lo PRIMERO: válvula cerrada. La resistencia de 10 kΩ Gate->GND ya la mantenía
    //    cerrada durante el arranque; aquí el pin toma el control en LOW.
    pinMode(PIN_VALVULA, OUTPUT);
    digitalWrite(PIN_VALVULA, LOW);

    pinMode(PIN_LED, OUTPUT);
    digitalWrite(PIN_LED, HIGH);         // LED apagado (funciona al revés)

    pinMode(PIN_BOTON, INPUT_PULLUP);    // el botón BOOT une GPIO9 con GND al presionarlo

    // Sensor: INPUT sin pull-up interno porque el divisor 10k/20k ya fija el voltaje.
    // FALLING = cuenta cuando la señal baja de 3.3 V a 0 V (un pulso por cada giro del rotor).
    pinMode(PIN_SENSOR, INPUT);
    attachInterrupt(digitalPinToInterrupt(PIN_SENSOR), contarPulso, FALLING);

    Serial.begin(115200);                // por el USB-C de la placa
    delay(1500);                         // tiempo para que alcances a abrir el monitor serial
    mensaje("\n=== Tinaco prototipo WiFi/OTA ===");

    // 2) WiFi. No se queda esperando aquí: el loop revisa cuándo conecta. Así el botón
    //    y la seguridad funcionan aunque el router esté apagado.
    WiFi.mode(WIFI_STA);                 // STA = se conecta a un router (no crea su propia red)
    WiFi.setHostname(NOMBRE_RED);
    WiFi.setAutoReconnect(true);         // si se cae el WiFi, se reconecta solo
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    // Si la señal no llega bien a la azotea, prueba quitar las // de la línea de abajo
    // (problema conocido de la antena de varios SuperMini: con potencia máxima conectan peor):
    // WiFi.setTxPower(WIFI_POWER_8_5dBm);
    mensaje("Conectando a WiFi \"%s\"...", WIFI_SSID);
}

// ----------------------------------------------------------------------------------
// LOOP: se repite sin parar. No usa delay() para que la web, el OTA y telnet
// siempre respondan; en su lugar compara tiempos con millis().
// ----------------------------------------------------------------------------------
void loop()
{
    uint32_t ahora = millis();   // milisegundos desde que encendió

    // --- Red (solo si hay WiFi) ---
    bool hayWifi = (WiFi.status() == WL_CONNECTED);
    if (hayWifi)
    {
        if (!redLista) arrancarServiciosDeRed();
        ArduinoOTA.handle();
        servidorWeb.handleClient();
        atenderTelnet();
    }

    // --- LED: encendido = válvula abierta | apagado = cerrada | parpadeando = buscando WiFi ---
    if (valvulaAbierta) digitalWrite(PIN_LED, LOW);
    else if (hayWifi)   digitalWrite(PIN_LED, HIGH);
    else                digitalWrite(PIN_LED, (ahora / 250) % 2);

    // --- Botón y comandos por USB ---
    atenderBoton();
    while (Serial.available()) ejecutarComando((char)Serial.read());

    // --- Cada 1 segundo: calcular flujo y mostrar lecturas ---
    static uint32_t horaUltimoCalculo = 0;
    if (ahora - horaUltimoCalculo >= 1000)
    {
        float segundos = (ahora - horaUltimoCalculo) / 1000.0f;  // casi siempre 1.0
        horaUltimoCalculo = ahora;

        uint32_t pulsos = leerPulsos();
        pulsosTotales += pulsos;
        flujo = (pulsos / PULSOS_POR_LITRO) * 60.0f / segundos;  // litros en este segundo × 60 = L/min
        if (flujo >= FLUJO_MINIMO) horaUltimoFlujo = ahora;      // sí pasa agua: reinicia la espera

        mensaje("%s | %5.2f L/min | esta vez %6.3f L | total %7.3f L | %3lu s",
                valvulaAbierta ? "ABIERTA" : "cerrada", flujo, litrosEstaVez(),
                litrosTotales(), (unsigned long)segundosAbierta());
    }

    // --- Seguridad (siempre, con o sin WiFi) ---
    if (valvulaAbierta)
    {
        const char *motivo = revisarSeguridad();
        if (motivo != nullptr) cerrarValvula(motivo);
    }
}
