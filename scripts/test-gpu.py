#!/usr/bin/env python3
"""
Test GPU functionality in VulcanLab container.

Usage:
    docker exec vulcanlab /opt/venv/bin/python /app/scripts/test-gpu.py
"""

import sys
import time


def test_pytorch_cuda():
    """Test PyTorch CUDA availability."""
    print("=" * 60)
    print("Testing PyTorch CUDA Support")
    print("=" * 60)

    try:
        import torch

        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"Device count: {torch.cuda.device_count()}")

            for i in range(torch.cuda.device_count()):
                print(f"\nGPU {i}:")
                print(f"  Name: {torch.cuda.get_device_name(i)}")
                props = torch.cuda.get_device_properties(i)
                print(f"  Compute capability: {props.major}.{props.minor}")
                print(f"  Total memory: {props.total_memory / 1024**3:.2f} GB")
                print(f"  Multiprocessors: {props.multi_processor_count}")

            print("\n✅ GPU support is working!")
            return True
        else:
            print("\n⚠️  CUDA not available - running on CPU")
            print("   This is normal if:")
            print("   - No GPU in system")
            print("   - Container not started with --gpus flag")
            print("   - NVIDIA drivers not installed")
            return False

    except ImportError as e:
        print(f"\n❌ Failed to import PyTorch: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error testing PyTorch: {e}")
        return False


def test_reranker_model():
    """Test loading and running the reranker model."""
    print("\n" + "=" * 60)
    print("Testing Reranker Model")
    print("=" * 60)

    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification

        model_name = "BAAI/bge-reranker-large"
        device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"Loading model on device: {device}")
        start = time.time()

        tokenizer = AutoTokenizer.from_pretrained(model_name)

        if device == "cuda":
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                torch_dtype=torch.float16
            ).to(device)
        else:
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name
            ).to(device)

        load_time = time.time() - start
        print(f"Model loaded in {load_time:.2f} seconds")

        # Test inference
        print("\nRunning test inference (100 pairs)...")
        pairs = [("test query", "test document")] * 100

        # Warmup
        inputs = tokenizer(
            pairs[:10],
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512
        ).to(device)

        with torch.no_grad():
            _ = model(**inputs)

        # Benchmark
        inputs = tokenizer(
            pairs,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512
        ).to(device)

        start = time.time()
        with torch.no_grad():
            outputs = model(**inputs)
        inference_time = time.time() - start

        throughput = len(pairs) / inference_time
        print(f"Processed {len(pairs)} pairs in {inference_time:.3f} seconds")
        print(f"Throughput: {throughput:.0f} pairs/second")

        # Performance assessment
        if device == "cuda":
            if throughput > 1000:
                print("✅ Excellent GPU performance!")
            elif throughput > 500:
                print("✅ Good GPU performance")
            else:
                print("⚠️  Lower than expected GPU performance")
                print("   Consider checking GPU utilization with nvidia-smi")
        else:
            if throughput > 100:
                print("✅ Good CPU performance")
            else:
                print("⚠️  Lower than expected CPU performance")

        return True

    except ImportError as e:
        print(f"\n❌ Failed to import required libraries: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error testing reranker: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_opencv():
    """Test OpenCV/OpenGL libraries."""
    print("\n" + "=" * 60)
    print("Testing OpenCV")
    print("=" * 60)

    try:
        import cv2
        print(f"OpenCV version: {cv2.__version__}")

        # Try to import docling which uses OpenCV
        try:
            from docling.document_converter import DocumentConverter
            print("✅ Docling imports successfully")
            print("   OpenGL libraries are working")
            return True
        except Exception as e:
            print(f"⚠️  Docling import issue: {e}")
            print("   Document conversion may not work")
            return False

    except ImportError as e:
        print(f"❌ Failed to import OpenCV: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("VulcanLab GPU Test Suite")
    print("=" * 60 + "\n")

    results = {}

    # Test 1: PyTorch CUDA
    results['pytorch_cuda'] = test_pytorch_cuda()

    # Test 2: Reranker model
    results['reranker'] = test_reranker_model()

    # Test 3: OpenCV
    results['opencv'] = test_opencv()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed - check output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
