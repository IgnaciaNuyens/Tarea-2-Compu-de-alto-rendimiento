"""
graficos.py - Lee resultados/<computador>/tiempos.csv y genera los graficos y
tablas del informe en graficos/ y tablas/.

Uso (desde la carpeta del repo):
    python scripts/graficos.py <computador1> [<computador2> ...] [--n 64]
Ej.:
    python scripts/graficos.py ignacia companero --n 64

--n es el tamano de bloque elegido para el Algoritmo 2 (el mismo N_BLOQUE
con que se corrio correr_experimentos.sh).

Para cada medicion se usa el MINIMO de las repeticiones (menos sensible a
interrupciones del sistema operativo). Speedup y eficiencia usan como T(1) el
tiempo de la MISMA version con 1 thread.
"""

import csv
import os
import sys
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------------------------------------------- estilo
plt.rcParams.update({
    "font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12,
    "legend.fontsize": 10.5, "xtick.labelsize": 11, "ytick.labelsize": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e4e3df", "grid.linewidth": 0.8,
    "axes.edgecolor": "#8a8984", "lines.linewidth": 2, "lines.markersize": 7,
    "savefig.dpi": 200, "savefig.bbox": "tight",
})
COLOR = {"alg1": "#2a78d6", "alg2": "#eb6834", "alg3": "#1baf7a"}
MARCA = {"alg1": "o", "alg2": "s", "alg3": "^"}
NOMBRE = {"alg1": "Alg. 1 (OpenMP datos)", "alg2": "Alg. 2 (OpenMP tareas)",
          "alg3": "Alg. 3 (Numba)"}
GRIS_IDEAL = "#8a8984"
COMPUTADOR_COLOR = ["#2a78d6", "#eb6834", "#1baf7a"]
COMPUTADOR_MARCA = ["o", "s", "^"]


def rampa(k):
    """k tonos de un mismo azul, de claro a oscuro (para magnitudes: n o N)."""
    return [plt.cm.Blues(x) for x in np.linspace(0.35, 0.95, k)]


# ----------------------------------------------------------------- datos
def leer(computador):
    """Devuelve dict[(alg, N, n, p)] -> lista de tiempos."""
    datos = defaultdict(list)
    with open(os.path.join("resultados", computador, "tiempos.csv")) as f:
        for fila in csv.DictReader(f):
            clave = (fila["alg"], int(fila["N"]), int(fila["n"]), int(fila["p"]))
            datos[clave].append(float(fila["tiempo_s"]))
    return datos


def tmin(datos, alg, N, n, p):
    t = datos.get((alg, N, n, p))
    return min(t) if t else np.nan


def bloque_de(alg, N, n_elegido):
    return n_elegido if alg == "alg2" else N


def ps_de(datos, alg, N, n):
    return sorted({k[3] for k in datos if k[0] == alg and k[1] == N and k[2] == n})


def guardar(fig, carpeta, nombre):
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)
    fig.savefig(ruta)
    plt.close(fig)
    print("  ->", ruta)


def eje_p(ax, ps):
    ax.set_xscale("log", base=2)
    ax.set_xticks(ps)
    ax.set_xticklabels([str(p) for p in ps])
    ax.set_xlabel("Número de threads $p$")


# ----------------------------------------------------------------- graficos
def fig_a(datos, N, carpeta):
    ns = sorted({k[2] for k in datos if k[0] == "serial" and k[1] == N})
    ts = [tmin(datos, "serial", N, n, 1) for n in ns]
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.plot(ns, ts, marker="o", color=COLOR["alg2"])
    for n, t in zip(ns, ts):
        ax.annotate(f"{t:.2f}", (n, t), textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=9.5, color="#52514e")
    ax.set_xscale("log", base=2)
    ax.set_xticks(ns)
    ax.set_xticklabels([str(n) for n in ns])
    ax.set_xlabel("Tamaño de bloque $n$")
    ax.set_ylabel("Tiempo [s]")
    ax.set_ylim(0, max(ts) * 1.18)
    ax.set_title(f"serial.cpp, N = {N} ($n$ = N: sin subdivisión)")
    guardar(fig, carpeta, "a_serial_vs_bloque.png")


