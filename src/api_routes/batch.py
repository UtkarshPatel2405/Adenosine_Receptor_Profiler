import io
import logging
import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from src.predictor import predict
from src.config import SUBTYPES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/predict", tags=["batch"])


@router.post("/batch")
async def predict_batch(file: UploadFile = File(...)):
    if not file.filename.endswith((".csv", ".txt")):
        raise HTTPException(status_code=400, detail="Only CSV or TXT files are supported")

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {e}")

    smiles_col = None
    for col in df.columns:
        if str(col).strip().lower() in ("smiles", "smiles_string", "structure", "compound"):
            smiles_col = col
            break
    if not smiles_col:
        smiles_col = df.columns[0]

    results = []
    export_rows = []

    for idx, row in df.iterrows():
        smi = str(row[smiles_col]).strip()
        if not smi or smi == "nan":
            continue
        try:
            res = predict(smi, threshold=6.0, run_rf=False)
            best_t = res.get("best_target", "A2A")
            xgb_preds = res.get("predictions", {}).get("XGBoost", {})
            best_val = xgb_preds.get(best_t, 0.0)

            record = {
                "id": idx + 1,
                "smiles": res["smiles"],
                "best_target": best_t,
                "best_value": round(best_val, 3),
                "in_db": res.get("in_database", False),
                "ad_status": "Inside AD" if res.get("in_database") else "Moderate AD",
            }
            for s in SUBTYPES:
                record[s] = round(xgb_preds.get(s, 0.0), 3)

            results.append(record)

            export_row = {"SMILES": res["smiles"], "Best_Target": best_t, "Max_pChEMBL": round(best_val, 3)}
            for s in SUBTYPES:
                export_row[f"pChEMBL_{s}"] = round(xgb_preds.get(s, 0.0), 3)
            export_rows.append(export_row)

        except Exception as e:
            logger.warning("Batch prediction failed for row %d (%s): %s", idx, smi, e)

    return {
        "status": "success",
        "total_processed": len(results),
        "results": results,
    }


@router.post("/batch/export")
async def export_batch_csv(file: UploadFile = File(...)):
    res_data = await predict_batch(file)
    results = res_data.get("results", [])
    df_export = pd.DataFrame(results)

    stream = io.StringIO()
    df_export.to_csv(stream, index=False)
    stream.seek(0)

    return StreamingResponse(
        io.BytesIO(stream.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=adenosine_predictions.csv"},
    )
