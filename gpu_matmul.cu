// The tiled kernel below is adapted from GPU_matmul_demo.ipynb.
#include <cuda_runtime.h>
#include <cuda_fp16.h>
#include <cublas_v2.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <string>
#include <vector>

#define CUDA(call) do { \
    cudaError_t status = (call); \
    if (status != cudaSuccess) { \
        fprintf(stderr, "%s: %s\n", #call, cudaGetErrorString(status)); \
        exit(EXIT_FAILURE); \
    } \
} while (0)
#define BLAS(call) do { \
    cublasStatus_t status = (call); \
    if (status != CUBLAS_STATUS_SUCCESS) { \
        fprintf(stderr, "%s: cuBLAS status %d\n", #call, int(status)); \
        exit(EXIT_FAILURE); \
    } \
} while (0)

__global__ void naive(const float *at, const float *b, float *c, int n)
{
    unsigned id = blockIdx.x * blockDim.x + threadIdx.x;
    if (id >= unsigned(n)*n) return;
    int row = id % n, col = id / n;
    float sum = 0.0f;
    for (int k = 0; k < n; ++k)
        sum += at[row*n+k] * b[col*n+k];
    c[id] = sum;
}


#define BlockDimM 64
#define BlockDimN 64
#define BlockDimK 4

#define WarpDimM 32
#define WarpDimN 16

#define ThreadDimM 4
#define ThreadDimN 4


__global__ void custom_sgemm(const float *A, const float *B, float *C, int M, int K)
{

    int block_row = blockIdx.x;
    int block_col = blockIdx.y;

    float frag_a[ThreadDimM];
    float frag_b[ThreadDimN];

    float accumulator[ThreadDimN][ThreadDimM];

    int c_id = threadIdx.y*blockDim.x + threadIdx.x;
    int warp_id = c_id / 32;
    int thread_id = c_id % 32;

    int warp_x = warp_id / (BlockDimM/WarpDimM);
    int warp_y = warp_id % (BlockDimM/WarpDimM);

    int frag_x = thread_id / (WarpDimM/ThreadDimM);
    int frag_y = thread_id % (WarpDimM/ThreadDimM);

    const float *data_block_A;
    const float *data_block_B;
    float *data_block_C;

    __shared__ float As[BlockDimK][BlockDimM];
    __shared__ float Bs[BlockDimN][BlockDimK];

    int l, e_per_th, p_x, p_y;

    data_block_C = &C[block_col*BlockDimN*M + block_row*BlockDimM];

    #pragma unroll
    for(int thread_x = 0; thread_x < ThreadDimN; thread_x ++)
      #pragma unroll
      for(int thread_y = 0; thread_y < ThreadDimM; thread_y++)
        accumulator[thread_x][thread_y] = 0.0f;

    for(int block_k = 0; block_k < (K/BlockDimK); block_k++)
    {
      data_block_A = &A[block_k*BlockDimK*M + block_row*BlockDimM];
      data_block_B = &B[block_col*BlockDimN*K + block_k*BlockDimK];

      e_per_th = (BlockDimM*BlockDimK)/(blockDim.x*blockDim.y);
      for(l = 0; l < e_per_th; l++)
      {
        p_x = (c_id*e_per_th + l)/BlockDimM;
        p_y = (c_id*e_per_th + l)%BlockDimM;

        As[p_x][p_y] = data_block_A[p_x*M + p_y];
      }

      e_per_th = (BlockDimN*BlockDimK)/(blockDim.x*blockDim.y);
      for(l = 0; l < e_per_th; l++)
      {
        p_x = (c_id*e_per_th + l)/BlockDimK;
        p_y = (c_id*e_per_th + l)%BlockDimK;

        Bs[p_x][p_y] = data_block_B[p_x*K + p_y];
      }

      __syncthreads();

      #pragma unroll
      for(int warp_k = 0; warp_k < BlockDimK; warp_k++)
      {
        #pragma unroll
        for(int thread_y = 0; thread_y < ThreadDimM; thread_y++)
          frag_a[thread_y] = As[warp_k][warp_y*WarpDimM + frag_y*ThreadDimM + thread_y];
        #pragma unroll
        for(int thread_x = 0; thread_x < ThreadDimN; thread_x ++)
          frag_b[thread_x] = Bs[warp_x*WarpDimN + frag_x*ThreadDimN + thread_x][warp_k];

        #pragma unroll
        for(int thread_x = 0; thread_x < ThreadDimN; thread_x ++)
          #pragma unroll
          for(int thread_y = 0; thread_y < ThreadDimM; thread_y++)
            accumulator[thread_x][thread_y] +=
              frag_a[thread_y]*frag_b[thread_x];
      }
      __syncthreads();
    }

    #pragma unroll
    for(int thread_x = 0; thread_x < ThreadDimN; thread_x ++)
    {

      #pragma unroll
      for(int thread_y = 0; thread_y < ThreadDimM; thread_y++)

        data_block_C[(warp_x*WarpDimN + frag_x*ThreadDimN + thread_x)*M + (warp_y*WarpDimM + frag_y*ThreadDimM + thread_y)] =
          accumulator[thread_x][thread_y];
    }

}
template <typename T>
static T *device_copy(const std::vector<T> &values)
{
    T *dst;
    CUDA(cudaMalloc(&dst, values.size() * sizeof(T)));
    CUDA(cudaMemcpy(dst, values.data(), values.size() * sizeof(T), cudaMemcpyHostToDevice));
    return dst;
}

