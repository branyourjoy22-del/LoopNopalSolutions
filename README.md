# Loop Nopal Solutions

Proyecto privado de Loop Nopal Solutions para representar visualmente ciclos
semafóricos y escenarios de congestión urbana.

## Estructura actual

```text
LoopNopalSolutions/
├── Website/
│   └── Site/
│       ├── index.html
│       ├── styles.css
│       ├── .claude/
│       │   └── hosting.json
│       ├── public/
│       │   └── og.png
│       └── simulaciones/
│           ├── simulaciones.css
│           ├── v1.html
│           ├── v2.html
│           ├── v4.html
│           └── Simulacion_visual_v5_event_log.html
├── API/
└── Documentacion/
```

## Simulaciones

- `v1.html`: ciclo semafórico de seis fases.
- `v2.html`: perfil demostrativo de congestión durante 24 horas.
- `v4.html`: comparación visual del plan actual y el plan optimizado.
- `Simulacion_visual_v5_event_log.html` (tarjeta 04, tiempo real): corre el
  plan actual y el optimizado en paralelo sobre los mismos vehículos
  simulados, con 1–2 incidentes aleatorios por día que la optimizada detecta
  y responde reasignando tiempos de verde, y un registro de eventos en vivo.

Las simulaciones `v1`, `v2` y `v4` están hechas solo con HTML y CSS
(deterministas, sin cálculo en tiempo real). `Simulacion_visual_v5_event_log.html`
sí incorpora JavaScript para generar incidentes aleatorios, recalcular el plan
optimizado y actualizar métricas y el registro de eventos en vivo.

Las cifras mostradas son ilustrativas y no sustituyen aforos viales reales.

## Uso local

Abre `Website/Site/index.html` directamente en un navegador. El sitio no necesita
instalación de dependencias, compilación ni un servidor para funcionar.

## API conservada

La carpeta `API/` contiene un servicio mínimo en Python reservado para una futura
integración. No participa en las simulaciones HTML/CSS actuales.
