"""Simulacion mesoscopica del cruce Sombrerete, Calle 6 y Praxedis Guerrero.

La geometria sigue la imagen de referencia proporcionada por el usuario. La
secuencia base sigue el programa semaforico adjunto, con un ciclo de 100 s:

    F1  0-20 s    Sombrerete sur -> norte y giro izquierdo protegido
    F2 20-40 s    Sombrerete en ambos sentidos, movimientos de frente
    F3 40-50 s    Metrobus sur -> norte
    F4 50-60 s    Metrobus norte -> sur
    F5 60-80 s    Calle 6 poniente -> oriente
    F6 80-100 s   Praxedis Guerrero oriente -> poniente

Cada fase reserva sus ultimos 3 s para amarillo, tal como indica el archivo
fuente. Los volumenes y flujos de saturacion siguen siendo hipotesis hasta
contar con aforos, programa del controlador y mediciones de descarga en campo.
El giro protegido se conserva en la agenda, pero no recibe demanda propia
porque la imagen no documenta un carril ni un aforo separado para ese giro.
"""

import argparse
import math
import os
import random
import statistics
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VERDE, AMARILLO, ROJO = "VERDE", "AMARILLO", "ROJO"
ICONO_LUZ = {VERDE: "[V]", AMARILLO: "[A]", ROJO: "[R]"}

MOVIMIENTOS = [
    ("somb_n_izq", "Sombrerete sur -> norte (giro izq. protegido)"),
    ("somb_n_frente", "Sombrerete sur -> norte (de frente)"),
    ("somb_s_frente", "Sombrerete norte -> sur (de frente)"),
    ("metrobus_n", "Metrobús sur -> norte"),
    ("metrobus_s", "Metrobús norte -> sur"),
    ("calle6", "Calle 6 poniente -> oriente"),
    ("praxedis", "Praxedis oriente -> poniente"),
]

CONFIG_MOVIMIENTOS = {
    "somb_n_izq": {"carriles": 1, "saturacion_carril": 1750, "demanda_pico": 0, "icono": "<"},
    "somb_n_frente": {"carriles": 2, "saturacion_carril": 1750, "demanda_pico": 1150, "icono": "#"},
    "somb_s_frente": {"carriles": 2, "saturacion_carril": 1750, "demanda_pico": 1250, "icono": "#"},
    "metrobus_n": {"carriles": 1, "saturacion_carril": 900, "demanda_pico": 48, "icono": "B"},
    "metrobus_s": {"carriles": 1, "saturacion_carril": 900, "demanda_pico": 48, "icono": "B"},
    "calle6": {"carriles": 1, "saturacion_carril": 1750, "demanda_pico": 420, "icono": "#"},
    "praxedis": {"carriles": 2, "saturacion_carril": 1750, "demanda_pico": 1350, "icono": "#"},
}

ESCENARIOS = {
    "valle": {
        "somb_n_izq": 0, "somb_n_frente": 450, "somb_s_frente": 500,
        "metrobus_n": 20, "metrobus_s": 20, "calle6": 180, "praxedis": 650,
    },
    "referencia": {
        "somb_n_izq": 0, "somb_n_frente": 800, "somb_s_frente": 850,
        "metrobus_n": 32, "metrobus_s": 32, "calle6": 300, "praxedis": 950,
    },
    "pico": {
        "somb_n_izq": 0, "somb_n_frente": 1150, "somb_s_frente": 1250,
        "metrobus_n": 48, "metrobus_s": 48, "calle6": 420, "praxedis": 1350,
    },
}

FACTORES_24H = (
    0.22, 0.17, 0.13, 0.11, 0.14, 0.27, 0.55, 0.88,
    1.00, 0.78, 0.62, 0.56, 0.61, 0.66, 0.63, 0.72,
    0.86, 1.02, 0.96, 0.79, 0.62, 0.48, 0.36, 0.28,
)
HORAS_PICO = [((7, 0), (9, 0)), ((17, 0), (19, 0))]

NOMBRES_FASES = (
    "F1 - Sombrerete sur -> norte y giro protegido",
    "F2 - Sombrerete ambos sentidos de frente",
    "F3 - Metrobús sur -> norte",
    "F4 - Metrobús norte -> sur",
    "F5 - Calle 6",
    "F6 - Praxedis Guerrero",
)
DURACIONES_BASE = (20, 20, 10, 10, 20, 20)
MINIMOS_OPTIMIZACION = (8, 10, 8, 8, 10, 10)
SEGUNDOS_AMARILLO = 3
PLAN_BASE = {"nombre": "base actual", "ciclo": 100, "duraciones": DURACIONES_BASE}
CICLO_TOTAL = PLAN_BASE["ciclo"]


