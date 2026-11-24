
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <cblas.h>
#include <tgmath.h>

#include <sys/time.h>

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


//Naive triple loop matmul
void matmul_v1(const float *A, const float *B, float *C, int M, int N, int K)
{
	int i, j, k;
	for(i=0; i<M; i++) {
		for(j=0; j<N; j++) {
			float sum = 0.0f;
			for(k=0; k<K; k++) {
				C[i + j*M] += A[i + k*M] * B[k + j*K];
			}
		}
	}
}

void matmul_v2(const float *A, const float *B, float *C, int M, int N, int K)
{
	int i, j, k;
	for(i=0; i<M; i++) {
		for(j=0; j<N; j++) {
			float sum = 0.0f;
			for(k=0; k<K; k++) {
				sum += A[i + k*M] * B[k + j*K];
			}
			C[i + j*M] = sum;
		}
	}
}

// Q14: transpose A so both reads in the inner loop are contiguous.
void matmul_v3(const float *A, const float *B, float *C, int M, int N, int K)
{
	float *AT = malloc((size_t)M*K*sizeof(float));
	if (!AT) { perror("AT"); exit(EXIT_FAILURE); }
	for (int i = 0; i < M; i++)
		for (int k = 0; k < K; k++)
			AT[k + i*K] = A[i + k*M];
	for (int j = 0; j < N; j++)
		for (int i = 0; i < M; i++) {
			float sum = 0.0f;
			for (int k = 0; k < K; k++)
				sum += AT[k + i*K] * B[k + j*K];
			C[i + j*M] = sum;
		}
	free(AT);
}


//v3 + manual vectorization through memory aligned SIMD operations 
//Note, require C11 ISO, not compatible with C99 while auto vectorization is compatible

// Define a memory aligned vector type of 32 Bytes -> 8 float of 4 bytes (32 bits) each
typedef float vec __attribute__ (( vector_size(32) ));

void matmul_v4(const float *A, const float *B, float *C, int M, int N, int K)
{
	if(K % 8 != 0)
	{
		printf("Error, mismatch between matrix size and kernel size");
		exit(EXIT_FAILURE);
	}
	
	//1° Create the vectorized versions of A and B
	typedef float vec __attribute__((vector_size(32)));

	int n_vectors = K/8;
	vec *AT_vec = aligned_alloc(sizeof(vec), (size_t)M* n_vectors* sizeof(vec));
	vec *B_vec = aligned_alloc(sizeof(vec), (size_t)N* n_vectors* sizeof(vec));
	
	//2° Fill the vectorized versions
	for (int i = 0; i<M; i++) {
		for(int v= 0; v<n_vectors;v++) {
			for (int lane =0; lane < 8 ; lane++) {
				int k = 8*v +lane;
				AT_vec[i*n_vectors+v][lane] = A[i+k*M];
			}
		}
	}
	for (int j = 0; j<N; j++) {
		for(int v= 0; v<n_vectors;v++) {
			for (int lane =0; lane < 8 ; lane++) {
				int k = 8*v +lane;
				B_vec[j*n_vectors+v][lane] = B[k + j*K];
			}
		}
	}
	//3° Do the i,j,k loops with the vectorized accumulate loop over k and fill the corresponding cell of C
	for (int j=0;j<N;j++){
		for ( int i=0;i<M;i++){
			vec acc = {0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
			for(int v=0;v<n_vectors;v++){
				acc+= AT_vec[v+i*n_vectors]*B_vec[v+j*n_vectors];
			}
			float sum = 0.0f;
			for(int l=0;l<8;l++){
				sum+=acc[l];
			}
			C[i+j*M] = sum;
		}
	}
	free(AT_vec);
	free(B_vec);
}	



int main(int argc, char *argv[])
{
	size_t i;
	
	int l_size, M, N, K;
	float *A, *B, *C, *C_blas;

	if (argc >= 2)
		l_size = atoi(argv[1]);
	else
		l_size = 512;
	
	void (*matmul)(const float *, const float *, float *, int, int, int) = matmul_v1;
	if (argc >= 3) {
		if (strcmp(argv[2], "matmul_v2") == 0) matmul = matmul_v2;
		else if (strcmp(argv[2], "matmul_v3") == 0) matmul = matmul_v3;
		else if (strcmp(argv[2], "OpenBLAS") == 0) matmul = matmul_blas;
		else if (strcmp(argv[2], "matmul_v4") ==0) matmul = matmul_v4;
		else if (strcmp(argv[2], "matmul_v1") != 0) {
			fprintf(stderr, "Unknown implementation: %s\n", argv[2]);
			return EXIT_FAILURE;
		}
	}

	M = l_size; N = l_size; K = l_size;

	create_matrices(&A, &B, &C, &C_blas, M, N, K);

	init_timing(&timer);

	matmul_blas(A,B,C_blas,M,N,K);

	printf("Regular sgemm time: %f s\n", elapsed_time(timer));

	init_timing(&timer);

	matmul(A,B,C,M,N,K); // selected implementation; v1 by default
	
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

		
		
