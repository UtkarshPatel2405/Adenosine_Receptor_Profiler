import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api_routes.single import router as single_router
from src.api_routes.batch import router as batch_router
from src.api_routes.model_results import router as model_results_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("src.api")

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


@app.get("/")
def read_root():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Adenosine Selectivity Model API active. Access /docs for API documentation."}
