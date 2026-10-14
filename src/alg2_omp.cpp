// alg2_omp.cpp - Algoritmo 2: dividir y conquistar con tareas de OpenMP.
// Parte de serial.cpp. Cada nivel de la recursion divide C en 4 cuadrantes y crea
// una tarea (#pragma omp task) por cuadrante. Al llegar a bloques de tamano <= n
// se hace la multiplicacion densa directa (hoja).
//
// Uso:   OMP_NUM_THREADS=p ./alg2_omp [N] [n] [repeticiones] [verificar]
// Ej.:   OMP_NUM_THREADS=8 ./alg2_omp 2048 64 3
//        OMP_NUM_THREADS=8 ./alg2_omp 1024 64 1 verificar
//
// Imprime una linea por repeticion con el formato
//   CSV,alg2,N,n,p,repeticion,tiempo_s,checksum

#include <omp.h>
#include <vector>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>

// Vista de un bloque s x s dentro de una matriz N x N (row-major), sin copiar.
// (igual que en serial.cpp)
struct MatView {
    double* data;
    int stride;
    int size;
    double& at(int i, int j) const { return data[i * stride + j]; }
    MatView sub(int r, int c, int s) const { return { data + r * stride + c, stride, s }; }
};

double det_value(int i, int j, double offset) {
    return std::sin(i * 0.1 + j * 0.3 + offset);
}

void init_matrix(std::vector<double>& M, int N, double offset) {
    for (int i = 0; i < N; ++i)
        for (int j = 0; j < N; ++j)
            M[i * N + j] = det_value(i, j, offset);
}

// Hoja: multiplicacion densa que acumula en C (C += A * B). Igual que serial.cpp.
void multiply_leaf(MatView A, MatView B, MatView C) {
    int s = C.size;
    for (int i = 0; i < s; ++i) {
        for (int k = 0; k < s; ++k) {
            double a = A.at(i, k);
            for (int j = 0; j < s; ++j) {
                C.at(i, j) += a * B.at(k, j);
            }
        }
    }
}

// Version serial de serial.cpp (se usa solo para verificar).
void multiply_rec(MatView A, MatView B, MatView C, int n) {
    int s = C.size;
    if (s <= n) { multiply_leaf(A, B, C); return; }
    int h = s / 2;
    multiply_rec(A.sub(0, 0, h), B.sub(0, 0, h), C.sub(0, 0, h), n);
    multiply_rec(A.sub(0, h, h), B.sub(h, 0, h), C.sub(0, 0, h), n);
    multiply_rec(A.sub(0, 0, h), B.sub(0, h, h), C.sub(0, h, h), n);
    multiply_rec(A.sub(0, h, h), B.sub(h, h, h), C.sub(0, h, h), n);
    multiply_rec(A.sub(h, 0, h), B.sub(0, 0, h), C.sub(h, 0, h), n);
    multiply_rec(A.sub(h, h, h), B.sub(h, 0, h), C.sub(h, 0, h), n);
    multiply_rec(A.sub(h, 0, h), B.sub(0, h, h), C.sub(h, h, h), n);
    multiply_rec(A.sub(h, h, h), B.sub(h, h, h), C.sub(h, h, h), n);
}

// Version paralela con tareas.
//   C11 = A11*B11 + A12*B21     C12 = A11*B12 + A12*B22
//   C21 = A21*B11 + A22*B21     C22 = A21*B12 + A22*B22
// Los 4 cuadrantes de C son independientes entre si => una tarea por cuadrante.
// Los 2 productos de un mismo cuadrante escriben el MISMO bloque de C => si corrieran
// en paralelo habria condicion de carrera. Por eso, dentro de cada tarea, se hacen
// uno despues del otro (el primero termina antes de empezar el segundo porque cada
// llamada recursiva termina con su propio taskwait).
// Las vistas A, B, C se pasan por valor: cada tarea recibe su propia copia
// (firstprivate por defecto), que solo guarda un puntero, el stride y el tamano.
void multiply_rec_par(MatView A, MatView B, MatView C, int n) {
    int s = C.size;
    if (s <= n) { multiply_leaf(A, B, C); return; }
    int h = s / 2;

    MatView A11 = A.sub(0, 0, h), A12 = A.sub(0, h, h), A21 = A.sub(h, 0, h), A22 = A.sub(h, h, h);
    MatView B11 = B.sub(0, 0, h), B12 = B.sub(0, h, h), B21 = B.sub(h, 0, h), B22 = B.sub(h, h, h);
    MatView C11 = C.sub(0, 0, h), C12 = C.sub(0, h, h), C21 = C.sub(h, 0, h), C22 = C.sub(h, h, h);

    #pragma omp task
    {
        multiply_rec_par(A11, B11, C11, n);
        multiply_rec_par(A12, B21, C11, n);
    }
    #pragma omp task
    {
        multiply_rec_par(A11, B12, C12, n);
        multiply_rec_par(A12, B22, C12, n);
    }
    #pragma omp task
    {
        multiply_rec_par(A21, B11, C21, n);
        multiply_rec_par(A22, B21, C21, n);
    }
    #pragma omp task
    {
        multiply_rec_par(A21, B12, C22, n);
        multiply_rec_par(A22, B22, C22, n);
    }
    // Esperar a las 4 tareas hijas antes de retornar. Asi quien llamo sabe que
    // su bloque de C ya esta completo (necesario para el segundo producto).
    #pragma omp taskwait
}

int main(int argc, char** argv) {
    int N    = (argc > 1) ? std::atoi(argv[1]) : 2048;
    int n    = (argc > 2) ? std::atoi(argv[2]) : 64;
    int reps = (argc > 3) ? std::atoi(argv[3]) : 3;
    bool verificar = (argc > 4) && std::strcmp(argv[4], "verificar") == 0;
    int p = omp_get_max_threads();

    std::vector<double> A(N * N), B(N * N), C(N * N);
    init_matrix(A, N, 1);
    init_matrix(B, N, 2);
    MatView Av{ A.data(), N, N }, Bv{ B.data(), N, N }, Cv{ C.data(), N, N };

    for (int r = 1; r <= reps; ++r) {
        std::fill(C.begin(), C.end(), 0.0);           // no se mide

        double t0 = omp_get_wtime();
        // Se crea el equipo de threads una sola vez; un solo thread (single)
        // inicia la recursion y los demas van tomando las tareas que se encolan.
        #pragma omp parallel
        {
            #pragma omp single
            multiply_rec_par(Av, Bv, Cv, n);
        }
        double t1 = omp_get_wtime();

        double checksum = 0.0;
        for (double v : C) checksum += v;
        std::printf("CSV,alg2,%d,%d,%d,%d,%.6f,%.6f\n", N, n, p, r, t1 - t0, checksum);
        std::fflush(stdout);
    }

    if (verificar) {
        std::vector<double> R(N * N, 0.0);
        MatView Rv{ R.data(), N, N };
        multiply_rec(Av, Bv, Rv, n);
        double maxdiff = 0.0;
        for (int i = 0; i < N * N; ++i) maxdiff = std::fmax(maxdiff, std::fabs(C[i] - R[i]));
        std::printf("VERIFICACION alg2 N=%d n=%d p=%d max|C-Cref|=%.3e %s\n",
                    N, n, p, maxdiff, maxdiff < 1e-8 ? "OK" : "ERROR");
    }
    return 0;
}
