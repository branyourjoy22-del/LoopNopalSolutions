"""Simulación mesoscópica del cruce Sombrerete, Calle 6 y Praxedis Guerrero.

Geometría documentada por la imagen de referencia:
* Sombrerete: dos carriles generales por sentido.
* Corredor central: un carril exclusivo de Metrobús por sentido.
* Praxedis Guerrero: dos carriles de entrada y dos de salida.
* Calle 6: un carril de entrada y uno de salida.

El modelo representa únicamente movimientos rectos visibles. Los tiempos,
volúmenes y flujos de saturación son hipótesis de análisis hasta disponer de
aforos, programa del controlador, giros, peatones y mediciones de descarga.
"""

import argparse
import math
import os
import random
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VERDE, AMARILLO, ROJO = "VERDE", "AMARILLO", "ROJO"
ICONO_LUZ = {VERDE: "[V]", AMARILLO: "[A]", ROJO: "[R]"}

MOVIMIENTOS = [
    ("sb_general", "Sombrerete norte -> sur"),
    ("nb_general", "Sombrerete sur -> norte"),
    ("sb_bus", "Metrobús norte -> sur"),
    ("nb_bus", "Metrobús sur -> norte"),
    ("c6_eb", "Calle 6 poniente -> oriente"),
    ("prax_wb", "Praxedis oriente -> poniente"),
]

CONFIG_MOVIMIENTOS = {
    "sb_general": {"carriles": 2, "saturacion_carril": 1750, "grupo": "ns", "demanda_pico": 1250, "icono": "#"},
    "nb_general": {"carriles": 2, "saturacion_carril": 1750, "grupo": "ns", "demanda_pico": 1150, "icono": "#"},
    "sb_bus": {"carriles": 1, "saturacion_carril": 900, "grupo": "bus", "demanda_pico": 48, "icono": "B"},
    "nb_bus": {"carriles": 1, "saturacion_carril": 900, "grupo": "bus", "demanda_pico": 48, "icono": "B"},
    "c6_eb": {"carriles": 1, "saturacion_carril": 1750, "grupo": "ew", "demanda_pico": 420, "icono": "#"},
    "prax_wb": {"carriles": 2, "saturacion_carril": 1750, "grupo": "ew", "demanda_pico": 1350, "icono": "#"},
}

ESCENARIOS = {
    "valle": {"sb_general": 500, "nb_general": 450, "sb_bus": 20, "nb_bus": 20, "c6_eb": 180, "prax_wb": 650},
    "referencia": {"sb_general": 850, "nb_general": 800, "sb_bus": 32, "nb_bus": 32, "c6_eb": 300, "prax_wb": 950},
    "pico": {"sb_general": 1250, "nb_general": 1150, "sb_bus": 48, "nb_bus": 48, "c6_eb": 420, "prax_wb": 1350},
}

FACTORES_24H = (
    0.22, 0.17, 0.13, 0.11, 0.14, 0.27, 0.55, 0.88,
    1.00, 0.78, 0.62, 0.56, 0.61, 0.66, 0.63, 0.72,
    0.86, 1.02, 0.96, 0.79, 0.62, 0.48, 0.36, 0.28,
)
HORAS_PICO = [((7, 0), (9, 0)), ((17, 0), (19, 0))]

PLAN_BASE = {"nombre": "base", "ciclo": 100, "verdes": {"ns": 35, "bus": 12, "ew": 37}}
CICLO_TOTAL = PLAN_BASE["ciclo"]


