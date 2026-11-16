from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field
from src.predict import predict, load
from src.common import ROOT, TABLES, CONFIG

app = FastAPI(
    title="Prognoza średnich cen mieszkań",
    version="1.0.0",
    description="Stały snapshot badawczy2026Q3; nie prognoza aktualizowana na żywo.",
)
STATIC = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    return (STATIC / "index.html").read_text(encoding="utf-8")


@app.get("/catalog")
def catalog():
    bundle, data = load()
    selection = json.loads((ROOT / "models/selection.json").read_text(encoding="utf-8"))
    scores = pd.read_csv(TABLES / "scores.csv")
    test = scores[scores.phase.eq("locked_test") & scores.horizon.eq(4)]
    return {
        "areas": sorted(data.area_clean.unique().tolist()),
        "reference_origin": bundle["reference_origin"],
        "generated": "2026-11-15",
        "evaluation": {
            "origin": CONFIG["test_origin"],
            "target": str(pd.Period(CONFIG["test_origin"]) + 4),
            "model_mape": float(test.loc[test.model.eq(selection["winner"]), "MAPE_pct"].iloc[0]),
            "baseline_mape": float(test.loc[test.model.eq("no_change"), "MAPE_pct"].iloc[0]),
        },
    }


class Request(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    area: str = Field(min_length=2, max_length=50)
    market: Literal["primary", "secondary"]


@app.get("/health")
def health():
    return {"status": "ok", "snapshot": "2026Q3"}


@app.post("/predict")
def prediction(body: Request):
    try:
        return predict(body.area, body.market)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
