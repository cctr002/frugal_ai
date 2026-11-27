#!/usr/bin/env bash
# À lancer depuis le poste Linux de la salle.
set -euo pipefail
cd "$(dirname "$0")"

export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 OMP_DYNAMIC=FALSE
python3 - <<'PY'
from statistics import mean
from time import perf_counter

import matmul as m

n = 1920
a, b = m.np.random.default_rng(0).random((2, n, n), dtype=m.np.float32)
c = m.np.zeros_like(a)
warm = m.np.ones((2, 2), dtype=m.np.float32)
m.matmul_naive_jit(warm, warm, warm.copy(), 2, 2, 2)
times = []
for _ in range(3):
    start = perf_counter()
    m.matmul_naive_jit(a, b, c, n, n, n)
    times.append(perf_counter() - start)
m.np.testing.assert_allclose(c[:4, :4], a[:4] @ b[:, :4], rtol=1e-5)
print(f"Q9 Numba à {n} : {mean(times):.4f} s (3 passages hors compilation)")
PY

tmp=$(mktemp -d)
trap 'rm -f "$tmp/q34.c" "$tmp/q34"; rmdir "$tmp"' EXIT
cat > "$tmp/q34.c" <<'C'
#define main benchmark_original
#include "matmul.c"
#undef main
#include <omp.h>
int main(void) {
    const int n = 9600;
    float *a, *b, *c, *reference;
    create_matrices(&a, &b, &c, &reference, n, n, n);
    matmul_v6(a, b, c, n, n, n);
    double start = omp_get_wtime(), elapsed;
    int repeats = 0;
    do {
        matmul_v6(a, b, c, n, n, n);
        ++repeats;
        elapsed = omp_get_wtime() - start;
    } while (elapsed < 45.0 || repeats < 3);
    printf("%.6f\n", elapsed / repeats);
    free(a); free(b); free(c); free(reference);
    return 0;
}
C
gcc -I . -O3 -march=native -funroll-loops -ffast-math -fopenmp \
    -DV6_OMP_AXIS_N=0 -DBLOCK_M=64 -DBLOCK_N=120 -DBLOCK_K=480 \
    "$tmp/q34.c" -o "$tmp/q34" -lopenblas -lm
export OMP_SCHEDULE=static,1
mkdir -p openmp_results
out=$(mktemp openmp_results/q34_9600_XXXXXX.csv)
echo "threads,mean_s,gflops,watts,gflops_per_watt,gflops_per_watt_above_idle" > "$out"
echo "Q34. Résultats dans $out. Relever la puissance stabilisée pendant chaque passage."
read -rp "Puissance au repos dans ce montage (W) : " idle
for t in 1 2 4 8 12 16 20 24; do
    echo "v6 en cours : $t thread(s), N=9600"
    seconds=$(OMP_NUM_THREADS="$t" "$tmp/q34")
    read -rp "Puissance moyenne relevée en W pour $t thread(s) : " watts
    python3 - "$t" "$seconds" "$watts" "$idle" "$out" <<'PY'
import csv, sys
t, seconds, watts, idle, path = sys.argv[1:]
power = float(watts.replace(",", "."))
baseline = float(idle.replace(",", "."))
if not 0 <= baseline < power:
    raise SystemExit("La puissance de calcul doit dépasser celle au repos.")
gflops = 2 * 9600**3 / (1e9 * float(seconds))
with open(path, "a", newline="") as f:
    csv.writer(f).writerow([t, seconds, gflops, power, gflops / power, gflops / (power - baseline)])
print(f"{seconds} s | {gflops:.2f} GFLOP/s | {gflops/power:.2f} GFLOP/J")
PY
done
python3 - "$out" <<'PY'
import csv, sys
with open(sys.argv[1]) as f:
    best = max(csv.DictReader(f), key=lambda row: float(row["gflops_per_watt"]))
print(f"Meilleur résultat mesuré : {best['threads']} threads, {float(best['gflops_per_watt']):.2f} GFLOP/J")
PY