def fig_e(datos, N, n_elegido, carpeta):
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.3))
    todos_ps = set()
    for alg in ("alg1", "alg2", "alg3"):
        n = bloque_de(alg, N, n_elegido)
        ps = ps_de(datos, alg, N, n)
        if not ps:
            continue
        todos_ps.update(ps)
        T = np.array([tmin(datos, alg, N, n, p) for p in ps])
        S = T[0] / T
        E = S / np.array(ps)
        kw = dict(color=COLOR[alg], marker=MARCA[alg], label=NOMBRE[alg])
        axs[0].plot(ps, T, **kw)
        axs[0].plot(ps, T[0] / np.array(ps), color=COLOR[alg], ls=":", lw=1.3)
        axs[1].plot(ps, S, **kw)
        axs[2].plot(ps, E, **kw)
    ps = sorted(todos_ps)
    axs[1].plot(ps, ps, ls="--", color=GRIS_IDEAL, lw=1.5, label="Ideal $S = p$")
    axs[2].axhline(1, ls="--", color=GRIS_IDEAL, lw=1.5, label="Ideal $E = 1$")
    axs[0].plot([], [], ls=":", color=GRIS_IDEAL, lw=1.3, label="Ideal $T(1)/p$")
    axs[0].set_ylabel("Tiempo $T(p)$ [s]")
    axs[1].set_ylabel("Speedup $S(p)$")
    axs[2].set_ylabel("Eficiencia $E(p)$")
    axs[2].set_ylim(0, 1.15)
    for ax, t in zip(axs, ("Tiempo", "Speedup", "Eficiencia")):
        eje_p(ax, ps)
        ax.set_title(f"{t}, N = {N}")
        ax.legend()
    fig.suptitle(f"Algoritmo 2 con $n$ = {n_elegido}. $T(1)$: misma versión con 1 thread.",
                 y=1.02, fontsize=11.5, color="#52514e")
    guardar(fig, carpeta, "e_tiempo_speedup_eficiencia.png")


def fig_e_bloques(datos, N, carpeta):
    ns = sorted({k[2] for k in datos if k[0] == "alg2" and k[1] == N}, reverse=True)
    colores = rampa(len(ns))
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.3))
    ps = []
    for n, c in zip(ns, colores):
        ps = ps_de(datos, "alg2", N, n)
        T = np.array([tmin(datos, "alg2", N, n, p) for p in ps])
        axs[0].plot(ps, T, marker="o", color=c, label=f"$n$ = {n}")
        axs[1].plot(ps, T[0] / T, marker="o", color=c, label=f"$n$ = {n}")
    axs[1].plot(ps, ps, ls="--", color=GRIS_IDEAL, lw=1.5, label="Ideal")
    axs[0].set_ylabel("Tiempo $T(p)$ [s]")
    axs[1].set_ylabel("Speedup $S(p)$")
    axs[0].set_title(f"Algoritmo 2, tiempo según $n$ (N = {N})")
    axs[1].set_title(f"Algoritmo 2, speedup según $n$ (N = {N})")
    for ax in axs:
        eje_p(ax, ps)
    axs[1].legend(ncol=2)
    guardar(fig, carpeta, "e_alg2_por_bloque.png")


def fig_f(datos, Ns, n_elegido, carpeta):
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.3), sharey=True)
    colores = rampa(len(Ns))
    for ax, alg in zip(axs, ("alg1", "alg2", "alg3")):
        ps = []
        for N, c in zip(Ns, colores):
            n = bloque_de(alg, N, n_elegido)
            ps_N = ps_de(datos, alg, N, n)
            if not ps_N:
                continue
            ps = ps_N
            T = np.array([tmin(datos, alg, N, n, p) for p in ps])
            ax.plot(ps, T[0] / T / np.array(ps), marker="o", color=c, label=f"N = {N}")
        ax.axhline(1, ls="--", color=GRIS_IDEAL, lw=1.5)
        eje_p(ax, ps)
        ax.set_title(NOMBRE[alg])
        ax.set_ylim(0, 1.15)
        ax.legend()
    axs[0].set_ylabel("Eficiencia $E(p)$")
    guardar(fig, carpeta, "f_eficiencia_por_N.png")


