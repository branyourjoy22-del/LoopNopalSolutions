# Sitio estático de Loop Nopal Solutions

El sitio (`index.html`) y las simulaciones `v1`/`v2`/`v4` utilizan solo HTML y
CSS. La simulación 04 (`Simulacion_visual_v5_event_log.html`) sí usa
JavaScript para su motor de incidentes en tiempo real.

## Abrir el proyecto

Abre `index.html` directamente en un navegador. No requiere instalación,
compilación, servidor ni dependencias de Node.

## Archivos principales

```text
index.html
styles.css
.claude/
  hosting.json
public/qro-aerea-cristian-gonzalez.jpg
public/loop-nopal-logo-transparent.png
simulaciones/
  simulaciones.css
  v1.html
  v2.html
  v4.html
  Simulacion_visual_v5_event_log.html
```

## Alcance de las simulaciones

`v1`, `v2` y `v4` son deterministas: HTML/CSS no calculan llegadas aleatorias,
colas ni métricas en tiempo real. `Simulacion_visual_v5_event_log.html` es la
excepción — corre el plan actual y el optimizado en paralelo sobre los mismos
vehículos simulados, genera 1 o 2 incidentes aleatorios por día (6:00–23:00)
que la optimizada detecta con un retraso simulado y responde reasignando
segundos de verde, y registra cada evento en vivo con hora exacta.

En todos los casos, las cifras mostradas son ilustrativas y no sustituyen
aforos viales reales. Antes de usar los valores para decisiones operativas se
requieren aforos y validación técnica.
