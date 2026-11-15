from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch

# Skip only where no NVIDIA driver is visible (CI runners); on a GPU host a CPU-only torch must fail.
# WSL keeps nvidia-smi off a scrubbed PATH; /dev/dxg alone would also match AMD/Intel GPUs.
NVIDIA_SMI_PATHS = (Path("/usr/lib/wsl/lib/nvidia-smi"), Path("/dev/nvidia0"))
NO_NVIDIA_DRIVER = shutil.which("nvidia-smi") is None and not any(p.exists() for p in NVIDIA_SMI_PATHS)


@pytest.mark.skipif(NO_NVIDIA_DRIVER, reason="no NVIDIA driver (nvidia-smi) on this host")
def test_cuda_available():
    assert torch.cuda.is_available(), f"torch {torch.__version__} from {torch.__file__} cannot see the GPU"