def copiar_demandas(origen):
    return {clave: max(0.0, float(origen.get(clave, 0))) for clave, _ in MOVIMIENTOS}


def construir_agenda(plan):
    """Construye la agenda exacta a partir de las seis fases ordenadas."""
    duraciones = tuple(int(valor) for valor in plan["duraciones"])
    if len(duraciones) != 6 or any(valor <= SEGUNDOS_AMARILLO for valor in duraciones):
        raise ValueError("El plan debe contener seis fases mayores a 3 s")
    if sum(duraciones) != int(plan["ciclo"]):
        raise ValueError("Las seis fases deben sumar exactamente el ciclo declarado")

    limites = [0]
    for duracion in duraciones:
        limites.append(limites[-1] + duracion)
    fases = [(limites[i], limites[i + 1], NOMBRES_FASES[i]) for i in range(6)]

    agenda = {clave: [] for clave, _ in MOVIMIENTOS}
    f1_fin, f2_fin, f3_fin, f4_fin, f5_fin, f6_fin = limites[1:]
    agenda["somb_n_izq"] = [(0, f1_fin - SEGUNDOS_AMARILLO, VERDE), (f1_fin - SEGUNDOS_AMARILLO, f1_fin, AMARILLO)]
    agenda["somb_n_frente"] = [(0, f2_fin - SEGUNDOS_AMARILLO, VERDE), (f2_fin - SEGUNDOS_AMARILLO, f2_fin, AMARILLO)]
    agenda["somb_s_frente"] = [(f1_fin, f2_fin - SEGUNDOS_AMARILLO, VERDE), (f2_fin - SEGUNDOS_AMARILLO, f2_fin, AMARILLO)]
    agenda["metrobus_n"] = [(f2_fin, f3_fin - SEGUNDOS_AMARILLO, VERDE), (f3_fin - SEGUNDOS_AMARILLO, f3_fin, AMARILLO)]
    agenda["metrobus_s"] = [(f3_fin, f4_fin - SEGUNDOS_AMARILLO, VERDE), (f4_fin - SEGUNDOS_AMARILLO, f4_fin, AMARILLO)]
    agenda["calle6"] = [(f4_fin, f5_fin - SEGUNDOS_AMARILLO, VERDE), (f5_fin - SEGUNDOS_AMARILLO, f5_fin, AMARILLO)]
    agenda["praxedis"] = [(f5_fin, f6_fin - SEGUNDOS_AMARILLO, VERDE), (f6_fin - SEGUNDOS_AMARILLO, f6_fin, AMARILLO)]
    return agenda, fases


AGENDA, FASES = construir_agenda(PLAN_BASE)


def segundos_verde(movimiento, plan=PLAN_BASE):
    agenda, _ = construir_agenda(plan)
    return sum(fin - inicio for inicio, fin, color in agenda[movimiento] if color == VERDE)


def capacidad_efectiva(movimiento, plan=PLAN_BASE):
    cfg = CONFIG_MOVIMIENTOS[movimiento]
    return cfg["carriles"] * cfg["saturacion_carril"] * segundos_verde(movimiento, plan) / plan["ciclo"]


def grados_saturacion(plan, demandas):
    demandas = copiar_demandas(demandas)
    return {
        clave: demandas[clave] / max(0.001, capacidad_efectiva(clave, plan))
        for clave, _ in MOVIMIENTOS if demandas[clave] > 0
    }


def puntuar_plan(plan, demandas):
    grados = tuple(grados_saturacion(plan, demandas).values())
    return max(grados, default=0.0), sum(valor * valor for valor in grados)


def crear_plan_calculado(demandas):
    """Optimiza reparto conservando ciclo, orden y seis fases reales."""
    demandas = copiar_demandas(demandas)
    duraciones = list(MINIMOS_OPTIMIZACION)
    while sum(duraciones) < CICLO_TOTAL:
        candidatos = []
        for indice in range(6):
            propuesta = duraciones.copy()
            propuesta[indice] += 1
            plan = {"nombre": "optimizado", "ciclo": sum(propuesta), "duraciones": tuple(propuesta)}
            candidatos.append((puntuar_plan(plan, demandas), indice))
        _, mejor_indice = min(candidatos)
        duraciones[mejor_indice] += 1
    return {"nombre": "optimizado", "ciclo": CICLO_TOTAL, "duraciones": tuple(duraciones)}


def estado_en_agenda(agenda, movimiento, t):
    for inicio, fin, color in agenda[movimiento]:
        if inicio <= t < fin:
            return color
    return ROJO


