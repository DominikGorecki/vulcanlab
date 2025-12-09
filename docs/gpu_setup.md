# GPU Support for VulcanLab Docker Container

This guide explains how to enable GPU acceleration in VulcanLab for faster ML operations (reranking, embeddings, document processing).

## Prerequisites

### 1. NVIDIA GPU and Driver

You need:
- An NVIDIA GPU (GeForce, Quadro, Tesla, etc.)
- NVIDIA GPU drivers installed on your host machine (version 525.60.13 or newer recommended)

Check your driver version:
```bash
nvidia-smi
```

### 2. NVIDIA Container Toolkit

The NVIDIA Container Toolkit allows Docker containers to access your GPU.

#### Install on Ubuntu/Debian:
```bash
# Add NVIDIA package repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install NVIDIA Container Toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Restart Docker
sudo systemctl restart docker
```

#### Install on other systems:
See [NVIDIA Container Toolkit Installation Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

### 3. Verify Installation

Test that Docker can access your GPU:
```bash
docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu22.04 nvidia-smi
```

You should see your GPU listed.

## Building the GPU-Enabled Image

### Option 1: Use the GPU Dockerfile

Build the GPU-enabled image:
```bash
docker build -f docker/Dockerfile.allinone.gpu -t vulcanlab:gpu .
```

This creates an image with CUDA 12.6 support.

### Option 2: Modify Existing Dockerfile

If you want to use a different CUDA version or customize the build, edit `docker/Dockerfile.allinone.gpu` and adjust the CUDA package versions.

## Running with GPU Support

### Using docker run

Add the `--gpus` flag:
```bash
docker run -d \
  --name vulcanlab \
  --gpus all \
  -p 3000:3000 \
  -v $(pwd)/data:/app/data \
  --env-file .env.docker \
  vulcanlab:gpu
```

Or to use specific GPUs:
```bash
# Use GPU 0 only
docker run -d --gpus '"device=0"' ...

# Use GPUs 0 and 1
docker run -d --gpus '"device=0,1"' ...
```

### Using docker-compose

Add GPU configuration to `docker-compose.yml`:

```yaml
services:
  vulcanlab:
    image: vulcanlab:gpu
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all  # or specific count: 1
              capabilities: [gpu]
```

Or for older docker-compose versions:
```yaml
services:
  vulcanlab:
    image: vulcanlab:gpu
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
```

## Verifying GPU Usage

### 1. Run the GPU Test Suite (Recommended)

We provide a comprehensive test script that checks all GPU functionality:

```bash
docker exec vulcanlab /opt/venv/bin/python /app/scripts/test-gpu.py
```

This will test:
- PyTorch CUDA availability
- GPU device information
- Reranker model loading and performance
- OpenCV/OpenGL libraries
- Performance benchmarks

Expected output with GPU:
```
============================================================
VulcanLab GPU Test Suite
============================================================

============================================================
Testing PyTorch CUDA Support
============================================================
PyTorch version: 2.x.x
CUDA available: True
CUDA version: 12.6
Device count: 1

GPU 0:
  Name: NVIDIA GeForce RTX 3060
  Compute capability: 8.6
  Total memory: 12.00 GB
  Multiprocessors: 28

✅ GPU support is working!

============================================================
Testing Reranker Model
============================================================
Loading model on device: cuda
Model loaded in 2.34 seconds

Running test inference (100 pairs)...
Processed 100 pairs in 0.089 seconds
Throughput: 1124 pairs/second
✅ Excellent GPU performance!

============================================================
Testing OpenCV
============================================================
OpenCV version: 4.x.x
✅ Docling imports successfully
   OpenGL libraries are working

============================================================
Test Summary
============================================================
pytorch_cuda         ✅ PASS
reranker             ✅ PASS
opencv               ✅ PASS

🎉 All tests passed!
```

### 2. Check GPU is Detected

After starting the container, check the logs:
```bash
docker logs vulcanlab 2>&1 | grep -i cuda
```

### 3. Monitor GPU Usage

While running a conversion or query, monitor GPU utilization:
```bash
# On host machine
watch nvidia-smi

# Inside container
docker exec vulcanlab nvidia-smi
```

### 4. Manual PyTorch Test

Enter the container and test PyTorch:
```bash
docker exec -it vulcanlab /opt/venv/bin/python
```

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA device count: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"Current device: {torch.cuda.current_device()}")
    print(f"Device name: {torch.cuda.get_device_name(0)}")
```

## Performance Expectations

With GPU acceleration enabled:

- **Reranking**: ~5-10x faster for large result sets (100+ chunks)
- **Document Processing**: ~2-3x faster for PDF/image processing
- **Embeddings**: ~3-5x faster for batch operations

Actual speedup depends on:
- GPU model (newer = faster)
- Batch size (larger batches utilize GPU better)
- CPU bottlenecks (data transfer, preprocessing)

## Troubleshooting

### "nvidia-smi not found" in container

This is expected if CUDA runtime libraries are installed but not the full toolkit. The GPU will still work for PyTorch operations.

### PyTorch not detecting GPU

1. Check NVIDIA drivers on host: `nvidia-smi`
2. Verify container has GPU access: `docker exec vulcanlab nvidia-smi`
3. Check PyTorch CUDA compatibility:
```bash
docker exec vulcanlab /opt/venv/bin/python -c "import torch; print(torch.version.cuda)"
```

### Out of memory errors

Reduce batch size or use a GPU with more memory. You can also limit GPU memory allocation:

```python
# In your code
import torch
torch.cuda.set_per_process_memory_fraction(0.8)  # Use max 80% of GPU memory
```

### Performance not improving

1. Check if GPU is actually being used: `nvidia-smi` during operations
2. Ensure you're processing enough data to benefit from GPU (small batches may not see speedup)
3. Check for CPU bottlenecks (preprocessing, I/O)

## CPU-Only Fallback

The application automatically falls back to CPU if:
- No GPU is detected
- CUDA is not available
- GPU memory is exhausted

This is handled in [retrieve.py:318](../src/vulcanlab/retrieval/retrieve.py#L318):
```python
device = "cuda" if torch.cuda.is_available() else "cpu"
```

## Resource Management

### Limit GPU Memory

Add to your environment variables:
```bash
# In .env.docker
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### Share GPU with Other Containers

Use GPU fractions:
```bash
docker run --gpus '"device=0"' ...  # First container
docker run --gpus '"device=0"' ...  # Second container (shares GPU 0)
```

Monitor with `nvidia-smi` to avoid overloading.

## Advanced: Multi-GPU Support

For multiple GPUs, PyTorch will use GPU 0 by default. To use specific GPUs:

```bash
# Use GPU 1
docker run -e CUDA_VISIBLE_DEVICES=1 --gpus all ...

# Use GPUs 0 and 2
docker run -e CUDA_VISIBLE_DEVICES=0,2 --gpus all ...
```

Or modify the code to use specific devices:
```python
device = torch.device("cuda:1")  # Use GPU 1
```

## References

- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker)
- [Docker GPU Support](https://docs.docker.com/config/containers/resource_constraints/#gpu)
- [PyTorch CUDA Semantics](https://pytorch.org/docs/stable/notes/cuda.html)
