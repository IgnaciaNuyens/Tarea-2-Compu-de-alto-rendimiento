# Tarea 2 · IIC3533 Computación de Alto Rendimiento · 2026-2

Multiplicación de matrices densas C = A·B (N × N) con tres versiones paralelas:

| Archivo | Versión |
|---|---|
| `src/serial.cpp` | Referencia serial entregada por el curso (dividir y conquistar con bloques de tamaño n) |
| `src/alg1_omp.cpp` | **Algoritmo 1**, paralelismo de datos con `#pragma omp parallel for` sobre las filas |
| `src/alg2_omp.cpp` | **Algoritmo 2**, dividir y conquistar con `#pragma omp task` y `taskwait` |
| `src/alg3_numba.py` | **Algoritmo 3**, paralelismo de datos en Python con `@njit(parallel=True)` y `prange` |

Todas las versiones usan las mismas matrices que `serial.cpp` y se verifican contra la referencia
(las versiones en C++ dan exactamente el mismo resultado, diferencia 0).

## Requisitos

* `g++` con OpenMP (Linux o WSL) o `clang++` con `libomp` (macOS, `brew install libomp`)
* Python 3 con `numpy`, `numba` y `matplotlib` (por ejemplo `conda install numba matplotlib`)

## Cómo correr todo

Desde la carpeta del repo:

```bash
bash scripts/correr_experimentos.sh <nombre_computador>     # ej. ignacia
```

Esto compila con `-O3 -march=native -fopenmp`, guarda las características del computador
(cores físicos, lógicos, reloj) y corre todos los experimentos. Los resultados quedan en
`resultados/<nombre_computador>/`:

* `info_computador.txt` características del computador (ítem g)
* `verificacion.txt` comparación de cada versión con la referencia
* `tiempos.csv` todas las mediciones (`alg,N,n,p,rep,tiempo_s,checksum`)

Tarda del orden de 15 a 30 minutos. Conviene cerrar otros programas y dejar el computador enchufado.

Luego, para generar gráficos (`graficos/`) y tablas en LaTeX (`tablas/`):

```bash
python scripts/graficos.py <computador1> <computador2> --n 64
```

## Correr una versión a mano

```bash
bash scripts/compilar.sh
./bin/serial 2048 64                              # N = 2048, n = 64
OMP_NUM_THREADS=4 ./bin/alg1_omp 2048 3           # N, repeticiones
OMP_NUM_THREADS=4 ./bin/alg2_omp 2048 64 3        # N, n, repeticiones
python src/alg3_numba.py 2048 3 1 2 4 8           # N, repeticiones, threads
OMP_NUM_THREADS=8 ./bin/alg2_omp 1024 64 1 verificar   # compara con la referencia
```

## Experimentos que corre el script

| Ítem | Experimento |
|---|---|
| (a) | `serial.cpp` con N = 2048 y n ∈ {2048, 1024, 512, 256, 128, 64, 32} |
| (b) | Algoritmo 1, N = 2048, p ∈ {1, 2, 4, 8} |
| (c), (e) | Algoritmo 2, N = 2048, todos los n anteriores y p ∈ {1, 2, 4, 8} |
| (d) | Algoritmo 3, N = 2048, p ∈ {1, 2, 4, 8} (con warm-up para excluir la compilación JIT) |
| (f) | Las tres versiones con N ∈ {1024, 2048, 4096} y p ∈ {1, 2, 4, 8} |
| (g) | Todo lo anterior se repite en un segundo computador |

Cada medición se repite (3 veces, 2 para N = 4096) y se usa el mínimo.

## Uso de IA

Parte del código y de los scripts se desarrolló con ayuda de Claude (Anthropic), lo que se declara en el informe.
