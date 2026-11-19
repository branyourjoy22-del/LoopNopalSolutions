// PLANTILLA de credenciales. Copia este archivo como "secrets.h" (misma carpeta)
// y pon tus datos reales. secrets.h está en .gitignore: tus contraseñas no se suben a git.
#pragma once

#define WIFI_SSID "NombreDeTuRed"     // red 2.4 GHz (el ESP32-C3 NO ve redes de 5 GHz)
#define WIFI_PASS "ContrasenaDeTuRed"
#define OTA_PASS  "CambiaEstaClave"   // la misma que pondrás en $env:TINACO_OTA_PASS para subir por OTA
