"""
Visualización gráfica de la geometría, colas y ciclo del cruce
Sombrerete - Calle 6 - Praxedis Guerrero (Querétaro).

Reutiliza el motor de simulación de semaforo_sombrerete.py (misma AGENDA,
mismos parámetros de tráfico) para que las gráficas y la simulación de
consola nunca queden desincronizadas.

Genera una figura con tres paneles: geometría documentada, colas durante
24 horas y diagrama de tiempos construido desde el mismo motor.

Uso:
    python3 graficar_simulacion.py
    python3 graficar_simulacion.py --semilla 7 --muestreo 30
"""

import argparse
import importlib.util
import os

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Falta matplotlib. Instala la dependencia con: pip install matplotlib"
    ) from exc

# ------------------------------------------------------------------
# Importar el motor de simulación desde semaforo_sombrerete.py
# (debe estar en la misma carpeta que este script)
# ------------------------------------------------------------------
RUTA_BASE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "semaforo_sombrerete", os.path.join(RUTA_BASE, "semaforo_sombrerete.py")
)
sem = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sem)

# Paleta de colores (accesible para daltonismo: azul/naranja como par principal)
COLOR_SOMBRERETE = "#4C72B0"   # azul
COLOR_CALLE6 = "#DD8452"       # naranja
COLOR_PRAXEDIS = "#C44E52"     # rojo ladrillo
COLOR_METROBUS = "#55A868"     # verde
COLOR_PICO = "#808080"

COLOR_LUZ = {sem.VERDE: "#2E7D32", sem.AMARILLO: "#F9A825", sem.ROJO: "#E0E0E0"}


def simular_24h(semilla=None, muestreo_seg=30):
    """
    Corre la simulación de colas durante 24 h (rápido, sin pantalla ni
    sleep) y devuelve series de tiempo agregadas por grupo de movimiento.
    """
    sim = sem.SimulacionCruce(semilla=semilla)

    horas = []
    serie = {
        "Sombrerete general (4 carriles)": [],
        "Calle 6 (1 entrada)": [],
        "Praxedis Guerrero (2 entradas)": [],
        "Metrobús (2 carriles exclusivos)": [],
    }

    for s in range(0, 86400):
        t_ciclo = s % sem.CICLO_TOTAL
        sim.actualizar_colas(s, t_ciclo)

        if s % muestreo_seg == 0:
            horas.append(s / 3600.0)
            c = sim.colas
            serie["Sombrerete general (4 carriles)"].append(c["somb_n_frente"] + c["somb_s_frente"])
            serie["Calle 6 (1 entrada)"].append(c["calle6"])
            serie["Praxedis Guerrero (2 entradas)"].append(c["praxedis"])
            serie["Metrobús (2 carriles exclusivos)"].append(c["metrobus_n"] + c["metrobus_s"])

    return horas, serie


