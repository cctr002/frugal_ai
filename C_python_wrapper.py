import csv
import os
import shlex
import subprocess
from itertools import combinations
from pathlib import Path
from statistics import mean, stdev
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent
ENV = {**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"}


def compile_c(executable, flags):
    subprocess.run(
        ["gcc", "matmul.c", *shlex.split(flags), "-o", str(executable), "-lopenblas", "-lm"],
        cwd=ROOT, check=True,
    )


def measure(executable, size, version, repeats=3):
    """Return custom mean, sample standard deviation, and OpenBLAS mean (seconds)."""
    times, blas_times = [], []
    for _ in range(repeats):
        output = subprocess.check_output(
            [str(executable), str(size), version], cwd=ROOT, env=ENV, text=True,
        )
        blas_time, custom_time = [float(line.split()[-2]) for line in output.splitlines()]
        if min(blas_time, custom_time) <= 0:
            raise ValueError("Measurement too short: increase the matrix size.")
        blas_times.append(blas_time)
        times.append(custom_time)
    return mean(times), stdev(times) if repeats > 1 else 0, mean(blas_times)


def search_flags(question, size=1920):
    """Print five-run measurements for every compilation combination requested."""
    versions = {
        10: ["matmul_v1"],
        12: ["matmul_v2"],
        14: ["matmul_v3"],
        16: ["matmul_v3"],
        19: ["matmul_v4"],
    }[question]
    flags = ["", "-O1", "-O2", "-O3"]
    if question == 16:
        extra = ["-march=native", "-funroll-loops", "-ffast-math"]
        flags = [" ".join(("-O3", *combo))
                 for n in range(len(extra)+1) for combo in combinations(extra, n)]
    if question == 19:
        extra = ["-march=native", "-funroll-loops", "-ffast-math"]
        flags.append("-O3 -march=native -funroll-loops -ffast-math")
    with TemporaryDirectory() as directory:
        executable = Path(directory) / "matmul"
        for options in flags:
            compile_c(executable, options)
            print(f"\nQ{question} | size={size} | {options or 'no flags'}", flush=True)
            for version in versions:
                avg, sd, blas = measure(executable, size, version)
                print(f"{version}: {avg:.6f} +/- {sd:.6f} s (sample SD, 3 runs)"
                      f" | {100*blas/avg:.2f}% of OpenBLAS performance", flush=True)


def plot_compare_FLOPS(m_sizes, versions, name="matmul", repeats=3):
    """versions is a list of (C implementation, compilation flags) pairs."""
    import matplotlib.pyplot as plt

    m_sizes = list(m_sizes)
    fig, ax = plt.subplots()
    with TemporaryDirectory() as directory, open(f"{name}.csv", "w", newline="") as data:
        executable = Path(directory) / "matmul"
        writer = csv.writer(data)
        writer.writerow(["version", "size", "flags", "time_mean_s", "time_sd_s", "gflops"])
        for version, flags in versions:
            compile_c(executable, flags)
            speeds = []
            for size in m_sizes:
                avg, sd, _ = measure(executable, size, version, repeats)
                speed = size**3 / (avg*1e9) 
                speeds.append(speed)
                writer.writerow([version, size, flags, avg, sd, speed])
                print(f"{version}, N={size}: {avg:.6f} +/- {sd:.6f} s", flush=True)
            ax.plot(m_sizes, speeds, label=f"{version} {flags}".strip())
    ax.set_yscale("log")
    ax.set_xlabel("m_size")
    ax.set_ylabel("GFLOPs")
    ax.legend()
    fig.savefig(f"{name}.png")
    plt.show()
    search_flags()

if __name__ == "__main__":
    search_flags(19)
    # v1 = ("matmul_v1", "-O2")
    # v2 = ("matmul_v2", "-O1")
    # v3_q15 = ("matmul_v3", "-O2")
    # v3_q17 = ("matmul_v3", "-O3 -march=native -funroll-loops -ffast-math")
    # blas = ("OpenBLAS", "-O2")
    # plot_compare_FLOPS(range(128, 1921, 128),
                    #    versions=[v1, v2], name="q11_13")
    # plot_compare_FLOPS(range(128, 4097, 128),
                    #    versions=[v3_q15, v3_q17, blas], name="q15_17")



