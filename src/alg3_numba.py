"""
alg3_numba.py - Algoritmo 3: paralelismo de datos en Python con Numba.

Misma idea que el Algoritmo 1 (tres loops i, k, j) pero escrito en Python.
@njit(parallel=True) compila la funcion y prange reparte las filas i entre threads.

Uso:
    python alg3_numba.py [N] [repeticiones] [threads...] [--verificar]
Ej.:
    python alg3_numba.py 2048 3 1 2 4 8
    python alg3_numba.py 1024 1 8 --verificar

Imprime una linea por repeticion con el formato
    CSV,alg3,N,n,p,repeticion,tiempo_s,checksum
"""

import sys
import time

import numpy as np
import numba
from numba import njit, prange


@njit(parallel=True)
def matmul_numba(A, B, C):
    N = A.shape[0]
    # prange: las iteraciones de i se reparten entre los threads.
    # Cada thread escribe filas distintas de C, asi que no hay condicion de carrera.
    for i in prange(N):
        for k in range(N):
            a = A[i, k]
            for j in range(N):
                C[i, j] += a * B[k, j]


def init_matrix(N, offset):
    # Mismos valores que serial.cpp: sin(0.1 i + 0.3 j + offset)
    i = np.arange(N, dtype=np.float64).reshape(-1, 1)
    j = np.arange(N, dtype=np.float64).reshape(1, -1)
    return np.sin(i * 0.1 + j * 0.3 + offset)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    verificar = "--verificar" in sys.argv
    N = int(args[0]) if len(args) > 0 else 2048
    reps = int(args[1]) if len(args) > 1 else 3
    threads = [int(x) for x in args[2:]] if len(args) > 2 else [1, 2, 4, 8]

    A = init_matrix(N, 1.0)
    B = init_matrix(N, 2.0)
    C = np.zeros((N, N))

    # Warm-up: la primera llamada compila la funcion (JIT). Se hace con una matriz
    # chica del mismo tipo para que esa compilacion NO quede dentro de lo que se mide.
    chica = np.ones((64, 64))
    matmul_numba(chica, chica, np.zeros((64, 64)))

    max_threads = numba.config.NUMBA_NUM_THREADS
    for p in threads:
        if p > max_threads:
            print(f"# se omite p={p}: este computador solo permite {max_threads} threads en Numba")
            continue
        numba.set_num_threads(p)
        for r in range(1, reps + 1):
            C[:] = 0.0                                  # no se mide
            t0 = time.perf_counter()
            matmul_numba(A, B, C)
            t1 = time.perf_counter()
            print(f"CSV,alg3,{N},{N},{p},{r},{t1 - t0:.6f},{C.sum():.6f}", flush=True)

        if verificar:
            ref = A @ B                                 # referencia de NumPy
            maxdiff = np.abs(C - ref).max()
            estado = "OK" if maxdiff < 1e-8 else "ERROR"
            print(f"VERIFICACION alg3 N={N} p={p} max|C-Cref|={maxdiff:.3e} {estado}")


if __name__ == "__main__":
    main()
