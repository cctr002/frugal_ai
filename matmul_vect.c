
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <cblas.h>
#include <tgmath.h>

#include <sys/time.h>

typedef float vec __attribute__((vector_size(32)));

struct timeval timer;

void init_timing(struct timeval* tstart)
{
	gettimeofday(tstart, NULL);
}

float elapsed_time(struct timeval tstart)
{
	struct timeval tmp;
	long long diff;
	gettimeofday(&tmp, NULL);
	diff = tmp.tv_usec - tstart.tv_usec;
	diff += (tmp.tv_sec - tstart.tv_sec) * 1000000;
	return ((float)diff*1.0e-6);
}


void create_matrices(float** A, float** B, float** C, float** C_blas, int M, int N, int K)
{
    size_t i;

    *A = (float*) calloc(M*K,sizeof(float));
    *B = (float*) calloc(K*N,sizeof(float));
    *C = (float*) calloc(M*N,sizeof(float));
    *C_blas = (float*) calloc(M*N,sizeof(float));

    for(i = 0; i < M*K; i++)
        (*A)[i] = ((float)rand()/RAND_MAX-0.5)*0.1;

    for(i = 0; i < K*N; i++)
        (*B)[i] = ((float)rand()/RAND_MAX-0.5)*0.1;
}


void matmul_blas(const float* A, const float* B, float* C, int M, int N, int K)
{
    float alpha = 1.0f, beta = 0.0f;

    cblas_sgemm(CblasColMajor, CblasNoTrans, CblasNoTrans,
        M, N, K, alpha, A, M, B, K, beta, C, M);
}


//Matmul using FMA operation on a sub-part of C and optimizing the cache usage
//No need for transposition in this version as most of the work is done in cache anyway

#ifndef ker_w
#define ker_w 6
#endif
#ifndef ker_h
#define ker_h 16
#endif
#if ker_h <= 0 || ker_h % 8 != 0 || ker_w <= 0
#error "ker_h must be a positive multiple of 8; ker_w must be positive"
#endif

void kernel(const float *_a, const float *_b, float *_c,
	int M, int N, int K, int i, int j, int k_start, int k_stop)
{
	int k, b_m, b_n, l;
	float val;
	(void)N;
	//declared in cache
	vec t[ker_h/8][ker_w] = {0};

	//1° Loop over k that do the vectorized accumulate inside the kernel region using an implicit fma instruction
	for (k = k_start; k < k_stop; k++) {
		// 1.1 Loop over ker_w
		for (b_n = 0; b_n < ker_w; b_n++) {

			// Broadcast the b[k] value into a beta vector
			val = _b[k + (j+b_n)*K];
			vec beta = {val, val, val, val, val, val, val, val};

			// 1.2 Loop over the vectors in A (ker_h/8)
			for (b_m = 0; b_m < ker_h/8; b_m++) {
				// Fill an alpha vector with the content of the current vector of A
				vec alpha;
				memcpy(&alpha, _a + i + 8*b_m + k*M, sizeof(alpha));
				// Accumulate alpha * beta into the current vector cell of t[][]. Doing so with vectors will implicitely call an FMA operation.
				t[b_m][b_n] += alpha * beta;
			}
		}
	}


	//2° accumulate the result in the corresponding region of C
	for (b_n = 0; b_n < ker_w; b_n++)
		for (b_m = 0; b_m < ker_h/8; b_m++)
			for (l = 0; l < 8; l++)
				_c[i + 8*b_m + l + (j+b_n)*M] += t[b_m][b_n][l];
}


void matmul_v5(const float *A, const float *B, float *C, int M, int N, int K)
{
	int i,j;

	if(M % ker_h != 0 || N % ker_w != 0)
	{
		printf("Error, mismatch between matrix size and kernel size");
		exit(EXIT_FAILURE);
	}

	//Simple loop over M and N kernel regions that call the kernel over the whole K dimension (k_start = 0, k_stop = K)
	for (size_t cell = 0; cell < (size_t)M*N; cell++) C[cell] = 0.0f;
	for (j = 0; j < N; j += ker_w)
		for (i = 0; i < M; i += ker_h)
			kernel(A, B, C, M, N, K, i, j, 0, K);

}



//V4 but with blocking decomposition to successively load sub parts of A and B
//into L2 and L1 cache for maximum reuse. Maximizing the achievable memory bandwith

#ifndef BLOCK_M
#define BLOCK_M 64
#endif
#ifndef BLOCK_N
#define BLOCK_N 120
#endif
#ifndef BLOCK_K
#define BLOCK_K 240
#endif

void matmul_v6(const float *A, const float *B, float *C, int M, int N, int K)
{
	int i,j,k;

	// Set the size of the blocks and order them by importance into the different cache levels
	// Keep in mind that we want l3 < l2 < l1 and ensure that each dimension is a multiple of the corresponding kernel size
	const int l3 = BLOCK_M; //Number of rows from A
	const int l2 = BLOCK_N; //Number of columns from B
	const int l1 = BLOCK_K; //Number of columns from A

	if(l3 <= 0 || l2 <= 0 || l1 <= 0 || M % ker_h != 0 || N % ker_w != 0 || l2 % ker_w != 0 || l3 % ker_h != 0)
	{
		printf("Error, mismatch between matrix size and kernel size");
		exit(EXIT_FAILURE);
	}

	//5-nested loop version that goes through the blocks in cache and then call the kernel on the sub regions in the current block
	for (size_t cell = 0; cell < (size_t)M*N; cell++) C[cell] = 0.0f;
	for (i = 0; i < M; i += l3) {
		int i_stop = i+l3 < M ? i+l3 : M;
		for (j = 0; j < N; j += l2) {
			int j_stop = j+l2 < N ? j+l2 : N;
			for (k = 0; k < K; k += l1) {
				int k_stop = k+l1 < K ? k+l1 : K;
				for (int ii = i; ii < i_stop; ii += ker_h)
					for (int jj = j; jj < j_stop; jj += ker_w)
						kernel(A, B, C, M, N, K, ii, jj, k, k_stop);
			}
		}
	}

}


int main(int argc, char *argv[])
{
	size_t i;

	int l_size, M, N, K;
	float *A, *B, *C, *C_blas;

	if (argc == 2)
		l_size = atoi(argv[1]);
	else
		l_size = 1920;

	M = l_size; N = l_size; K = l_size;

	create_matrices(&A, &B, &C, &C_blas, M, N, K);

	init_timing(&timer);

	matmul_blas(A,B,C_blas,M,N,K);

	printf("Regular sgemm time: %f s\n", elapsed_time(timer));

	init_timing(&timer);

	matmul_v6(A,B,C,M,N,K); //your custom matmul implementation

	printf("Custom sgemm time: %f s\n", elapsed_time(timer));

	//Verify the content of C against the OpenBLAS matmul
	for (i = 0; i < M*N; i++)
		if((C[i] - C_blas[i])*(C[i] - C_blas[i]) > 0.00001)
		{
			printf("ERROR ! MATRIX DIFF !\n");
			printf("i:%ld C:%f C_blas:%f\n", i, C[i], C_blas[i]);
			exit(EXIT_FAILURE);
		}
	exit(EXIT_SUCCESS);
}


