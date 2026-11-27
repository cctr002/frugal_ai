"""Run and compare the CUDA matrix multiplication experiments (Q35–40)."""

import argparse
import csv
import json
import math
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path
from statistics import mean, stdev
from tempfile import TemporaryDirectory

from C_python_wrapper import ENV, ROOT, compile_c, measure

GPU_MODES = ("fp32", "naive", "tiled", "tensor")
LABELS = {
    "fp32": "cuBLAS FP32", "naive": "CUDA naive", "tiled": "CUDA tiled",
    "tensor": "GemmEx FP16 / FP32 accumulation",
    "cpu_one": "OpenBLAS 1 thread", "cpu_multi": "OpenBLAS multicore",
}
FIELDS = ("mode", "size", "mean_s", "sd_s", "gflops", "threads", "device", "repeats")


def sizes_for(limit, step):
    return sorted(set(range(step, limit + 1, step)) | {limit, min(4096, limit)})


def record(writer, mode, size, avg, sd, device, repeats, threads=""):
    rate = 2 * size**3 / (avg * 1e9)
    writer.writerow((mode, size, avg, sd, rate, threads, device, repeats))
    print(f"{LABELS[mode]}, N={size}: {avg:.6g} ± {sd:.3g} s | {rate:.2f} GFLOP/s", flush=True)


def bench_gpu(args, sizes):
    if not shutil.which("nvcc") or not shutil.which("nvidia-smi"):
        raise SystemExit("GPU benchmark needs the CUDA toolkit (nvcc) and a visible NVIDIA GPU (nvidia-smi).")
    info = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=name,compute_cap", "--format=csv,noheader"], text=True
    ).splitlines()
    device, capability = (part.strip() for part in info[0].rsplit(",", 1))
    arch = args.arch or "sm_" + capability.replace(".", "")
    if not re.fullmatch(r"sm_\d+[a-z]?", arch):
        raise SystemExit(f"Invalid CUDA target {arch}. Specify --arch, e.g. sm_75 for T4.")
    print(f"GPU: {device} | target: {arch}", flush=True)
    with TemporaryDirectory() as tmp:
        binary = Path(tmp) / ("gpu_matmul.exe" if os.name == "nt" else "gpu_matmul")
        subprocess.run(["nvcc", "-O3", f"-arch={arch}", str(ROOT / "gpu_matmul.cu"),
                        "-o", str(binary), "-lcublas"], check=True)

        def times(mode, size, repeats):
            raw = subprocess.check_output([str(binary), mode, str(size), str(repeats)], text=True)
            samples = [float(line) for line in raw.splitlines()]
            if len(samples) != repeats or any(not math.isfinite(t) or t <= 0 for t in samples):
                raise ValueError(f"Invalid CUDA timings for {mode} at N={size}: {raw!r}")
            return mean(samples), stdev(samples) if repeats > 1 else 0

        # The executable checks every output at this size before the larger runs.
        for mode in GPU_MODES:
            times(mode, 64, 1)
        with (args.output / "gpu.csv").open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(FIELDS)
            for size in sizes:
                for mode in GPU_MODES:
                    avg, sd = times(mode, size, args.repeats)
                    record(writer, mode, size, avg, sd, device, args.repeats)
                file.flush()


def bench_cpu(args, sizes):
    if not shutil.which("gcc"):
        raise SystemExit("CPU benchmark needs GCC and OpenBLAS development headers and libraries.")
    available = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else os.cpu_count() or 1
    model = platform.processor() or platform.machine()
    if shutil.which("lscpu"):
        cpu_info = subprocess.check_output(["lscpu", "-J"], text=True, env={**os.environ, "LC_ALL": "C"})
        model = next((item["data"] for item in json.loads(cpu_info)["lscpu"]
                      if item["field"] == "Model name:"), model)
    reference = min(4096, args.max_size)
    with TemporaryDirectory() as tmp:
        binary = Path(tmp) / "matmul"
        compile_c(binary, "-O3")

        def times(size, threads):
            env = dict(ENV, OMP_NUM_THREADS=str(threads), OPENBLAS_NUM_THREADS=str(threads),
                       OMP_DYNAMIC="FALSE")
            # The second SGEMM in the existing binary follows the first-call warmup.
            avg, sd, _ = measure(binary, size, "OpenBLAS", args.repeats, env=env)
            return avg, sd

        one = times(reference, 1)
        if args.threads is None:
            candidates = sorted({available, *(n for n in (2, 4, 8, 12, 16, 20) if n <= available)})
            trials = {}
            for threads in candidates:
                trials[threads] = one if threads == 1 else times(reference, threads)
                print(f"OpenBLAS tuning | N={reference} | {threads} threads | {trials[threads][0]:.6g} s",
                      flush=True)
            threads = min(trials, key=lambda count: trials[count][0])
            multi = trials[threads]
        else:
            threads = args.threads
            multi = one if threads == 1 else times(reference, threads)
        print(f"CPU: {model} | OpenBLAS curve: {threads} threads", flush=True)
        with (args.output / "cpu.csv").open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(FIELDS)
            record(writer, "cpu_one", reference, *one, model, args.repeats, 1)
            for size in sizes:
                avg, sd = multi if size == reference else times(size, threads)
                record(writer, "cpu_multi", size, avg, sd, model, args.repeats, threads)
                file.flush()


