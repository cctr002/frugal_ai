"""Run CPU questions 28–34 using the existing matmul benchmark."""

import argparse
import csv
import math
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from C_python_wrapper import ENV, FAST_FLAGS, compile_c, measure


def cpu_counts():
    allowed = os.sched_getaffinity(0)
    topology = subprocess.check_output(["lscpu", "-p=CPU,CORE,SOCKET"], text=True)
    rows = (line for line in topology.splitlines() if line and not line.startswith("#"))
    cores = set()
    for row in rows:
        cpu, core, socket = map(int, row.split(","))
        if cpu in allowed:
            cores.add((core, socket))
    return len(cores), len(allowed)


def run(size, blocks, counts, physical, repeats, output):
    import matplotlib.pyplot as plt

    bm, bn, bk = blocks
    if size <= 0 or size % 48 or bm <= 0 or bm % 16 or bn <= 0 or bn % 6 or bk <= 0:
        raise ValueError("Use a positive size divisible by 48, bM divisible by 16 and bN divisible by 6.")
    if repeats < 1 or physical < 1 or any(p < 1 for p in counts):
        raise ValueError("Thread counts and repeats must be positive.")
    counts = sorted(set(counts) | {1, physical})
    output.mkdir(parents=True, exist_ok=True)
    flags = f"{FAST_FLAGS} -DBLOCK_M={bm} -DBLOCK_N={bn} -DBLOCK_K={bk}"

    def timed(executable, threads=1, schedule="static", version="matmul_v6", blas_threads=1):
        env = dict(ENV, OMP_NUM_THREADS=str(threads), OMP_SCHEDULE=schedule,
                   OPENBLAS_NUM_THREADS=str(blas_threads), OMP_DYNAMIC="FALSE")
        avg, sd, _ = measure(executable, size, version, repeats, env=env)
        return avg, sd

    def save_plot(name, xlabel, ylabel, x, *curves):
        fig, ax = plt.subplots()
        for label, values in curves:
            ax.plot(x, values, "o-", label=label)
        ax.set(xlabel=xlabel, ylabel=ylabel)
        ax.legend()
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(output / f"{name}.png")
        plt.close(fig)

    work = 2 * size**3 / 1e9  # GEMM, two FLOPs per multiply-add.
    with TemporaryDirectory() as directory:
        binaries = {axis: Path(directory) / f"omp_{axis}" for axis in ("M", "N")}
        for axis, executable in binaries.items():
            compile_c(executable, f"{flags} -DV6_OMP_AXIS_N={int(axis == 'N')} -fopenmp")

        with (output / "q28_q29.csv").open("w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["question", "size", "axis", "schedule", "threads", "mean_s", "sd_s"])

            def compare(question, axis, schedule):
                avg, sd = timed(binaries[axis], threads=2, schedule=schedule)
                writer.writerow([question, size, axis, schedule, 2, avg, sd])
                print(f"Q{question} | {axis} | {schedule:10} | {avg:.6f} ± {sd:.6f} s", flush=True)
                return avg

            axis = min(binaries, key=lambda candidate: compare(28, candidate, "static"))
            schedules = ["static"] + [f"{kind},{chunk}" for kind in ("static", "dynamic", "guided")
                                       for chunk in (1, 2, 4)]
            schedule = min(schedules, key=lambda candidate: compare(29, axis, candidate))

        print(f"Q30 | axis={axis}, schedule={schedule}, blocks={blocks}", flush=True)
        timings = []
        for threads in counts:
            avg, sd = timed(binaries[axis], threads, schedule)
            timings.append((avg, sd))
            print(f"  {threads:2} threads | {avg:.6f} ± {sd:.6f} s | {work/avg:.2f} GFLOP/s",
                  flush=True)

        sequential = Path(directory) / "sequential"
        compile_c(sequential, f"{flags} -DV6_OMP_AXIS_N={int(axis == 'N')}")
        seq, seq_sd = timed(sequential)
        one, one_sd = timings[0]
        print(f"Q31 | without OpenMP {seq:.6f} ± {seq_sd:.6f} s | "
              f"OpenMP 1 thread {one:.6f} ± {one_sd:.6f} s", flush=True)
        throughputs = [work / avg for avg, _ in timings]
        speedup_seq = [seq / avg for avg, _ in timings]
        speedup_omp = [one / avg for avg, _ in timings]
        with (output / "q30_q32.csv").open("w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["size", "axis", "schedule", "block_m", "block_n", "block_k",
                             "threads", "mean_s", "sd_s", "gflops",
                             "seq_mean_s", "seq_sd_s", "omp_one_mean_s", "omp_one_sd_s",
                             "speedup_seq", "speedup_omp"])
            for p, (avg, sd), rate, s_seq, s_omp in zip(counts, timings, throughputs, speedup_seq, speedup_omp):
                writer.writerow([size, axis, schedule, bm, bn, bk, p, avg, sd, rate, seq, seq_sd,
                                 one, one_sd, s_seq, s_omp])
        save_plot("q30", "OpenMP threads", "GFLOP/s", counts, ("v6", throughputs))
        save_plot("q32", "OpenMP threads", "Speedup", counts,
                  ("Without OpenMP", speedup_seq), ("OpenMP, 1 thread", speedup_omp))

        cpu_time = timings[counts.index(physical)][0]
        blas_one, _ = timed(sequential, version="OpenBLAS")
        blas_many, _ = timed(sequential, version="OpenBLAS", blas_threads=physical)
        print(f"Q33 | E({physical}) / E(1), assuming twice the power | "
              f"v6={2*cpu_time/one:.3f} | OpenBLAS={2*blas_many/blas_one:.3f}", flush=True)

    print("Q34 | Supply wattmeter readings with --power-csv (columns: threads,watts).", flush=True)