// Check every cell on a small problem, and sample the corners and interior on large ones.
template <typename T>
static void validate(const T *result, const std::vector<float> &a,
                     const std::vector<float> &b, int n, bool mixed)
{
    int samples = n <= 64 ? n*n : 36;
    const int points[] = {0, 1, n/3, n/2, n-2, n-1};
    for (int sample = 0; sample < samples; ++sample) {
        int i = n <= 64 ? sample % n : points[sample % 6];
        int j = n <= 64 ? sample / n : points[sample / 6];
        double expected = 0;
        for (int k = 0; k < n; ++k)
            expected += double(a[i + k*n]) * b[k + j*n];
        T cell;
        CUDA(cudaMemcpy(&cell, result + i + j*n, sizeof(T), cudaMemcpyDeviceToHost));
        double actual = float(cell);
        double tolerance = mixed ? 0.00002 + 0.001*std::abs(expected) : 0.00002 + 0.0002*std::abs(expected);
        if (!std::isfinite(actual) || std::abs(actual - expected) > tolerance) {
            fprintf(stderr, "C[%d,%d]: expected %.9g, got %.9g (tolerance %.3g)\n",
                    i, j, expected, actual, tolerance);
            exit(EXIT_FAILURE);
        }
    }
}

int main(int argc, char **argv)
{
    if (argc != 4) {
        fprintf(stderr, "Usage: %s {fp32|naive|tiled|tensor} size repeats\n", argv[0]);
        return EXIT_FAILURE;
    }
    std::string mode = argv[1];
    int n = atoi(argv[2]), repeats = atoi(argv[3]);
    if ((mode != "fp32" && mode != "naive" && mode != "tiled" && mode != "tensor")
            || n <= 0 || n > 16384 || repeats < 1 || (mode == "tiled" && n % 64 != 0)) {
        fprintf(stderr, "Use a supported mode, a size in 1..16384 (multiple of 64 for tiled), and positive repeats.\n");
        return EXIT_FAILURE;
    }

    size_t count = size_t(n)*n;
    std::vector<float> a(count), b(count);
    std::mt19937 random(0);
    std::uniform_real_distribution<float> input(-0.05f, 0.05f);
    for (float &value : a) value = input(random);
    for (float &value : b) value = input(random);

    float *da = nullptr, *db = nullptr, *dc = nullptr;
    __half *ha = nullptr, *hb = nullptr, *hc = nullptr;
    if (mode == "tensor") {
        std::vector<__half> converted(count);
        for (size_t i = 0; i < count; ++i) {
            converted[i] = __float2half(a[i]);
            a[i] = __half2float(converted[i]);
        }
        ha = device_copy(converted);
        for (size_t i = 0; i < count; ++i) {
            converted[i] = __float2half(b[i]);
            b[i] = __half2float(converted[i]);
        }
        hb = device_copy(converted);
        CUDA(cudaMalloc(&hc, count*sizeof(__half)));
    } else {
        if (mode == "naive") {
            std::vector<float> at(count);
            for (int k = 0; k < n; ++k)
                for (int i = 0; i < n; ++i)
                    at[k+i*n] = a[i+k*n];
            da = device_copy(at);
        } else {
            da = device_copy(a);
        }
        db = device_copy(b);
        CUDA(cudaMalloc(&dc, count*sizeof(float)));
    }

    cublasHandle_t blas = nullptr;
    if (mode == "fp32" || mode == "tensor") BLAS(cublasCreate(&blas));
    if (mode == "fp32") BLAS(cublasSetMathMode(blas, CUBLAS_PEDANTIC_MATH));
    if (mode == "tensor")
        BLAS(cublasSetMathMode(blas, CUBLAS_MATH_DISALLOW_REDUCED_PRECISION_REDUCTION));
    const float alpha = 1.0f, beta = 0.0f;
    auto launch = [&]() {
        if (mode == "fp32") {
            BLAS(cublasSgemm(blas, CUBLAS_OP_N, CUBLAS_OP_N, n, n, n,
                             &alpha, da, n, db, n, &beta, dc, n));
        } else if (mode == "tensor") {
            BLAS(cublasGemmEx(blas, CUBLAS_OP_N, CUBLAS_OP_N, n, n, n,
                    &alpha, ha, CUDA_R_16F, n, hb, CUDA_R_16F, n,
                    &beta, hc, CUDA_R_16F, n, CUBLAS_COMPUTE_32F, CUBLAS_GEMM_DEFAULT));
        } else if (mode == "naive") {
            naive<<<(count+255)/256, 256>>>(da, db, dc, n);
        } else {
            custom_sgemm<<<dim3(n/BlockDimM, n/BlockDimN),
                           dim3(BlockDimM/ThreadDimM, BlockDimN/ThreadDimN)>>>(da, db, dc, n, n);
        }
        CUDA(cudaGetLastError());
    };

    cudaEvent_t start, stop;
    CUDA(cudaEventCreate(&start));
    CUDA(cudaEventCreate(&stop));
    launch();
    CUDA(cudaDeviceSynchronize());
    for (int r = 0; r < repeats; ++r) {
        CUDA(cudaEventRecord(start));
        launch();
        CUDA(cudaEventRecord(stop));
        CUDA(cudaEventSynchronize(stop));
        float ms;
        CUDA(cudaEventElapsedTime(&ms, start, stop));
        printf("%.9f\n", ms/1000.0);
    }
    if (mode == "tensor") {
        validate(hc, a, b, n, true);
        CUDA(cudaFree(ha));
        CUDA(cudaFree(hb));
        CUDA(cudaFree(hc));
    } else {
        validate(dc, a, b, n, false);
        CUDA(cudaFree(da));
        CUDA(cudaFree(db));
        CUDA(cudaFree(dc));
    }
    CUDA(cudaEventDestroy(start));
    CUDA(cudaEventDestroy(stop));
    if (blas) BLAS(cublasDestroy(blas));
    return EXIT_SUCCESS;
}
