#!/usr/bin/env bash
# Corre TODOS los experimentos de la Tarea 2 en este computador y guarda los
# resultados en resultados/<nombre>/.
#
# Uso (desde la carpeta del repo):
#     bash scripts/correr_experimentos.sh <nombre_computador>
# Ej.:
#     bash scripts/correr_experimentos.sh ignacia
#
# Opciones (variables de entorno):
#     REPS=3          repeticiones de cada medicion (para N = 1024 y 2048)
#     REPS_GRANDE=2   repeticiones para N = 4096 (son las mas lentas)
#     N_BLOQUE=64     tamano de bloque n del Algoritmo 2 para el item (f)
#     PYTHON=python   interprete de Python con numba instalado
#     N_CHICO=1024 N_BASE=2048 N_GRANDE=4096   tamanos de matriz (no cambiarlos para la entrega)
#
# Mientras corre, conviene cerrar otros programas y dejar el computador enchufado.

set -e
cd "$(dirname "$0")/.."

NOMBRE=${1:?"Falta el nombre del computador. Ej: bash scripts/correr_experimentos.sh ignacia"}
REPS=${REPS:-3}
REPS_GRANDE=${REPS_GRANDE:-2}
N_BLOQUE=${N_BLOQUE:-64}
PYTHON=${PYTHON:-python3}
N_CHICO=${N_CHICO:-1024}
N_BASE=${N_BASE:-2048}
N_GRANDE=${N_GRANDE:-4096}
THREADS="1 2 4 8"
BLOQUES=""
b=$N_BASE; while (( b >= 32 )); do BLOQUES="$BLOQUES $b"; b=$(( b / 2 )); done

OUT=resultados/$NOMBRE
mkdir -p "$OUT"
CSV=$OUT/tiempos.csv
[[ -f $CSV ]] && mv "$CSV" "$CSV.anterior_$(date +%Y%m%d_%H%M%S)"
echo "alg,N,n,p,rep,tiempo_s,checksum" > "$CSV"

echo "== 0. Caracteristicas del computador"
bash scripts/info_computador.sh | tee "$OUT/info_computador.txt"
"$PYTHON" -c "import numba; print('numba', numba.__version__, '| threads maximos numba:', numba.config.NUMBA_NUM_THREADS)" | tee -a "$OUT/info_computador.txt"

echo "== 1. Compilando"
bash scripts/compilar.sh | tee -a "$OUT/info_computador.txt"

# Guarda en el CSV solo las lineas que empiezan con "CSV," (y las muestra en pantalla)
guardar() { tee /dev/stderr | grep '^CSV,' | sed 's/^CSV,//' >> "$CSV"; }

# serial.cpp imprime "N=.. n=.. tiempo=.. ms checksum=..": se pasa al mismo formato
correr_serial() {   # $1 = N, $2 = n, $3 = repeticion
    ./bin/serial "$1" "$2" | awk -v r="$3" '{
        split($1,a,"="); split($2,b,"="); split($3,c,"="); split($5,d,"=");
        printf "CSV,serial,%s,%s,1,%s,%.6f,%s\n", a[2], b[2], r, c[2]/1000, d[2] }'
}

echo "== 2. Verificacion (N = $N_CHICO, todos los algoritmos contra la referencia)"
{
    for p in 1 8; do
        OMP_NUM_THREADS=$p ./bin/alg1_omp "$N_CHICO" 1 verificar
        OMP_NUM_THREADS=$p ./bin/alg2_omp "$N_CHICO" 64 1 verificar
        OMP_NUM_THREADS=$p ./bin/alg2_omp "$N_CHICO" 32 1 verificar
    done
    "$PYTHON" src/alg3_numba.py "$N_CHICO" 1 1 8 --verificar
} | grep VERIFICACION | tee "$OUT/verificacion.txt"

echo "== 3. Item (a): serial.cpp con N = $N_BASE y n = $BLOQUES"
for n in $BLOQUES; do
    for r in $(seq 1 "$REPS"); do correr_serial "$N_BASE" "$n" "$r"; done
done | guardar

echo "== 4. Items (b) y (f): Algoritmo 1, N = $N_BASE y $N_CHICO"
for N in "$N_BASE" "$N_CHICO"; do
    for p in $THREADS; do OMP_NUM_THREADS=$p ./bin/alg1_omp "$N" "$REPS"; done
done | guardar

echo "== 5. Items (c) y (e): Algoritmo 2, N = $N_BASE, todos los n"
for n in $BLOQUES; do
    for p in $THREADS; do OMP_NUM_THREADS=$p ./bin/alg2_omp "$N_BASE" "$n" "$REPS"; done
done | guardar

echo "== 6. Item (f): Algoritmo 2, N = $N_CHICO con n = $N_BLOQUE"
for p in $THREADS; do OMP_NUM_THREADS=$p ./bin/alg2_omp "$N_CHICO" "$N_BLOQUE" "$REPS"; done | guardar

echo "== 7. Item (d): Algoritmo 3 (Numba), N = $N_BASE y $N_CHICO"
for N in "$N_BASE" "$N_CHICO"; do "$PYTHON" src/alg3_numba.py "$N" "$REPS" $THREADS; done | guardar

echo "== 8. Item (f): N = $N_GRANDE (lo mas lento, puede tardar varios minutos)"
{
    for p in $THREADS; do OMP_NUM_THREADS=$p ./bin/alg1_omp "$N_GRANDE" "$REPS_GRANDE"; done
    for p in $THREADS; do OMP_NUM_THREADS=$p ./bin/alg2_omp "$N_GRANDE" "$N_BLOQUE" "$REPS_GRANDE"; done
    "$PYTHON" src/alg3_numba.py "$N_GRANDE" "$REPS_GRANDE" $THREADS
} | guardar

echo "== Listo. Resultados en $OUT/"
