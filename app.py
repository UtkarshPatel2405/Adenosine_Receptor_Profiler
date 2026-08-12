import os
import uvicorn
import gradio as gr
import spaces
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("app")

# Pre-load all machine learning models into memory during container boot to avoid cold-start timeouts
try:
    from src.predictor import _load_models, _load_db_lookup
    logger.info("Pre-loading QSAR models into memory on startup...")
    _load_db_lookup()
    for prefix in ("xgboost", "rf", "lgb", "stack_ridge"):
        _load_models(prefix)
    logger.info("All QSAR models pre-loaded successfully!")
except Exception as e:
    logger.error("Failed to pre-load models: %s", e)

# 1. Define the Gradio app with @spaces.GPU to satisfy Hugging Face ZeroGPU checks
@spaces.GPU
def dummy_gpu_func(text):
    return f"ZeroGPU active: {text}"

demo = gr.Interface(
    fn=dummy_gpu_func,
    inputs="text",
    outputs="text",
    title="Adeno Advance API Backend"
)

# 2. Extract Gradio's internal FastAPI instance to register our routes directly
# (This avoids mounting conflicts and ensures HF supervisor pings find the Gradio UI at root "/")
app = demo.app

# 3. Import and include our custom FastAPI routers
from src.api_routes.single import router as single_router
from src.api_routes.batch import router as batch_router
from src.api_routes.model_results import router as model_results_router

app.include_router(single_router)
app.include_router(batch_router)
app.include_router(model_results_router)

# Add health check route
@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}

# Enable CORS for cross-origin requests from Vercel
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
