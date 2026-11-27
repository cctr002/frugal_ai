import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import numpy as np
import time
from numba import jit
import matplotlib.pyplot as plt
from tqdm import tqdm

def matmul_naive(A, B, C, M, N, K):
	for i in range(M):
		for j in range(N):
			sum = 0.0
			for k in range(K):
				sum+= A[i][k]*B[k][j]
			C[i][j] = sum
	return C

@jit(nopython=True, cache=True, fastmath=False)
def matmul_naive_jit(A, B, C, M, N, K):
	for i in range(M):
		for j in range(N):
			sum = 0.0
			for k in range(K):
				sum+= A[i][k]*B[k][j]
			C[i][j] = sum
	return C

@jit(nopython=True, cache=True, fastmath=False)
def matmul_inner_numpy_jit(A, B, C, M, N, K):
	for i in range(M):
		for j in range(N):
			C[i][j] = (A[i,:]*B[:,j]).sum()
	return C

def matmul_inner_numpy(A, B, C, M, N, K):
	for i in range(M):
		for j in range(N):
			C[i][j] = (A[i,:]*B[:,j]).sum()
	return C

def matmul_at(A, B, C, M, N, K):
    return A @ B


def matmul_np_matmul(A, B, C, M, N, K):
    return np.matmul(A, B)


def matmul_np_dot(A, B, C, M, N, K):
    return np.dot(A, B)


def plot_compare_FLOPS(m_sizes, f_list, seed=0):
    rng = np.random.RandomState(seed)
    sizes = {fn: [] for fn in f_list}
    rates = {fn: [] for fn in f_list}
    warm = np.zeros((1, 1), dtype=np.float32)
    for fn in f_list:
        if hasattr(fn, "py_func"):
            fn(warm, warm, warm.copy(), 1, 1, 1)

    for n in tqdm(m_sizes):
        A = ((rng.random((n, n)) - 0.5) * 0.1).astype("float32")
        B = ((rng.random((n, n)) - 0.5) - 0.1).astype("float32")
        expected = A @ B
        for fn in f_list:
            if fn is matmul_naive and n > 512:
                continue
            C = np.zeros_like(expected)
            start = time.perf_counter()
            result = fn(A, B, C, n, n, n)
            seconds = time.perf_counter() - start
            if not np.sum((result - expected)**2) <= 0.00001:
                raise ValueError(f"{fn.__name__}: résultat incorrect pour N={n}")
            sizes[fn].append(n)
            rates[fn].append(n**3 / (seconds * 1e9))

    for fn in f_list:
        plt.plot(sizes[fn], rates[fn], label=fn.__name__)
    plt.yscale("log")
    plt.legend()
    plt.xlabel("m_size")
    plt.ylabel("GFLOPs")
    plt.show()


if __name__ == "__main__":
    plot_compare_FLOPS(range(128, 4097, 128), [matmul_at, matmul_np_matmul, matmul_np_dot])
