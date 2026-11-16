import json
import numpy as np, pandas as pd
from fastapi.testclient import TestClient
from api.app import app
from src.common import *
from src.train import split, fit_model, forecast
from src.predict import predict, load


def test_source_integrity():
    verify_sources()


def test_temporal_purge_and_groups():
    f = pd.read_csv(PROCESSED / "training_wide.csv")
    for q in CONFIG["validation_origins"] + [
        CONFIG["test_origin"],
        CONFIG["reference_origin"],
    ]:
        tr, te = split(f, q, 12)
        assert tr.label_available_ord.max() < pd.Period(q).ordinal
        assert not set(tr.origin) & set(te.origin)


def test_data_contract():
    f = pd.read_csv(PROCESSED / "supervised_long.csv")
    assert len(f) >= 5000
    assert len(FEATURES) >= 8
    assert not f.duplicated(["origin", "series_id", "horizon"]).any()
    assert f.target_price_pln_m2.gt(0).all()
    assert not set(TARGETS) & set(FEATURES)


def test_all_forecasts_match_export():
    table = pd.read_csv(TABLES / "current_forecasts.csv")
    for (a, m), g in table.groupby(["area", "market"]):
        assert np.allclose(
            [x["prediction_pln_m2"] for x in predict(a, m)["forecasts"]],
            g.sort_values("horizon").prediction_pln_m2,
            atol=0.0051,
            rtol=0,
        )


def test_serialization_and_finite():
    bundle, f = load()
    v = forecast(bundle["estimator"], f)
    assert v.shape == (34, 5)
    assert np.isfinite(v).all()
    assert (v > 0).all()


def test_api_contract():
    client = TestClient(app)
    r = client.post("/predict", json={"area": "Warszawa", "market": "secondary"})
    assert r.status_code == 200
    assert len(r.json()["forecasts"]) == 5
    for body in [
        {"area": "Atlantyda", "market": "secondary"},
        {"area": "Warszawa", "market": "bad"},
        {"area": "Warszawa", "market": "secondary", "quarter": "2030Q1"},
        {"area": 4, "market": "primary"},
    ]:
        assert client.post("/predict", json=body).status_code == 422


def test_no_test_selection():
    selection = json.loads((ROOT / "models/selection.json").read_text())
    assert selection["selection_before_test"]
    trials = pd.read_csv(TABLES / "tuning_all_trials.csv")
    assert not trials.origin.eq(CONFIG["test_origin"]).any()
    assert (trials.max_train_label < trials.decision_ord).all()


def test_original_model_reproduction():
    r = json.loads((TABLES / "legacy_reproduction.json").read_text())
    assert r["max_price_difference_pln_m2"] < 1e-7
    assert abs(r["historical_h4_MAPE_pct"] - 5.6006585633) < 1e-7


def test_dashboard_catalog_and_assets():
    client = TestClient(app)
    page = client.get("/")
    assert page.status_code == 200
    assert 'id="forecast-table"' in page.text
    for asset in ["/static/style.css", "/static/dashboard.js"]:
        assert client.get(asset).status_code == 200
    catalog = client.get("/catalog").json()
    assert len(catalog["areas"]) == 17
    assert "Warszawa" in catalog["areas"]
    result = client.post(
        "/predict", json={"area": "Warszawa", "market": "secondary"}
    ).json()
    assert catalog["reference_origin"] == result["reference_origin"]
    assert catalog["evaluation"]["model_mape"] > 0
    assert client.get("/docs").status_code == 200