def power_efficiency(output, powers):
    """Combine wattmeter readings with the saved Q30 measurements."""
    import matplotlib.pyplot as plt

    with (output / "q30_q32.csv").open(newline="") as file:
        timings = {int(row["threads"]): (float(row["mean_s"]), float(row["gflops"]))
                   for row in csv.DictReader(file)}
    with powers.open(newline="") as file:
        watts = {int(row["threads"]): float(row["watts"]) for row in csv.DictReader(file)}
    if not watts or set(watts) - set(timings) or any(not math.isfinite(w) or w <= 0 for w in watts.values()):
        raise ValueError("Q34 needs positive wattmeter readings for tested thread counts.")
    measured = [(p, timings[p][0], watts[p], timings[p][1] / watts[p]) for p in sorted(watts)]
    with (output / "q34.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["threads", "mean_s", "watts", "gflops_per_watt"])
        writer.writerows(measured)
    best = max(measured, key=lambda row: row[3])
    print(f"Q34 | best measured efficiency: {best[0]} threads, {best[3]:.3f} GFLOP/J", flush=True)
    fig, ax = plt.subplots()
    ax.plot([row[0] for row in measured], [row[3] for row in measured], "o-")
    ax.set(xlabel="OpenMP threads", ylabel="GFLOP/J")
    fig.tight_layout()
    fig.savefig(output / "q34.png")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=1920)
    parser.add_argument("--blocks", type=int, nargs=3, metavar=("BM", "BN", "BK"), default=(64, 120, 240))
    parser.add_argument("--threads", type=int, nargs="+")
    parser.add_argument("--physical-cores", type=int)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("openmp_results"))
    parser.add_argument("--power-csv", type=Path, help="Q34 wattmeter readings with columns threads,watts")
    args = parser.parse_args()
    if args.power_csv is not None:
        power_efficiency(args.output, args.power_csv)
    else:
        physical, logical = cpu_counts()
        physical = physical if args.physical_cores is None else args.physical_cores
        counts = args.threads or [p for p in (1, 2, 4, 8, 12, 16) if p <= logical] + [logical, logical + 4]
        print(f"CPU available: {physical} physical cores used as Q33 target, {logical} logical CPUs")
        run(args.size, args.blocks, counts, physical, args.repeats, args.output)