def graficar_congestion(ax, horas, serie):
    colores = {
        "Sombrerete general (4 carriles)": COLOR_SOMBRERETE,
        "Calle 6 (1 entrada)": COLOR_CALLE6,
        "Praxedis Guerrero (2 entradas)": COLOR_PRAXEDIS,
        "Metrobús (2 carriles exclusivos)": COLOR_METROBUS,
    }
    estilos = {
        "Sombrerete general (4 carriles)": "-",
        "Calle 6 (1 entrada)": "--",
        "Praxedis Guerrero (2 entradas)": "-.",
        "Metrobús (2 carriles exclusivos)": ":",
    }

    for nombre, valores in serie.items():
        ax.plot(horas, valores, label=nombre, color=colores[nombre],
                 linestyle=estilos[nombre], linewidth=1.8)

    # Resaltar horas pico
    for (h1, m1), (h2, m2) in sem.HORAS_PICO:
        ax.axvspan(h1 + m1 / 60, h2 + m2 / 60, color=COLOR_PICO, alpha=0.15)

    # Una sola entrada de leyenda para las franjas de hora pico
    parche_pico = mpatches.Patch(color=COLOR_PICO, alpha=0.15, label="Hora pico (7-9 AM / 5-7 PM)")
    handles, labels = ax.get_legend_handles_labels()
    handles.append(parche_pico)
    labels.append("Hora pico (7-9 AM / 5-7 PM)")

    ax.set_title("Colas modeladas durante 24 horas", fontweight="bold")
    ax.set_xlabel("Hora del día")
    ax.set_ylabel("Vehículos en cola (simulado)")
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 2))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)])
    ax.legend(handles=handles, labels=labels, loc="upper left", frameon=True, fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def graficar_geometria(ax):
    """Representa únicamente carriles y sentidos confirmados por la imagen."""
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")

    asfalto = "#30363d"
    ax.add_patch(mpatches.Rectangle((3, 0), 4, 10, color=asfalto))
    ax.add_patch(mpatches.Rectangle((0, 3.5), 10, 3, color=asfalto))
    ax.add_patch(mpatches.Rectangle((4.65, 0), 0.70, 10, color="#2D6CA9", alpha=0.92))

    for x in (3.65, 4.25, 5.75, 6.35):
        ax.plot([x, x], [0, 3.3], color="white", linewidth=0.8, dashes=(6, 6))
        ax.plot([x, x], [6.7, 10], color="white", linewidth=0.8, dashes=(6, 6))
    ax.plot([5, 5], [0, 3.3], color="white", linewidth=0.8, dashes=(5, 5))
    ax.plot([5, 5], [6.7, 10], color="white", linewidth=0.8, dashes=(5, 5))
    for y in (4.25, 5.0, 5.75):
        ax.plot([7.2, 10], [y, y], color="white", linewidth=0.8, dashes=(6, 6))
    ax.plot([0, 2.8], [5, 5], color="white", linewidth=0.8, dashes=(6, 6))

    for x in (3.95, 4.45):
        ax.text(x, 8.2, "↓", color="white", fontsize=18, ha="center", va="center")
        ax.text(x, 1.8, "↓", color="white", fontsize=18, ha="center", va="center")
    for x in (5.55, 6.05):
        ax.text(x, 8.2, "↑", color="white", fontsize=18, ha="center", va="center")
        ax.text(x, 1.8, "↑", color="white", fontsize=18, ha="center", va="center")
    ax.text(4.82, 8.2, "↓", color="white", fontsize=15, ha="center")
    ax.text(5.18, 1.8, "↑", color="white", fontsize=15, ha="center")
    ax.text(1.2, 5.55, "←", color="white", fontsize=18, ha="center")
    ax.text(1.8, 4.45, "→", color="white", fontsize=18, ha="center")
    ax.text(8.2, 5.85, "←  ←", color="white", fontsize=16, ha="center")
    ax.text(8.2, 4.15, "→  →", color="white", fontsize=16, ha="center")

    ax.text(5, 9.72, "Sombrerete · norte", color="white", ha="center", fontweight="bold")
    ax.text(5, 0.12, "Sombrerete · sur", color="white", ha="center", fontweight="bold")
    etiqueta = {"boxstyle": "round,pad=0.25", "facecolor": "#30363d", "edgecolor": "#55A868", "alpha": 0.95}
    ax.text(1.35, 6.05, "Calle 6\n1 entrada / 1 salida", color="white", ha="center", va="center", fontsize=8, bbox=etiqueta)
    ax.text(8.35, 6.05, "Praxedis Guerrero\n2 entradas / 2 salidas", color="white", ha="center", va="center", fontsize=8, bbox=etiqueta)
    ax.text(5, 7.2, "METROBÚS", color="white", ha="center", fontsize=8, rotation=90)
    ax.set_title("Geometría y sentidos documentados", fontweight="bold")


def graficar_ciclo_semaforico(ax):
    """Diagrama de tiempos (tipo Gantt) del ciclo de 100 s, construido
    directamente desde AGENDA (misma fuente que usa la simulación)."""
    etiquetas = [etq for _, etq in sem.MOVIMIENTOS]
    claves = [clv for clv, _ in sem.MOVIMIENTOS]

    for i, clave in enumerate(claves):
        y = len(claves) - i
        # Línea base (todo el ciclo) en gris muy claro para dar contexto
        ax.broken_barh([(0, sem.CICLO_TOTAL)], (y - 0.4, 0.8), facecolors=COLOR_LUZ[sem.ROJO])
        for inicio, fin, color in sem.AGENDA[clave]:
            ax.broken_barh([(inicio, fin - inicio)], (y - 0.4, 0.8),
                            facecolors=COLOR_LUZ[color])

    # Líneas verticales en los límites de las seis fases documentadas.
    for numero, (inicio, fin, nombre) in enumerate(sem.FASES, 1):
        ax.axvline(inicio, color="black", linewidth=0.6, alpha=0.4)
        ax.text(inicio + (fin - inicio) / 2, len(claves) + 0.7, str(numero),
                ha="center", fontsize=7, color="black")
    ax.axvline(sem.CICLO_TOTAL, color="black", linewidth=0.6, alpha=0.4)

    ax.set_yticks(range(1, len(claves) + 1))
    ax.set_yticklabels(list(reversed(etiquetas)), fontsize=9)
    ax.set_xlim(0, sem.CICLO_TOTAL)
    ax.set_xlabel("Segundo del ciclo semafórico (0-100 s)")
    ax.set_title("Ciclo base documentado: seis fases (20+20+10+10+20+20 s)", fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    leyenda = [
        mpatches.Patch(color=COLOR_LUZ[sem.VERDE], label="Verde"),
        mpatches.Patch(color=COLOR_LUZ[sem.AMARILLO], label="Amarillo"),
        mpatches.Patch(color=COLOR_LUZ[sem.ROJO], label="Rojo"),
    ]
    ax.legend(handles=leyenda, loc="upper center", bbox_to_anchor=(0.5, -0.18),
              ncol=3, frameon=False, fontsize=9)


def generar_figura(semilla=None, muestreo_seg=30, salida="congestion_cruce_sombrerete.png"):
    horas, serie = simular_24h(semilla=semilla, muestreo_seg=muestreo_seg)

    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update({
        "figure.dpi": 150,
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 10,
    })

    fig, (ax0, ax1, ax2) = plt.subplots(3, 1, figsize=(11, 15),
                                         gridspec_kw={"height_ratios": [1.15, 1.3, 1]})

    graficar_geometria(ax0)
    graficar_congestion(ax1, horas, serie)
    graficar_ciclo_semaforico(ax2)

    fig.suptitle("Cruce Av. Sombrerete - Calle 6 - Av. Praxedis Guerrero (Querétaro)",
                 fontsize=15, fontweight="bold", y=0.995)
    fig.text(0.5, 0.965,
              "Carriles y sentidos tomados de la imagen; tiempos base tomados del programa adjunto; "
              "demanda y saturación son supuestos, no conteos viales reales",
              ha="center", fontsize=9, style="italic", color="#555555")

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    ruta_salida = os.path.join(RUTA_BASE, salida)
    plt.savefig(ruta_salida, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta_salida


def parsear_argumentos():
    p = argparse.ArgumentParser(description="Genera gráficas de la simulación del cruce")
    p.add_argument("--semilla", type=int, default=42, help="Semilla aleatoria (reproducibilidad)")
    p.add_argument("--muestreo", type=int, default=30, help="Segundos entre cada muestra tomada en 24h")
    p.add_argument("--salida", default="congestion_cruce_sombrerete.png", help="Nombre del archivo PNG de salida")
    return p.parse_args()


if __name__ == "__main__":
    args = parsear_argumentos()
    ruta = generar_figura(semilla=args.semilla, muestreo_seg=args.muestreo, salida=args.salida)
    print(f"Gráfica generada: {ruta}")
