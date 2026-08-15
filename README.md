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
│       ├── public/
│       │   └── og.png
│       └── simulaciones/
│           ├── simulaciones.css
│           ├── v1.html
│           ├── v2.html
│           └── v4.html
├── API/
└── Documentacion/
```

## Simulaciones

- `v1.html`: ciclo semafórico de seis fases.
- `v2.html`: perfil demostrativo de congestión durante 24 horas.
- `v4.html`: comparación visual del plan actual y el plan optimizado.

Toda la interfaz y las animaciones de las simulaciones están desarrolladas con
HTML y CSS. No existe código JavaScript ni TypeScript en el proyecto.

Las cifras mostradas son ilustrativas y no sustituyen aforos viales reales.

## Uso local

Abre `Website/Site/index.html` directamente en un navegador. El sitio no necesita
instalación de dependencias, compilación ni un servidor para funcionar.

## API conservada

La carpeta `API/` contiene un servicio mínimo en Python reservado para una futura
integración. No participa en las simulaciones HTML/CSS actuales.
