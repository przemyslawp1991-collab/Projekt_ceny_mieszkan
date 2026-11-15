"""Serve a fixed research snapshot, without pretending it is a live forecast."""

from functools import lru_cache
import joblib, pandas as pd, numpy as np
from .common import ROOT, PROCESSED


@lru_cache(maxsize=1)
def load():
    return joblib.load(ROOT / "models/model.pkl"), pd.read_csv(
        PROCESSED / "current_input.csv"
    )


def predict(area, market):
    bundle, f = load()
    row = f[f.area_clean.eq(area) & f.market.eq(market)]
    if len(row) != 1:
        raise ValueError("Nieobsługiwane miasto lub rynek")
    v = row.known_price.iloc[0] * np.exp(bundle["estimator"].predict(row)[0])
    q = bundle["reference_origin"]
    return dict(
        area=area,
        market=market,
        reference_origin=q,
        generated="2026-11-15",
        known_price_quarter=row.known_price_quarter.iloc[0],
        known_price_pln_m2=float(row.known_price.iloc[0]),
        unit="PLN/m2",
        scope="Średnia cena transakcyjna w mieście; archiwalny scenariusz badawczy",
        forecasts=[
            dict(
                horizon=h,
                target_quarter=str(pd.Period(q) + h),
                prediction_pln_m2=round(float(v[h]), 2),
            )
            for h in range(5)
        ],
        warning="h0 to nowcast. Brak skalibrowanych przedziałów. To nie wycena mieszkania ani sygnał inwestycyjny.",
    )


if __name__ == "__main__":
    import argparse, json

    p = argparse.ArgumentParser()
    p.add_argument("--area", default="Warszawa")
    p.add_argument("--market", choices=["primary", "secondary"], default="secondary")
    a = p.parse_args()
    print(json.dumps(predict(a.area, a.market), ensure_ascii=False, indent=2))
