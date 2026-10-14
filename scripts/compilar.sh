#!/usr/bin/env bash
# Compila serial.cpp, alg1_omp.cpp y alg2_omp.cpp con -O3 -march=native -fopenmp.
# En macOS usa clang + libomp (instalar antes con: brew install libomp).
set -e
cd "$(dirname "$0")/.."
mkdir -p bin

if [[ "$(uname)" == "Darwin" ]]; then
    OMP=$(brew --prefix libomp)
    if [[ "$(uname -m)" == "arm64" ]]; then ARCH="-mcpu=native"; else ARCH="-march=native"; fi
    CXX="clang++"
    FLAGS="-O3 $ARCH -std=c++17 -Xpreprocessor -fopenmp -I$OMP/include -L$OMP/lib -lomp"
else
    CXX="g++"
    FLAGS="-O3 -march=native -std=c++17 -fopenmp"
fi

for prog in serial alg1_omp alg2_omp; do
    echo "$CXX src/$prog.cpp $FLAGS -o bin/$prog"
    $CXX src/$prog.cpp $FLAGS -o bin/$prog
done
echo "Compilacion lista (binarios en bin/)"
