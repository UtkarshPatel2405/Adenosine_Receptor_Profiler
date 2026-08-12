import os
import uvicorn

# Satisfy Hugging Face ZeroGPU startup validation
try:
    import spaces
    @spaces.GPU
    def dummy_gpu_func():
        return "ZeroGPU check passed"
    dummy_gpu_func()
except ImportError:
    pass

if __name__ == "__main__":
    # Hugging Face Spaces dynamically sets the PORT environment variable (usually 7860)
    port = int(os.environ.get("PORT", 7860))
    
    # Import the FastAPI app from src.api
    from src.api import app
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=port)
