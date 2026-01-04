
## GPU Support

- The ONNX model will use GPU automatically if your ONNX Runtime has the CUDA Execution Provider installed.
- To enable GPU inference, install `onnxruntime-gpu` or ONNX Runtime with CUDA support.
- Optionally install `nvidia-ml-py3` (`pynvml`) to provide more accurate GPU memory stats.
- Use `scripts/check_onnx_device.py` to confirm available providers.