def construir_agenda(plan):
    """Construye agenda y fases con amarillos/despejes fijos."""
    verdes = plan["verdes"]
    bloques = [
        ("ns", VERDE, verdes["ns"], "Sombrerete general - verde"),
        ("ns", AMARILLO, 4, "Amarillo Sombrerete"),
        (None, ROJO, 2, "Todo rojo - despeje"),
        ("bus", VERDE, verdes["bus"], "Metrobús - ambos sentidos"),
        ("bus", AMARILLO, 3, "Amarillo Metrobús"),
        (None, ROJO, 2, "Todo rojo - despeje"),
        ("ew", VERDE, verdes["ew"], "Calle 6 y Praxedis - verde"),
        ("ew", AMARILLO, 3, "Amarillo oriente-poniente"),
        (None, ROJO, 2, "Todo rojo - reinicio"),
    ]
    agenda = {clave: [] for clave, _ in MOVIMIENTOS}
    fases = []
    inicio = 0
    for grupo, color, duracion, nombre in bloques:
        fin = inicio + duracion
        fases.append((inicio, fin, nombre))
        if grupo is not None:
            for clave, _ in MOVIMIENTOS:
                if CONFIG_MOVIMIENTOS[clave]["grupo"] == grupo:
                    agenda[clave].append((inicio, fin, color))
        inicio = fin
    if inicio != plan["ciclo"]:
        raise ValueError(f"La agenda suma {inicio} s y el plan declara {plan['ciclo']} s")
    return agenda, fases


AGENDA, FASES = construir_agenda(PLAN_BASE)


def copiar_demandas(origen):
    return {clave: max(0.0, float(origen[clave])) for clave, _ in MOVIMIENTOS}


def crear_plan_calculado(demandas):
    """Reparte verde por el flujo crítico de cada etapa.

    El ciclo se acota entre 70 y 150 s. Metrobús conserva 10 s mínimos;
    el verde restante se reparte entre Sombrerete y el eje este-oeste.
    """
    demandas = copiar_demandas(demandas)
    relaciones = {}
    for grupo in ("ns", "bus", "ew"):
        relaciones[grupo] = max(
            demandas[clave] / (cfg["carriles"] * cfg["saturacion_carril"])
            for clave, cfg in CONFIG_MOVIMIENTOS.items() if cfg["grupo"] == grupo
        )
    suma = sum(relaciones.values())
    ciclo = round(min(150, max(70, 29 / max(0.05, 1 - suma))))
    verde_efectivo = ciclo - 16
    verde_bus = 10
    disponible = verde_efectivo - verde_bus
    peso_general = relaciones["ns"] + relaciones["ew"]
    verde_ns = round(disponible * relaciones["ns"] / max(0.001, peso_general))
    verde_ew = verde_efectivo - verde_bus - verde_ns
    return {"nombre": "calculado", "ciclo": ciclo, "verdes": {"ns": verde_ns, "bus": verde_bus, "ew": verde_ew}}


def estado_en_agenda(agenda, movimiento, t):
    for inicio, fin, color in agenda[movimiento]:
        if inicio <= t < fin:
            return color
    return ROJO


def estado_de(movimiento, t):
    """Estado del movimiento para el plan base."""
    return estado_en_agenda(AGENDA, movimiento, t % CICLO_TOTAL)


def fase_en_lista(fases, t):
    for inicio, fin, nombre in fases:
        if inicio <= t < fin:
            return nombre
    return fases[-1][2]


def fase_de(t):
    """Fase activa para el plan base."""
    return fase_en_lista(FASES, t % CICLO_TOTAL)


def parsear_hora(cadena):
    h, m = cadena.split(":")
    if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
        raise ValueError("La hora debe usar HH:MM entre 00:00 y 23:59")
    return int(h) * 3600 + int(m) * 60


