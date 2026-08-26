"""
Visualización gráfica (matplotlib) de la simulación del cruce
Av. Sombrerete - Calle 6 - Av. Praxedis Guerrero (Querétaro)

Reutiliza el motor de simulación de semaforo_sombrerete.py (misma AGENDA,
mismos parámetros de tráfico) para que las gráficas y la simulación de
consola nunca queden desincronizadas.

Genera una figura con dos paneles:
  A) Congestión (vehículos en cola) a lo largo de 24 h, con las horas
     pico (7-9 AM y 5-7 PM) resaltadas.
  B) Diagrama de tiempos del ciclo semafórico de 100 s (verde/amarillo
     por movimiento), equivalente al diagrama del PDF original pero
     generado directamente desde los mismos datos que usa la simulación.

Uso:
    python3 graficar_simulacion.py
    python3 graficar_simulacion.py --semilla 7 --muestreo 30
"""

import argparse
import importlib.util
import os

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

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
        "Av. Sombrerete (ambos sentidos)": [],
        "Calle 6": [],
        "Av. Praxedis Guerrero": [],
        "Metrobús (ambas rutas)": [],
    }

    for s in range(0, 86400):
        t_ciclo = s % sem.CICLO_TOTAL
        sim.actualizar_colas(s, t_ciclo)

        if s % muestreo_seg == 0:
            horas.append(s / 3600.0)
            c = sim.colas
            serie["Av. Sombrerete (ambos sentidos)"].append(
                c["somb_n_izq"] + c["somb_n_frente"] + c["somb_s_frente"]
            )
            serie["Calle 6"].append(c["calle6"])
            serie["Av. Praxedis Guerrero"].append(c["praxedis"])
            serie["Metrobús (ambas rutas)"].append(c["metrobus_n"] + c["metrobus_s"])

    return horas, serie


def graficar_congestion(ax, horas, serie):
    colores = {
        "Av. Sombrerete (ambos sentidos)": COLOR_SOMBRERETE,
        "Calle 6": COLOR_CALLE6,
        "Av. Praxedis Guerrero": COLOR_PRAXEDIS,
        "Metrobús (ambas rutas)": COLOR_METROBUS,
    }
    estilos = {
        "Av. Sombrerete (ambos sentidos)": "-",
        "Calle 6": "--",
        "Av. Praxedis Guerrero": "-.",
        "Metrobús (ambas rutas)": ":",
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

    ax.set_title("La congestión se dispara en horas pico (7-9 AM y 5-7 PM)",
                 fontweight="bold")
    ax.set_xlabel("Hora del día")
    ax.set_ylabel("Vehículos en cola (simulado)")
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 2))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)])
    ax.legend(handles=handles, labels=labels, loc="upper left", frameon=True, fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


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

    # Líneas verticales en los límites de cada fase (F1..F6)
    for inicio, fin, nombre in sem.FASES:
        ax.axvline(inicio, color="black", linewidth=0.6, alpha=0.4)
        ax.text(inicio + (fin - inicio) / 2, len(claves) + 0.7, nombre.split(" - ")[0],
                ha="center", fontsize=8, color="black")
    ax.axvline(sem.CICLO_TOTAL, color="black", linewidth=0.6, alpha=0.4)

    ax.set_yticks(range(1, len(claves) + 1))
    ax.set_yticklabels(list(reversed(etiquetas)), fontsize=9)
    ax.set_xlim(0, sem.CICLO_TOTAL)
    ax.set_xlabel("Segundo del ciclo semafórico (0-100 s)")
    ax.set_title("Ciclo semafórico del cruce (100 s por ciclo)", fontweight="bold")
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

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 10),
                                    gridspec_kw={"height_ratios": [1.3, 1]})

    graficar_congestion(ax1, horas, serie)
    graficar_ciclo_semaforico(ax2)

    fig.suptitle("Cruce Av. Sombrerete - Calle 6 - Av. Praxedis Guerrero (Querétaro)",
                 fontsize=15, fontweight="bold", y=0.995)
    fig.text(0.5, 0.965,
              "Fases y tiempos de luz tomados del diagrama/mapa mental proporcionados; "
              "las tasas de llegada de vehículos son simuladas (no son conteos viales reales)",
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