def report(args):
    import matplotlib.pyplot as plt

    data = {}
    for file in (args.output / "gpu.csv", args.output / "cpu.csv"):
        if file.name == "cpu.csv" and not file.exists():
            print("CPU comparison unavailable. Copy cpu.csv from the CPU machine to this results folder.")
            continue
        with file.open(newline="", encoding="utf-8") as source:
            for row in csv.DictReader(source):
                data.setdefault(row["mode"], {})[int(row["size"])] = row

    def rate(row):
        return float(row["gflops"])

    def plot(filename, modes):
        fig, ax = plt.subplots(figsize=(10, 5))
        for mode in modes:
            if mode not in data:
                continue
            rows = sorted(data[mode].items())
            label = LABELS[mode]
            if mode.startswith("cpu_"):
                label += f" ({rows[0][1]['threads']} threads)"
            ax.plot([n for n, _ in rows], [rate(row) for _, row in rows], "o-", label=label)
        ax.set(xlabel="Matrix size N", ylabel="GFLOP/s (2N³ operations)", yscale="log")
        ax.legend()
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(args.output / filename, dpi=150)
        plt.close(fig)

    fp32 = data["fp32"]
    print("Q35, Q38–40 | N=4096")
    for mode, rows in data.items():
        if 4096 in rows:
            row = rows[4096]
            print(f"  {LABELS[mode]}: {float(row['mean_s']):.6g} s | {rate(row):.2f} GFLOP/s")
    if 4096 in fp32:
        for mode in ("cpu_one", "cpu_multi"):
            if 4096 in data.get(mode, {}):
                ratio = rate(fp32[4096]) / rate(data[mode][4096])
                print(f"Q35 | cuBLAS FP32 / {LABELS[mode]}: {ratio:.2f}x")
    for mode, question in (("naive", "Q38"), ("tiled", "Q39"), ("tensor", "Q40")):
        common = fp32.keys() & data.get(mode, {}).keys()
        if not common:
            continue
        ratios = {n: rate(data[mode][n]) / rate(fp32[n]) for n in common}
        peak = max(ratios, key=ratios.get)
        fastest = max(data[mode], key=lambda n: rate(data[mode][n]))
        print(f"{question} | {LABELS[mode]}: best relative throughput {ratios[peak]:.3f}x cuBLAS FP32"
              f" at N={peak}; peak absolute throughput at N={fastest}")
    print(f"Q40 | cuBLAS FP32 peak absolute throughput at N={max(fp32, key=lambda n: rate(fp32[n]))}")
    for mode, watts in (("fp32", args.gpu_watts), ("cpu_multi", args.cpu_watts)):
        if watts is not None and mode in data:
            n, row = max(data[mode].items(), key=lambda item: rate(item[1]))
            print(f"Q37 | {LABELS[mode]}: {rate(row)/watts:.2f} GFLOP/J at N={n} "
                  f"(constant-power estimate at {watts:g} W)")
    plot("q36_cpu_gpu.png", ("cpu_multi", "fp32"))
    plot("q38_q40_cuda.png", GPU_MODES)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("gpu", "cpu", "report"))
    parser.add_argument("--output", type=Path, default=Path("gpu_results"))
    parser.add_argument("--max-size", type=int, default=16384)
    parser.add_argument("--step", type=int, default=1024)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--threads", type=int, help="Force OpenBLAS curve thread count instead of tuning.")
    parser.add_argument("--arch", help="Override CUDA target, e.g. sm_75 for T4.")
    parser.add_argument("--gpu-watts", type=float)
    parser.add_argument("--cpu-watts", type=float)
    args = parser.parse_args()
    if not (64 <= args.step <= args.max_size <= 16384) or args.step % 64 or args.max_size % 64:
        parser.error("step and max-size must be multiples of 64, with 64 <= step <= max-size <= 16384")
    if args.repeats < 1 or (args.threads is not None and args.threads < 1):
        parser.error("repeats and threads must be positive")
    if any(w is not None and (not math.isfinite(w) or w <= 0) for w in (args.gpu_watts, args.cpu_watts)):
        parser.error("power must be finite and positive")
    if args.action == "report":
        report(args)
    else:
        args.output.mkdir(parents=True, exist_ok=True)
        (bench_gpu if args.action == "gpu" else bench_cpu)(args, sizes_for(args.max_size, args.step))


if __name__ == "__main__":
    main()
