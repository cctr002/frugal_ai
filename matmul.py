
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.system("export OMP_NUM_THREADS=1")
os.system("export OPENBLAS_NUM_THREADS=1")
os.system("export MKL_NUM_THREADS=1")
os.system("export NUMEXPR_NUM_THREADS=1")

import numpy as np
import time
from numba import jit
import matplotlib.pyplot as plt
from tqdm import tqdm

def matmul_naive(A, B, C, M, N, K):
	# Add your own naive 3-loop implementation here
	for i in range(M):
		for j in range(N):
			sum = 0.0
			for k in range(K):
				sum+= A[i][k]*B[k][j]
			C[i][j] = sum
	return C

@jit(nopython=True, cache=True, fastmath=False)
def matmul_naive_jit(A, B, C, M, N, K):
	# Add your own naive 3-loop implementation here
	for i in range(M):
		for j in range(N):
			sum = 0.0
			for k in range(K):
				sum+= A[i][k]*B[k][j]
			C[i][j] = sum
	return C

@jit(nopython=True, cache=True, fastmath=False)
def matmul_inner_numpy_jit(A, B, C, M, N, K):
	# Add your own naive 3-loop implementation here
	for i in range(M):
		for j in range(N):
			C[i][j] = (A[i,:]*B[:,j]).sum()
	return C

def matmul_inner_numpy(A, B, C, M, N, K):
	# Add your own naive 3-loop implementation here
	for i in range(M):
		for j in range(N):
			C[i][j] = (A[i,:]*B[:,j]).sum()
	return C

def matmul_at(A,B,C,M,N,K):
	C = A@B
	return C
def matmul_np_matmul(A,B,C,M,N,K):
	C = np.matmul(A,B)
	return C
def matmul_np_dot(A,B,C,M,N,K):
	C = np.dot(A,B)
	return C
def plot_compare_FLOPS(m_sizes,f_list,seed=0):
	np.random.seed(seed)
	time_list = [[] for i in range(len(f_list))]
	A = ((np.random.random((1,1))-0.5)*0.1).astype("float32")
	B = ((np.random.random((1,1))-0.5)-0.1).astype("float32")
	C =  np.zeros((1,1), dtype="float32")
	for i in range(len(f_list)):
		if "_jit" in f_list[i].__name__:
			f_list[i](A, B, C, 1, 1, 1)
	for m_size in tqdm(m_sizes) :
		print(f"processing {m_size}")
		M = m_size
		N = m_size
		K = m_size
		A = ((np.random.random((M,K))-0.5)*0.1).astype("float32")
		B = ((np.random.random((K,N))-0.5)-0.1).astype("float32")
		C_list =  [np.zeros((M,N), dtype="float32") for i in range(len(f_list))]
		C_verif = A@B
		for i,C in tqdm(enumerate(C_list)) :
			if f_list[i] is matmul_naive and m_size > 512:
				continue
			t_start = time.time()
			C = f_list[i](A, B, C, M, N, K)
			ellapsed_time = time.time() - t_start 
			if(np.sum((C - C_verif)**2) > 0.00001) :
				print(f"Error: results do not match!for {i}")
				raise Error
			time_list[i].append(ellapsed_time)
	for i in range(len(f_list)):
		plt.plot(m_sizes[:len(time_list[i])],(np.array(m_sizes[:len(time_list[i])])**3)/(np.array(time_list[i])*10**9),label=f_list[i].__name__)
	plt.yscale("log")
	plt.legend()
	plt.xlabel("m_size")
	plt.ylabel("GFLOPs")
	plt.show()

if __name__ == "__main__":
	m_sizes6 = [i*128 for i in range(1,16)]
	f_list6 = [matmul_naive,matmul_naive_jit,matmul_inner_numpy,matmul_inner_numpy_jit]
	m_sizes7 = [96+i*128 for i in range(0,15)]
	f_list7 = [matmul_naive_jit,matmul_inner_numpy,matmul_inner_numpy_jit]
	m_sizes8 = [i*128 for i in range(1,4096//128+1)]
	f_list8 = [matmul_at,matmul_np_matmul,matmul_np_dot]
	
	plot_compare_FLOPS(m_sizes8,f_list8)




