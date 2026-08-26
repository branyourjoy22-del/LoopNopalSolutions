"""
Simulación del ciclo semafórico con reloj de 24 h y congestión vehicular
Intersección: Av. Sombrerete - Calle 6 - Av. Praxedis Guerrero (Querétaro)

Fuente de los datos de las fases: diagrama temporal (PDF) y mapa mental
(imagen) proporcionados por el usuario. Ciclo del semáforo = 100 s,
repartido en 6 fases:

    F1  0-20 s   Av. Sombrerete UP con giro izquierdo protegido
    F2  20-40 s  Av. Sombrerete UP y DOWN con verde simultaneo (de frente)
    F3  40-50 s  Metrobus sentido UP
    F4  50-60 s  Metrobus sentido DOWN
    F5  60-80 s  Calle 6
    F6  80-100 s Av. Praxedis Guerrero

Los números del eje de tiempo del PDF venían corruptos por el OCR, así
que se usó como fuente de verdad la tabla de fases + el desglose
"20+20+10+10+20+20 = 100 s" que el propio documento entrega.

NUEVO EN ESTA VERSIÓN
----------------------
1) Reloj de 24 h: el ciclo de 100 s se repite continuamente a lo largo
   del día y se muestra la hora real (HH:MM:SS) además del segundo del
   ciclo.
2) Congestión vehicular simulada: cada acceso vehicular (Sombrerete
   ambos sentidos, Calle 6, Praxedis Guerrero, Metrobus) tiene una
   "cola" de vehículos esperando. Durante horas pico (7-9 AM y
   5-7 PM) la tasa de llegada de vehículos sube, así que las colas
   crecen más rápido de lo que el verde alcanza a descargarlas -> se ve
   congestionamiento real en pantalla. Fuera de hora pico las colas se
   vacían normalmente en cada verde.

IMPORTANTE: los documentos originales (PDF/mapa mental) NO traían datos
de aforo vehicular real. Las tasas de llegada/salida de vehículos son
valores simulados, razonables para ilustrar el fenómeno de
congestionamiento en hora pico, no conteos viales reales de Querétaro.
"""

import time
import os
import sys
import math
import random
import argparse

# ----------------------------------------------------------------------
# 1. Movimientos (cabezales semafóricos) del cruce
# ----------------------------------------------------------------------
MOVIMIENTOS = [
    ("somb_n_izq",   "Av. Sombrerete UP  (giro izq. protegido)"),
    ("somb_n_frente", "Av. Sombrerete UP  (de frente)"),
    ("somb_s_frente", "Av. Sombrerete DOWN (de frente)"),
    ("metrobus_n",    "Metrobus UP"),
    ("metrobus_s",    "Metrobus DOWN"),
    ("calle6",        "Calle 6"),
    ("praxedis",      "Av. Praxedis Guerrero"),
]

VERDE, AMARILLO, ROJO = "VERDE", "AMARILLO", "ROJO"
ICONO_LUZ = {VERDE: "🟢", AMARILLO: "🟡", ROJO: "🔴"}

CICLO_TOTAL = 100  # segundos por ciclo del semáforo

# ----------------------------------------------------------------------
# 2. Agenda de cada movimiento dentro de un ciclo de 100 s
# ----------------------------------------------------------------------
AGENDA = {
    "somb_n_izq":    [(0, 17, VERDE), (17, 20, AMARILLO)],
    "somb_n_frente": [(0, 37, VERDE), (37, 40, AMARILLO)],
    "somb_s_frente": [(20, 37, VERDE), (37, 40, AMARILLO)],
    "metrobus_n":    [(40, 47, VERDE), (47, 50, AMARILLO)],
    "metrobus_s":    [(50, 57, VERDE), (57, 60, AMARILLO)],
    "calle6":        [(60, 77, VERDE), (77, 80, AMARILLO)],
    "praxedis":      [(80, 97, VERDE), (97, 100, AMARILLO)],
}

FASES = [
    (0, 20, "F1 - Sombrerete UP con giro protegido"),
    (20, 40, "F2 - Sombrerete UP y DOWN con verde simultaneo"),
    (40, 50, "F3 - Metrobus UP"),
    (50, 60, "F4 - Metrobus DOWN"),
    (60, 80, "F5 - Calle 6"),
    (80, 100, "F6 - Av. Praxedis Guerrero"),
]

