// alg1_omp.cpp - Algoritmo 1: paralelismo de datos con OpenMP.
// C = A * B de N x N con los tres loops (orden i, k, j) y "#pragma omp parallel for"
// sobre el loop de las filas (i).
//
// Uso:   OMP_NUM_THREADS=p ./alg1_omp [N] [repeticiones] [verificar]
// Ej.:   OMP_NUM_THREADS=4 ./alg1_omp 2048 3
//        OMP_NUM_THREADS=4 ./alg1_omp 1024 1 verificar
//
// Imprime una linea por repeticion con el formato
//   CSV,alg1,N,n,p,repeticion,tiempo_s,checksum
// (n = N porque este algoritmo no divide en bloques).

#include <omp.h>
#include <vector>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>

// Mismos valores que serial.cpp, para que el resultado sea comparable.
double det_value(int i, int j, double offset) {
    return std::sin(i * 0.1 + j * 0.3 + offset);
}

void init_matrix(std::vector<double>& M, int N, double offset) {
    for (int i = 0; i < N; ++i)
        for (int j = 0; j < N; ++j)
            M[i * N + j] = det_value(i, j, offset);
}

// Version paralela: cada thread recibe un grupo de filas i de C.
// Dos threads nunca escriben la misma casilla C[i][j], asi que no hay condicion de carrera.
// A y B solo se leen (shared de solo lectura). Las variables i, k, j, a son privadas
// porque se declaran dentro del loop.
void matmul_omp(const double* A, const double* B, double* C, int N) {
    #pragma omp parallel for schedule(static)
    for (int i = 0; i < N; ++i) {
        for (int k = 0; k < N; ++k) {
            double a = A[i * N + k];
            for (int j = 0; j < N; ++j) {
                C[i * N + j] += a * B[k * N + j];
            }
        }
    }
}

// Referencia serial (identica a serial.cpp con n = N), para verificar.
void matmul_serial(const double* A, const double* B, double* C, int N) {
    for (int i = 0; i < N; ++i)
        for (int k = 0; k < N; ++k) {
            double a = A[i * N + k];
            for (int j = 0; j < N; ++j)
                C[i * N + j] += a * B[k * N + j];
        }
}

int main(int argc, char** argv) {
    int N    = (argc > 1) ? std::atoi(argv[1]) : 2048;
    int reps = (argc > 2) ? std::atoi(argv[2]) : 3;
    bool verificar = (argc > 3) && std::strcmp(argv[3], "verificar") == 0;
    int p = omp_get_max_threads();

    std::vector<double> A(N * N), B(N * N), C(N * N);
    init_matrix(A, N, 1);
    init_matrix(B, N, 2);

    for (int r = 1; r <= reps; ++r) {
        std::fill(C.begin(), C.end(), 0.0);           // no se mide

        double t0 = omp_get_wtime();
        matmul_omp(A.data(), B.data(), C.data(), N);
        double t1 = omp_get_wtime();

        double checksum = 0.0;
        for (double v : C) checksum += v;
        std::printf("CSV,alg1,%d,%d,%d,%d,%.6f,%.6f\n", N, N, p, r, t1 - t0, checksum);
        std::fflush(stdout);
    }

    if (verificar) {
        std::vector<double> R(N * N, 0.0);
        matmul_serial(A.data(), B.data(), R.data(), N);
        double maxdiff = 0.0;
        for (int i = 0; i < N * N; ++i) maxdiff = std::fmax(maxdiff, std::fabs(C[i] - R[i]));
        std::printf("VERIFICACION alg1 N=%d p=%d max|C-Cref|=%.3e %s\n",
                    N, p, maxdiff, maxdiff < 1e-8 ? "OK" : "ERROR");
    }
    return 0;
}