def estado_de(movimiento, t):
    return estado_en_agenda(AGENDA, movimiento, t % CICLO_TOTAL)


def fase_en_lista(fases, t):
    for inicio, fin, nombre in fases:
        if inicio <= t < fin:
            return nombre
    return fases[-1][2]


def fase_de(t):
    return fase_en_lista(FASES, t % CICLO_TOTAL)


def parsear_hora(cadena):
    h, m = cadena.split(":")
    if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
        raise ValueError("La hora debe usar HH:MM entre 00:00 y 23:59")
    return int(h) * 3600 + int(m) * 60


def hhmmss(segundo_del_dia):
    segundo = int(segundo_del_dia) % 86400
    h, resto = divmod(segundo, 3600)
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


def percentil(valores, proporcion):
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    posicion = (len(ordenados) - 1) * proporcion
    inferior = math.floor(posicion)
    superior = math.ceil(posicion)
    if inferior == superior:
        return float(ordenados[inferior])
    fraccion = posicion - inferior
    return ordenados[inferior] * (1 - fraccion) + ordenados[superior] * fraccion


def nivel_congestion(grado_x, cola=None):
    if grado_x < 0.60:
        return "ESTABLE"
    if grado_x < 0.85:
        return "MEDIO"
    if grado_x < 1.00:
        return "ALTO"
    return "SOBRESAT."


class SimulacionCruce:
    """Colas discretas con llegadas Poisson y descarga por saturacion."""

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
        self.reiniciar_metricas()

    def reiniciar_metricas(self):
        self.llegadas = {clave: 0 for clave, _ in MOVIMIENTOS}
        self.salidas = {clave: 0 for clave, _ in MOVIMIENTOS}
        self.cola_maxima = {clave: self.colas.get(clave, 0) for clave, _ in MOVIMIENTOS}
        self.vehiculos_segundo = 0.0
        self.pasos = 0
        self.historial_cola_total = []

    def estado_de(self, movimiento, t_ciclo):
        return estado_en_agenda(self.agenda, movimiento, t_ciclo % self.plan["ciclo"])

    def fase_de(self, t_ciclo):
        return fase_en_lista(self.fases, t_ciclo % self.plan["ciclo"])

    def grado_x(self, movimiento, segundo_del_dia):
        demanda = demandas_en(segundo_del_dia, self.escenario)[movimiento]
        return demanda / max(0.001, capacidad_efectiva(movimiento, self.plan))

    def actualizar_colas(self, segundo_del_dia, t_ciclo, registrar=True):
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
        if registrar:
            cola_total = sum(self.colas.values())
            self.vehiculos_segundo += cola_total
            self.pasos += 1
            self.historial_cola_total.append(cola_total)

    def metricas(self):
        salidas = sum(self.salidas.values())
        return {
            "llegadas": sum(self.llegadas.values()),
            "salidas": salidas,
            "cola_actual": sum(self.colas.values()),
            "cola_promedio": self.vehiculos_segundo / max(1, self.pasos),
            "cola_p95": percentil(self.historial_cola_total, 0.95),
            "cola_maxima": max(self.historial_cola_total, default=sum(self.colas.values())),
            "demora_detenida": self.vehiculos_segundo / max(1, salidas),
        }

    def imprimir_estado(self, segundo_del_dia, t_ciclo, limpiar=True):
        if limpiar:
            os.system("cls" if os.name == "nt" else "clear")
        etiqueta = "HORA PICO" if es_hora_pico(segundo_del_dia) else "perfil normal"
        print("=" * 88)
        print("  Cruce Sombrerete - Calle 6 - Praxedis Guerrero")
        print("=" * 88)
        print(f"  Hora: {hhmmss(segundo_del_dia)} | {etiqueta} | plan {self.plan['nombre']}")
        print(f"  Ciclo: segundo {t_ciclo:3d}/{self.plan['ciclo']} | {self.fase_de(t_ciclo)}")
        print("-" * 88)
        for clave, etiqueta_mov in MOVIMIENTOS:
            color = self.estado_de(clave, t_ciclo)
            grado = self.grado_x(clave, segundo_del_dia)
            nivel = nivel_congestion(grado)
            cola = self.colas[clave]
            barra = CONFIG_MOVIMIENTOS[clave]["icono"] * min(cola, 10)
            if cola > 10:
                barra += f"+{cola - 10}"
            print(f"  {ICONO_LUZ[color]} {etiqueta_mov:<45} {color:<9} cola:{cola:4d} x:{grado:4.2f} [{nivel:<9}] {barra}")
        print("=" * 88)
        print("  Giro protegido sin demanda separada; volumenes restantes son supuestos.")

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
            print("\nSimulacion detenida por el usuario.")
            sys.exit(0)
        resumen = self.metricas()
        print(f"\nResumen: cola media {resumen['cola_promedio']:.1f} veh | "
              f"demora detenida {resumen['demora_detenida']:.1f} s/veh | "
              f"cola final {resumen['cola_actual']} veh")


