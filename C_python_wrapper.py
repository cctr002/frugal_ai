import csv
import os
import shlex
import subprocess
from itertools import combinations, product
from pathlib import Path
from statistics import mean, stdev
from tempfile import TemporaryDirectory
import time 
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
        22: ["matmul_v3", "matmul_v4", "matmul_v5"],
        25: ["matmul_v4", "matmul_v5", "matmul_v6"],
    }[question]
    flags = ["", "-O1", "-O2", "-O3"]
    if question == 16:
        extra = ["-march=native", "-funroll-loops", "-ffast-math"]
        flags = [" ".join(("-O3", *combo))
                 for n in range(len(extra)+1) for combo in combinations(extra, n)]
    if question in (19, 22):
        extra = ["-march=native", "-funroll-loops", "-ffast-math"]
        flags.append("-O3 -march=native -funroll-loops -ffast-math")
    if question == 25:
        flags = ["-O3 -march=native -funroll-loops -ffast-math"]
    with TemporaryDirectory() as directory:
        executable = Path(directory) / "matmul"
        for options in flags:
            compile_c(executable, options)
            print(f"\nQ{question} | size={size} | {options or 'no flags'}", flush=True)
            for version in versions:
                avg, sd, blas = measure(executable, size, version)
                print(f"{version}: {avg:.6f} +/- {sd:.6f} s (sample SD, 3 runs)"
                        f" | {100*blas/avg:.2f}% of OpenBLAS performance", flush=True)


def test_kernel_sizes(sizes=(240, 1920), kernels=((8, 6), (16, 6), (16, 8)),
                      flags="-O3 -march=native -funroll-loops -ffast-math"):
    """Q24: compare kernel dimensions at one small and one large matrix size."""
    with TemporaryDirectory() as directory:
        executable = Path(directory) / "matmul"
        for height, width in kernels:
            if height <= 0 or height % 8 or width <= 0 or any(
                    size % height or size % width for size in sizes):
                raise ValueError("Sizes must be multiples of kernel height and width; height must be a multiple of 8.")
            compile_c(executable, f"{flags} -Dker_h={height} -Dker_w={width}")
            print(f"\nKernel {height}x{width}: {height//8*width} vector accumulators", flush=True)
            for size in sizes:
                avg, sd, blas = measure(executable, size, "matmul_v5")
                print(f"N={size}: {avg:.6f} +/- {sd:.6f} s"
                      f" | {100*blas/avg:.2f}% of OpenBLAS performance", flush=True)


def search_blocks(size=1920, rows=(32, 64, 128), columns=(60, 120, 240),
                  depths=(120, 240, 480), height=16, width=6,
                  flags="-O3 -march=native -funroll-loops -ffast-math"):
    """Q26: explore valid bK > bN > bM combinations; return the fastest blocks."""
    if height <= 0 or height % 8 or width <= 0 or size % height or size % width:
        raise ValueError("Matrix size must match the kernel; height must be a multiple of 8.")
    best_time, best_blocks = float("inf"), None
    with TemporaryDirectory() as directory:
        executable = Path(directory) / "matmul"
        for bm, bn, bk in product(rows, columns, depths):
            if not (0 < bm < bn < bk) or bm % height or bn % width:
                continue
            options = (f"{flags} -Dker_h={height} -Dker_w={width}"
                       f" -DBLOCK_M={bm} -DBLOCK_N={bn} -DBLOCK_K={bk}")
            compile_c(executable, options)
            avg, sd, blas = measure(executable, size, "matmul_v6")
            print(f"Q26 | blocks={bm},{bn},{bk} | {avg:.6f} +/- {sd:.6f} s"
                  f" | {100*blas/avg:.2f}% of OpenBLAS performance", flush=True)
            if avg < best_time:
                best_time, best_blocks = avg, (bm, bn, bk)
    if best_blocks is None:
        raise ValueError("No valid block combination for this kernel.")
    print(f"Best blocks: {best_blocks}, mean time {best_time:.6f} s", flush=True)
    return best_blocks


def plot_compare_FLOPS(m_sizes, versions, name="matmul", repeats=3):
    """versions is a list of (C implementation, compilation flags) pairs."""
    import matplotlib.pyplot as plt

    m_sizes = list(m_sizes)
    fig, ax = plt.subplots(figsize=(12, 6))
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
    fig.tight_layout()
    fig.savefig(f"{name}.png")
    plt.show()

if __name__ == "__main__":
    # Q25 -> Q26 -> Q27, in order.
    search_flags(25)
    best_flags = "-O3 -march=native -funroll-loops -ffast-math"
    height, width = 16, 6
    bm, bn, bk = search_blocks(height=height, width=width, flags=best_flags)
    v6_flags = (f"{best_flags} -Dker_h={height} -Dker_w={width}"
                f" -DBLOCK_M={bm} -DBLOCK_N={bn} -DBLOCK_K={bk}")
    plot_compare_FLOPS(range(48, 3841, 48),
        versions=[("matmul_v4", best_flags), ("matmul_v5", best_flags),
                  ("matmul_v6", v6_flags), ("OpenBLAS", "-O2")], name="q27")
    # search_flags(22)
    # Q24: test_kernel_sizes()
    # Q23: replace these flags with the best configuration measured in Q22.
    # best_flags = "-O3 -march=native -funroll-loops -ffast-math"
    # plot_compare_FLOPS(range(48, 3841, 48),
    #     versions=[("matmul_v4", best_flags), ("matmul_v5", best_flags),
    #               ("OpenBLAS", "-O2")], name="q23")
    # search_flags(19)
    # v1 = ("matmul_v1", "-O2")
    # v2 = ("matmul_v2", "-O1")
    # v3_q15 = ("matmul_v3", "-O2")
    # v3_q17 = ("matmul_v3", "-O3 -march=native -funroll-loops -ffast-math")
    v4_q19 = ("matmul_v4", "-O3 -march=native -funroll-loops -ffast-math")
    blas = ("OpenBLAS", "-O2")
    # plot_compare_FLOPS(range(128, 1921, 128),
                    #    versions=[v1, v2], name="q11_13")
    # plot_compare_FLOPS(range(128, 4097, 128),
    #                    versions=[v4_q19, blas], name="q19")