# ----------------------------------------------------------------------
# 3. Horas pico y parámetros de tráfico simulado por movimiento
#    valle/pico = vehículos por segundo que llegan (tasa de arribo)
#    servicio   = vehículos por segundo que la fase puede descargar en verde
#    capacidad  = cola "normal" de referencia, usada solo para clasificar
#                 el nivel de congestión (BAJO/MEDIO/ALTO/SATURADO)
# ----------------------------------------------------------------------
HORAS_PICO = [((7, 0), (9, 0)), ((17, 0), (19, 0))]  # 7-9 AM y 5-7 PM

PARAMS_TRAFICO = {
    "somb_n_izq":    {"valle": 0.05, "pico": 0.15, "servicio": 0.6, "capacidad": 12, "icono": "🚗"},
    "somb_n_frente": {"valle": 0.15, "pico": 0.45, "servicio": 0.9, "capacidad": 30, "icono": "🚗"},
    "somb_s_frente": {"valle": 0.12, "pico": 0.35, "servicio": 0.8, "capacidad": 25, "icono": "🚗"},
    "metrobus_n":    {"valle": 0.02, "pico": 0.04, "servicio": 1.0, "capacidad": 5,  "icono": "🚌"},
    "metrobus_s":    {"valle": 0.02, "pico": 0.04, "servicio": 1.0, "capacidad": 5,  "icono": "🚌"},
    "calle6":        {"valle": 0.05, "pico": 0.20, "servicio": 0.5, "capacidad": 15, "icono": "🚗"},
    "praxedis":      {"valle": 0.05, "pico": 0.20, "servicio": 0.5, "capacidad": 15, "icono": "🚗"},
}


def estado_de(movimiento: str, t: int) -> str:
    """Color del semáforo de `movimiento` en el segundo `t` del ciclo (0-99)."""
    for inicio, fin, color in AGENDA[movimiento]:
        if inicio <= t < fin:
            return color
    return ROJO


def fase_de(t: int) -> str:
    """Nombre de la fase (F1..F6) activa en el segundo `t` del ciclo."""
    for inicio, fin, nombre in FASES:
        if inicio <= t < fin:
            return nombre
    return FASES[-1][2]


def parsear_hora(cadena: str) -> int:
    """Convierte 'HH:MM' a segundos transcurridos desde la medianoche."""
    h, m = cadena.split(":")
    return (int(h) * 3600) + (int(m) * 60)


