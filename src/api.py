import logging
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mock spaces module locally to allow literal @spaces.GPU decorators in routes
try:
    import spaces
except ImportError:
    import types
    mock_spaces = types.ModuleType("spaces")
    def dummy_gpu(func):
        return func
    mock_spaces.GPU = dummy_gpu
    sys.modules["spaces"] = mock_spaces

from src.api_routes.single import router as single_router
from src.api_routes.batch import router as batch_router
from src.api_routes.model_results import router as model_results_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("src.api")

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

app = FastAPI(
    title="Adenosine Receptor Selectivity Predictor API",
    description="Publication-grade QSAR platform with MAPIE conformal prediction & multi-model ensembles",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(single_router)
app.include_router(batch_router)
app.include_router(model_results_router)

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}



