from __future__ import annotations

import shutil

import pytest
import torch

# Skip only where no NVIDIA driver is visible (CI runners); on a GPU host a CPU-only torch must fail.
NO_NVIDIA_DRIVER = shutil.which("nvidia-smi") is None


@pytest.mark.skipif(NO_NVIDIA_DRIVER, reason="no NVIDIA driver (nvidia-smi) on this host")
def test_cuda_available():
    assert torch.cuda.is_available(), f"torch {torch.__version__} from {torch.__file__} cannot see the GPU"