def fig_g(todos, N, n_elegido, carpeta):
    nombres = list(todos)
    fig, axs = plt.subplots(2, 3, figsize=(15, 8.2))
    for j, alg in enumerate(("alg1", "alg2", "alg3")):
        n = bloque_de(alg, N, n_elegido)
        for i, comp in enumerate(nombres):
            datos = todos[comp]
            ps = ps_de(datos, alg, N, n)
            if not ps:
                continue
            T = np.array([tmin(datos, alg, N, n, p) for p in ps])
            kw = dict(color=COMPUTADOR_COLOR[i % 3], marker=COMPUTADOR_MARCA[i % 3], label=comp)
            axs[0, j].plot(ps, T, **kw)
            axs[1, j].plot(ps, T[0] / T, **kw)
            eje_p(axs[0, j], ps)
            eje_p(axs[1, j], ps)
        pp = sorted({k[3] for d in todos.values() for k in d
                     if k[0] == alg and k[1] == N and k[2] == n})
        axs[1, j].plot(pp, pp, ls="--", color=GRIS_IDEAL, lw=1.5, label="Ideal")
        axs[0, j].set_title(f"{NOMBRE[alg]}, tiempo")
        axs[1, j].set_title(f"{NOMBRE[alg]}, speedup")
        axs[0, j].legend()
        axs[1, j].legend()
    axs[0, 0].set_ylabel("Tiempo $T(p)$ [s]")
    axs[1, 0].set_ylabel("Speedup $S(p)$")
    fig.suptitle(f"Comparación entre computadores, N = {N}", fontsize=14)
    fig.tight_layout()
    guardar(fig, carpeta, "g_comparacion_computadores.png")


# ----------------------------------------------------------------- tablas
def tabla_latex(encabezado, filas, titulo, etiqueta):
    cols = "l" + "r" * (len(encabezado) - 1)
    lineas = [r"\begin{table}[H]", r"\centering", r"\caption{" + titulo + "}",
              r"\label{" + etiqueta + "}", r"\begin{tabular}{" + cols + "}", r"\toprule",
              " & ".join(encabezado) + r" \\", r"\midrule"]
    lineas += [" & ".join(str(x) for x in f) + r" \\" for f in filas]
    lineas += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(lineas)