def simular_periodo(escenario, plan, semilla, inicio_seg, calentamiento_seg, medicion_seg):
    sim = SimulacionCruce(semilla=semilla, plan=plan, escenario=escenario)
    for paso in range(calentamiento_seg):
        segundo = inicio_seg + paso
        sim.actualizar_colas(segundo, segundo % sim.plan["ciclo"], registrar=False)
    sim.reiniciar_metricas()
    for paso in range(calentamiento_seg, calentamiento_seg + medicion_seg):
        segundo = inicio_seg + paso
        sim.actualizar_colas(segundo, segundo % sim.plan["ciclo"])
    return sim.metricas()


def resumir_corridas(escenario, plan, corridas=20, calentamiento_seg=900, medicion_seg=3600):
    resultados = [
        simular_periodo(escenario, plan, 1000 + semilla, 0, calentamiento_seg, medicion_seg)
        for semilla in range(corridas)
    ]
    resumen = {}
    for metrica in ("cola_promedio", "demora_detenida", "cola_p95"):
        valores = [resultado[metrica] for resultado in resultados]
        resumen[metrica] = statistics.fmean(valores)
        resumen[f"{metrica}_p10"] = percentil(valores, 0.10)
        resumen[f"{metrica}_p90"] = percentil(valores, 0.90)
    return resumen


def resumen_comparativo(escenario, corridas=20):
    demandas = ESCENARIOS[escenario]
    optimizado = crear_plan_calculado(demandas)
    return {
        "plan_base": PLAN_BASE,
        "plan_optimizado": optimizado,
        "base": resumir_corridas(escenario, PLAN_BASE, corridas=corridas),
        "optimizado": resumir_corridas(escenario, optimizado, corridas=corridas),
        "grados_base": grados_saturacion(PLAN_BASE, demandas),
        "grados_optimizado": grados_saturacion(optimizado, demandas),
    }


def resumen_hora(hora, corridas=6):
    inicio = int(hora) * 3600
    resultados = [
        simular_periodo("diario", PLAN_BASE, 2000 + semilla, inicio, 600, 1800)
        for semilla in range(corridas)
    ]
    demandas = demandas_en(inicio, "diario")
    return {
        "demanda_total": sum(demandas.values()),
        "cola_promedio": statistics.fmean(r["cola_promedio"] for r in resultados),
        "cola_p95": statistics.fmean(r["cola_p95"] for r in resultados),
        "demora_detenida": statistics.fmean(r["demora_detenida"] for r in resultados),
        "max_x": max(grados_saturacion(PLAN_BASE, demandas).values()),
    }


def resumen_fases(plan=PLAN_BASE):
    _, fases = construir_agenda(plan)
    print(f"\nPlan {plan['nombre']} | ciclo {plan['ciclo']} s")
    print("-" * 72)
    for inicio, fin, nombre in fases:
        print(f"  {nombre:<52} {inicio:>3}-{fin:<3} s")
    print("-" * 72)


def parsear_argumentos():
    parser = argparse.ArgumentParser(description="Simulacion del cruce Sombrerete - Calle 6 - Praxedis")
    parser.add_argument("--inicio", default="06:50", help="Hora inicial HH:MM. Default: 06:50")
    parser.add_argument("--duracion", type=float, default=20, help="Minutos simulados. Default: 20")
    parser.add_argument("--velocidad", type=float, default=0.05, help="Segundos reales por segundo simulado")
    parser.add_argument("--semilla", type=int, default=42, help="Semilla reproducible. Default: 42")
    parser.add_argument("--escenario", choices=("diario", "valle", "referencia", "pico"), default="diario")
    parser.add_argument("--plan", choices=("base", "optimizado"), default="base")
    parser.add_argument("--sin-limpiar", action="store_true", help="Conservar cada paso en la terminal")
    return parser.parse_args()


if __name__ == "__main__":
    args = parsear_argumentos()
    plan_elegido = PLAN_BASE if args.plan == "base" else "calculado"
    sim = SimulacionCruce(semilla=args.semilla, plan=plan_elegido, escenario=args.escenario)
    resumen_fases(sim.plan)
    print("Iniciando simulacion. Ctrl+C para detener.\n")
    sim.ejecutar(args.inicio, args.duracion, args.velocidad, not args.sin_limpiar)
