import os
import uvicorn
import gradio as gr
from src.api import app as fastapi_app

# 1. Define a dummy GPU function to satisfy Hugging Face ZeroGPU startup check
try:
    import spaces
    @spaces.GPU
    def dummy_gpu_func(text):
        return f"ZeroGPU active: {text}"
except ImportError:
    # Fallback for local runs where spaces isn't installed
    def dummy_gpu_func(text):
        return f"Local run: {text}"

# 2. Create a basic Gradio interface that uses the GPU function
demo = gr.Interface(
    fn=dummy_gpu_func,
    inputs="text",
    outputs="text",
    title="Adeno Advance API Backend"
)

# 3. Mount Gradio onto the FastAPI application at "/gradio"
# This keeps your FastAPI endpoints at the root "/" and mounts the Gradio interface at "/gradio"
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