def tablas(datos, comp, N_base, Ns, n_elegido, carpeta):
    os.makedirs(carpeta, exist_ok=True)
    salida = []

    # (a)
    ns = sorted({k[2] for k in datos if k[0] == "serial" and k[1] == N_base}, reverse=True)
    filas = [[n, f"{tmin(datos, 'serial', N_base, n, 1):.3f}"] for n in ns]
    salida.append(tabla_latex(["$n$", "Tiempo [s]"], filas,
                              f"Tiempo de serial.cpp según el tamaño de bloque (N = {N_base}, {comp}).",
                              f"tab:a_{comp}"))

    # (b), (c), (d)
    filas = []
    for alg in ("alg1", "alg2", "alg3"):
        n = bloque_de(alg, N_base, n_elegido)
        ps = ps_de(datos, alg, N_base, n)
        if not ps:
            continue
        T1 = tmin(datos, alg, N_base, n, ps[0])
        for p in ps:
            T = tmin(datos, alg, N_base, n, p)
            filas.append([NOMBRE[alg] if p == ps[0] else "", p, f"{T:.3f}",
                          f"{T1 / T:.2f}", f"{T1 / T / p:.2f}"])
    salida.append(tabla_latex(["Versión", "$p$", "$T(p)$ [s]", "$S(p)$", "$E(p)$"], filas,
                              f"Tiempo, speedup y eficiencia (N = {N_base}, Alg. 2 con $n$ = {n_elegido}, {comp}).",
                              f"tab:bcd_{comp}"))

    # (e) Alg. 2 por bloque
    ns2 = sorted({k[2] for k in datos if k[0] == "alg2" and k[1] == N_base}, reverse=True)
    ps = ps_de(datos, "alg2", N_base, n_elegido)
    filas = []
    for n in ns2:
        T = [tmin(datos, "alg2", N_base, n, p) for p in ps]
        filas.append([n] + [f"{t:.3f}" for t in T] + [f"{T[0] / T[-1]:.2f}"])
    salida.append(tabla_latex(["$n$"] + [f"$T({p})$" for p in ps] + [f"$S({ps[-1]})$"], filas,
                              f"Algoritmo 2, tiempo [s] según $n$ y $p$ (N = {N_base}, {comp}).",
                              f"tab:e_{comp}"))

    # (f) eficiencia por N y eficiencia debil
    filas = []
    for alg in ("alg1", "alg2", "alg3"):
        for N in Ns:
            n = bloque_de(alg, N, n_elegido)
            ps = ps_de(datos, alg, N, n)
            if not ps:
                continue
            T1 = tmin(datos, alg, N, n, 1)
            filas.append([NOMBRE[alg] if N == Ns[0] else "", N] +
                         [f"{T1 / tmin(datos, alg, N, n, p) / p:.2f}" for p in (1, 2, 4, 8)])
    salida.append(tabla_latex(["Versión", "N", "$E(1)$", "$E(2)$", "$E(4)$", "$E(8)$"], filas,
                              f"Eficiencia según el tamaño del problema ({comp}).", f"tab:f_{comp}"))

    filas = []
    for alg in ("alg1", "alg2", "alg3"):
        for N in Ns:
            if N // 2 not in Ns:
                continue
            Tchico = tmin(datos, alg, N // 2, bloque_de(alg, N // 2, n_elegido), 1)
            Tgrande = tmin(datos, alg, N, bloque_de(alg, N, n_elegido), 8)
            if np.isnan(Tchico) or np.isnan(Tgrande):
                continue
            filas.append([NOMBRE[alg], f"{N // 2} con $p$ = 1", f"{N} con $p$ = 8",
                          f"{Tchico:.3f}", f"{Tgrande:.3f}", f"{Tchico / Tgrande:.2f}"])
    salida.append(tabla_latex(["Versión", "Base", "Escalado", "$T$ base [s]", "$T$ escalado [s]",
                               "$E_{\\mathrm{débil}}$"], filas,
                              f"Eficiencia débil con trabajo por thread constante ({comp}).",
                              f"tab:debil_{comp}"))

    ruta = os.path.join(carpeta, f"tablas_{comp}.tex")
    with open(ruta, "w") as f:
        f.write("% Generado por scripts/graficos.py. Requiere \\usepackage{booktabs,float}\n\n")
        f.write("\n".join(salida))
    print("  ->", ruta)


# ----------------------------------------------------------------- main
def main():
    args = sys.argv[1:]
    n_elegido = 64
    if "--n" in args:
        i = args.index("--n")
        n_elegido = int(args[i + 1])
        del args[i:i + 2]
    if not args:
        args = sorted(d for d in os.listdir("resultados")
                      if os.path.isfile(os.path.join("resultados", d, "tiempos.csv")))
    todos = {c: leer(c) for c in args}

    for comp, datos in todos.items():
        print(f"== {comp}")
        Ns = sorted({k[1] for k in datos if k[0] == "alg1"})
        N_base = 2048 if 2048 in Ns else Ns[len(Ns) // 2]
        carpeta = os.path.join("graficos", comp)
        fig_a(datos, N_base, carpeta)
        fig_e(datos, N_base, n_elegido, carpeta)
        fig_e_bloques(datos, N_base, carpeta)
        fig_f(datos, Ns, n_elegido, carpeta)
        tablas(datos, comp, N_base, Ns, n_elegido, "tablas")

    if len(todos) >= 2:
        print("== comparación")
        primero = next(iter(todos.values()))
        Ns = sorted({k[1] for k in primero if k[0] == "alg1"})
        N_base = 2048 if 2048 in Ns else Ns[len(Ns) // 2]
        fig_g(todos, N_base, n_elegido, "graficos")


if __name__ == "__main__":
    main()