def hhmmss(segundo_del_dia):
    s = int(segundo_del_dia) % 86400
    h, resto = divmod(s, 3600)
    m, s = divmod(resto, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def es_hora_pico(segundo_del_dia):
    minuto = (int(segundo_del_dia) % 86400) // 60
    return any(h1 * 60 + m1 <= minuto < h2 * 60 + m2 for (h1, m1), (h2, m2) in HORAS_PICO)


def factor_horario(segundo_del_dia):
    hora = (int(segundo_del_dia) % 86400) // 3600
    return FACTORES_24H[hora]


def demandas_en(segundo_del_dia, escenario="diario"):
    if escenario in ESCENARIOS:
        return copiar_demandas(ESCENARIOS[escenario])
    factor = factor_horario(segundo_del_dia)
    return {clave: cfg["demanda_pico"] * factor for clave, cfg in CONFIG_MOVIMIENTOS.items()}


def muestra_poisson(lam, rng=None):
    """Muestra Poisson mediante Knuth usando un generador inyectable."""
    if lam <= 0:
        return 0
    rng = rng or random
    limite = math.exp(-lam)
    producto = 1.0
    k = 0
    while producto > limite:
        k += 1
        producto *= rng.random()
    return k - 1


def capacidad_efectiva(movimiento, plan=PLAN_BASE):
    cfg = CONFIG_MOVIMIENTOS[movimiento]
    verde = plan["verdes"][cfg["grupo"]]
    return cfg["carriles"] * cfg["saturacion_carril"] * verde / plan["ciclo"]


def nivel_congestion(grado_x, cola=None):
    """Clasifica por grado de saturación, no por un tope arbitrario de cola."""
    if grado_x < 0.60:
        return "ESTABLE"
    if grado_x < 0.85:
        return "MEDIO"
    if grado_x < 1.00:
        return "ALTO"
    return "SOBRESAT."


class SimulacionCruce:
    """Colas discretas con llegadas Poisson y descarga por flujo de saturación."""

    def __init__(self, semilla=42, plan=None, escenario="diario"):
        self.escenario = escenario
        demanda_objetivo = ESCENARIOS["pico"] if escenario == "diario" else ESCENARIOS[escenario]
        self.plan = plan or PLAN_BASE
        if self.plan == "calculado":
            self.plan = crear_plan_calculado(demanda_objetivo)
        self.agenda, self.fases = construir_agenda(self.plan)
        self.rng = random.Random(semilla)
        self.colas = {clave: 0 for clave, _ in MOVIMIENTOS}
        self.credito_servicio = {clave: 0.0 for clave, _ in MOVIMIENTOS}
        self.llegadas = {clave: 0 for clave, _ in MOVIMIENTOS}
        self.salidas = {clave: 0 for clave, _ in MOVIMIENTOS}
        self.cola_maxima = {clave: 0 for clave, _ in MOVIMIENTOS}
        self.vehiculos_segundo = 0.0
        self.pasos = 0

    def estado_de(self, movimiento, t_ciclo):
        return estado_en_agenda(self.agenda, movimiento, t_ciclo % self.plan["ciclo"])

    def fase_de(self, t_ciclo):
        return fase_en_lista(self.fases, t_ciclo % self.plan["ciclo"])

    def grado_x(self, movimiento, segundo_del_dia):
        demanda = demandas_en(segundo_del_dia, self.escenario)[movimiento]
        return demanda / capacidad_efectiva(movimiento, self.plan)

    def actualizar_colas(self, segundo_del_dia, t_ciclo):
        demandas = demandas_en(segundo_del_dia, self.escenario)
        for clave, _ in MOVIMIENTOS:
            cfg = CONFIG_MOVIMIENTOS[clave]
            nuevos = muestra_poisson(demandas[clave] / 3600, self.rng)
            self.colas[clave] += nuevos
            self.llegadas[clave] += nuevos

            if self.estado_de(clave, t_ciclo) == VERDE and self.colas[clave] > 0:
                self.credito_servicio[clave] += cfg["carriles"] * cfg["saturacion_carril"] / 3600
                posibles = int(self.credito_servicio[clave])
                servidos = min(posibles, self.colas[clave])
                self.colas[clave] -= servidos
                self.credito_servicio[clave] -= servidos
                self.salidas[clave] += servidos
            else:
                self.credito_servicio[clave] = 0.0
            self.cola_maxima[clave] = max(self.cola_maxima[clave], self.colas[clave])

        self.vehiculos_segundo += sum(self.colas.values())
        self.pasos += 1

    def metricas(self):
        salidas = sum(self.salidas.values())
        return {
            "llegadas": sum(self.llegadas.values()),
            "salidas": salidas,
            "cola_actual": sum(self.colas.values()),
            "cola_promedio": self.vehiculos_segundo / max(1, self.pasos),
            "cola_maxima": sum(self.cola_maxima.values()),
            "demora_detenida": self.vehiculos_segundo / max(1, salidas),
        }

    def imprimir_estado(self, segundo_del_dia, t_ciclo, limpiar=True):
        if limpiar:
            os.system("cls" if os.name == "nt" else "clear")
        etiqueta = "HORA PICO" if es_hora_pico(segundo_del_dia) else "perfil normal"
        print("=" * 82)
        print("  Cruce Sombrerete - Calle 6 - Praxedis Guerrero")
        print("=" * 82)
        print(f"  Hora: {hhmmss(segundo_del_dia)} | {etiqueta} | plan {self.plan['nombre']}")
        print(f"  Ciclo: segundo {t_ciclo:3d}/{self.plan['ciclo']} | {self.fase_de(t_ciclo)}")
        print("-" * 82)
        for clave, etiqueta_mov in MOVIMIENTOS:
            color = self.estado_de(clave, t_ciclo)
            grado = self.grado_x(clave, segundo_del_dia)
            nivel = nivel_congestion(grado)
            cola = self.colas[clave]
            barra = CONFIG_MOVIMIENTOS[clave]["icono"] * min(cola, 10)
            if cola > 10:
                barra += f"+{cola - 10}"
            print(f"  {ICONO_LUZ[color]} {etiqueta_mov:<35} {color:<9} cola:{cola:4d} x:{grado:4.2f} [{nivel:<9}] {barra}")
        print("=" * 82)
        print("  Supuestos: sin giros, peatones, derrame de cola ni bloqueo aguas abajo.")

    def ejecutar(self, hora_inicio="06:50", duracion_min=20, velocidad=0.05, limpiar_pantalla=True):
        inicio_seg = parsear_hora(hora_inicio)
        try:
            for i in range(int(duracion_min * 60)):
                segundo_del_dia = inicio_seg + i
                t_ciclo = segundo_del_dia % self.plan["ciclo"]
                self.actualizar_colas(segundo_del_dia, t_ciclo)
                self.imprimir_estado(segundo_del_dia, t_ciclo, limpiar=limpiar_pantalla)
                if velocidad > 0:
                    time.sleep(velocidad)
        except KeyboardInterrupt:
            print("\nSimulación detenida por el usuario.")
            sys.exit(0)
        resumen = self.metricas()
        print(f"\nResumen: cola media {resumen['cola_promedio']:.1f} veh | "
              f"demora detenida {resumen['demora_detenida']:.1f} s/veh | "
              f"cola final {resumen['cola_actual']} veh")


def resumen_fases(plan=PLAN_BASE):
    _, fases = construir_agenda(plan)
    print(f"\nPlan {plan['nombre']} | ciclo {plan['ciclo']} s")
    print("-" * 64)
    for numero, (inicio, fin, nombre) in enumerate(fases, 1):
        print(f"  {numero}. {nombre:<38} {inicio:>3}-{fin:<3} s")
    print("-" * 64)


def parsear_argumentos():
    parser = argparse.ArgumentParser(description="Simulación del cruce Sombrerete - Calle 6 - Praxedis")
    parser.add_argument("--inicio", default="06:50", help="Hora inicial HH:MM. Default: 06:50")
    parser.add_argument("--duracion", type=float, default=20, help="Minutos simulados. Default: 20")
    parser.add_argument("--velocidad", type=float, default=0.05, help="Segundos reales por segundo simulado")
    parser.add_argument("--semilla", type=int, default=42, help="Semilla reproducible. Default: 42")
    parser.add_argument("--escenario", choices=("diario", "valle", "referencia", "pico"), default="diario")
    parser.add_argument("--plan", choices=("base", "calculado"), default="base")
    parser.add_argument("--sin-limpiar", action="store_true", help="Conservar cada paso en la terminal")
    return parser.parse_args()


if __name__ == "__main__":
    args = parsear_argumentos()
    plan_elegido = PLAN_BASE if args.plan == "base" else "calculado"
    sim = SimulacionCruce(semilla=args.semilla, plan=plan_elegido, escenario=args.escenario)
    resumen_fases(sim.plan)
    print("Iniciando simulación. Ctrl+C para detener.\n")
    sim.ejecutar(args.inicio, args.duracion, args.velocidad, not args.sin_limpiar)
