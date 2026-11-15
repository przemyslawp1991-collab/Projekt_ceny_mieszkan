from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from src.predict import predict

app = FastAPI(
    title="Prognoza średnich cen mieszkań",
    version="1.0.0",
    description="Stały snapshot badawczy2026Q3; nie prognoza aktualizowana na żywo.",
)


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