def hhmmss(segundo_del_dia: int) -> str:
    """Convierte segundos desde medianoche (puede pasar de 86400) a HH:MM:SS."""
    s = segundo_del_dia % 86400
    h, resto = divmod(s, 3600)
    m, s = divmod(resto, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def es_hora_pico(segundo_del_dia: int) -> bool:
    """True si el segundo del día (0-86399) cae en 7-9 AM o 5-7 PM."""
    s = segundo_del_dia % 86400
    h, m = divmod(s // 60, 60)
    minutos_del_dia = h * 60 + m
    for (h1, m1), (h2, m2) in HORAS_PICO:
        ini = h1 * 60 + m1
        fin = h2 * 60 + m2
        if ini <= minutos_del_dia < fin:
            return True
    return False


def muestra_poisson(lam: float) -> int:
    """Muestra un entero de una distribución Poisson(lam) sin dependencias
    externas (algoritmo de Knuth). Se usa para simular llegadas de
    vehículos por segundo de forma más realista que un simple azar 0/1."""
    if lam <= 0:
        return 0
    l = math.exp(-lam)
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= random.random()
        if p <= l:
            return k - 1


def nivel_congestion(cola: float, capacidad: float) -> str:
    """Clasifica el nivel de congestión de una cola respecto a su capacidad
    de referencia."""
    ratio = cola / capacidad if capacidad else 0
    if ratio < 0.3:
        return "BAJO"
    if ratio < 0.7:
        return "MEDIO"
    if ratio < 1.2:
        return "ALTO"
    return "SATURADO"


class SimulacionCruce:
    """Mantiene el estado de las colas vehiculares mientras corre el
    reloj de 24 h sobre el ciclo semafórico de 100 s."""

    def __init__(self, semilla: int = None):
        if semilla is not None:
            random.seed(semilla)
        self.colas = {clave: 0.0 for clave, _ in MOVIMIENTOS}

    def actualizar_colas(self, segundo_del_dia: int, t_ciclo: int):
        pico = es_hora_pico(segundo_del_dia)
        for clave, _ in MOVIMIENTOS:
            p = PARAMS_TRAFICO[clave]
            tasa = p["pico"] if pico else p["valle"]

            # Llegan vehículos nuevos a la cola
            self.colas[clave] += muestra_poisson(tasa)

            # Si el semáforo está en verde, la fase descarga vehículos
            if estado_de(clave, t_ciclo) == VERDE:
                self.colas[clave] = max(0.0, self.colas[clave] - p["servicio"])

            # Tope de simulación (más allá de esto se considera saturación
            # total / vehículos que buscan ruta alterna)
            self.colas[clave] = min(self.colas[clave], p["capacidad"] * 3)

    def imprimir_estado(self, segundo_del_dia: int, t_ciclo: int, limpiar: bool = True):
        if limpiar:
            os.system("cls" if os.name == "nt" else "clear")

        pico = es_hora_pico(segundo_del_dia)
        etiqueta_pico = "🔴 HORA PICO" if pico else "🟢 tráfico normal"

        print("=" * 68)
        print("  Cruce Av. Sombrerete - Calle 6 - Av. Praxedis Guerrero")
        print("=" * 68)
        print(f"  Hora:  {hhmmss(segundo_del_dia)}   ({etiqueta_pico})")
        print(f"  Ciclo semaforico:  segundo {t_ciclo:3d} / {CICLO_TOTAL}")
        print(f"  Fase activa:       {fase_de(t_ciclo)}")
        print("-" * 68)

        for clave, etiqueta in MOVIMIENTOS:
            color = estado_de(clave, t_ciclo)
            p = PARAMS_TRAFICO[clave]
            cola = self.colas[clave]
            nivel = nivel_congestion(cola, p["capacidad"])
            barra = p["icono"] * min(int(cola), 12)
            if cola > 12:
                barra += f"+{int(cola) - 12}"
            print(f"  {ICONO_LUZ[color]} {etiqueta:<38} {color:<9} "
                  f"cola:{int(cola):3d} [{nivel:<8}] {barra}")

        print("=" * 68)

    def ejecutar(self, hora_inicio: str = "06:50", duracion_min: float = 20,
                 velocidad: float = 0.05, limpiar_pantalla: bool = True):
        """
        hora_inicio:  'HH:MM' hora del día en la que arranca la simulación.
        duracion_min: cuántos minutos SIMULADOS se corren.
        velocidad:    segundos REALES de espera por cada segundo simulado
                      (1.0 = tiempo real; 0.05 = 20x más rápido, ideal
                      para ver rápidamente cómo sube la congestión).
        """
        inicio_seg = parsear_hora(hora_inicio)
        total_segundos = int(duracion_min * 60)

        try:
            for i in range(total_segundos):
                segundo_del_dia = inicio_seg + i
                t_ciclo = segundo_del_dia % CICLO_TOTAL
                self.actualizar_colas(segundo_del_dia, t_ciclo)
                self.imprimir_estado(segundo_del_dia, t_ciclo, limpiar=limpiar_pantalla)
                time.sleep(velocidad)
        except KeyboardInterrupt:
            print("\nSimulación detenida por el usuario.")
            sys.exit(0)


def resumen_fases():
    print("\nResumen del ciclo semafórico (100 s totales)")
    print("-" * 60)
    for inicio, fin, nombre in FASES:
        print(f"  {nombre:<45} {fin - inicio:>3d} s")
    print("-" * 60)
    print("Horas pico simuladas: 7:00-9:00 AM y 5:00-7:00 PM\n")


def parsear_argumentos():
    parser = argparse.ArgumentParser(
        description="Simulación del cruce Sombrerete - Calle 6 - Praxedis Guerrero"
    )
    parser.add_argument("--inicio", default="06:50",
                         help="Hora de inicio en formato HH:MM (24 h). Default: 06:50")
    parser.add_argument("--duracion", type=float, default=20,
                         help="Duración simulada en minutos. Default: 20")
    parser.add_argument("--velocidad", type=float, default=0.05,
                         help="Segundos reales por segundo simulado. Default: 0.05")
    parser.add_argument("--semilla", type=int, default=None,
                         help="Semilla aleatoria para resultados reproducibles")
    parser.add_argument("--sin-limpiar", action="store_true",
                         help="No limpiar pantalla en cada paso (útil para logs)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parsear_argumentos()
    resumen_fases()
    print(f"Iniciando simulación desde las {args.inicio}... (Ctrl+C para detener)\n")
    time.sleep(1.5)

    sim = SimulacionCruce(semilla=args.semilla)
    sim.ejecutar(
        hora_inicio=args.inicio,
        duracion_min=args.duracion,
        velocidad=args.velocidad,
        limpiar_pantalla=not args.sin_limpiar,
    )
