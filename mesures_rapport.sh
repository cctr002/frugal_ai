#!/usr/bin/env bash
# À lancer depuis le poste Linux de la salle.
set -euo pipefail
cd "$(dirname "$0")"

# Les commandes longues partagent une échéance de 45 min.
SECONDS=0
budget=2700
limited() {
    local cap=$1 remaining=$((budget - SECONDS))
    shift
    if ((remaining <= 0)); then return 124; fi
    if ((cap > remaining)); then cap=$remaining; fi
    timeout --kill-after=3s "${cap}s" "$@"
}

for cmd in gcc python3 timeout; do command -v "$cmd" >/dev/null || { echo "$cmd manquant" >&2; exit 1; }; done
mkdir -p openmp_results
out=$(mktemp openmp_results/q34_9600_XXXXXX.csv)
timings="${out%.csv}_temps.txt"
echo "threads,mean_s,gflops,watts,gflops_per_watt,gflops_per_watt_above_idle" > "$out"
echo "Résultats : $out et $timings. Temps maximal : 45 min."
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 OMP_DYNAMIC=FALSE
if ! limited 240 python3 - <<'PY' | tee -a "$timings"
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
then echo "Q9 en échec ou hors délai. Suite avec Q34." >&2; fi

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
limited 60 gcc -I . -O3 -march=native -funroll-loops -ffast-math -fopenmp \
    -DV6_OMP_AXIS_N=0 -DBLOCK_M=64 -DBLOCK_N=120 -DBLOCK_K=480 \
    "$tmp/q34.c" -o "$tmp/q34" -lopenblas -lm
export OMP_SCHEDULE=static,1
# Relevés stabilisés de notes.md à N=9600, sur le même poste.
idle=20
declare -A power=([1]=63 [2]=86 [4]=136 [8]=171 [12]=170 [16]=162 [20]=157 [24]=166)
for t in 1 2 4 8 12 16 20 24; do
    if ((SECONDS >= budget)); then break; fi
    echo "v6 en cours : $t thread(s), N=9600"
    if seconds=$(limited 180 env OMP_NUM_THREADS="$t" "$tmp/q34"); then
        printf '%s threads : %s s\n' "$t" "$seconds" >> "$timings"
    else
        echo "$t threads : échec ou limite de 3 min, point ignoré." | tee -a "$timings" >&2
        continue
    fi
    watts=${power[$t]}
    python3 - "$t" "$seconds" "$watts" "$idle" "$out" <<'PY'
import csv, sys
t, seconds, watts, idle, path = sys.argv[1:]
power = float(watts)
baseline = float(idle)
gflops = 2 * 9600**3 / (1e9 * float(seconds))
eff = gflops / power
delta_eff = gflops / (power - baseline)
with open(path, "a", newline="") as f:
    csv.writer(f).writerow([t, seconds, gflops, power, eff, delta_eff])
print(f"{seconds} s | {gflops:.2f} GFLOP/s" + f" | {eff:.2f} GFLOP/J")
PY
done
python3 - "$out" <<'PY'
import csv, sys
with open(sys.argv[1]) as f:
    best = max((r for r in csv.DictReader(f) if r["gflops_per_watt"]),
               key=lambda r: float(r["gflops_per_watt"]), default=None)
if best:
    print(f"Meilleur résultat mesuré : {best['threads']} threads, {float(best['gflops_per_watt']):.2f} GFLOP/J")
PY
