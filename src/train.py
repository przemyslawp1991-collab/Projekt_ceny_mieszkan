"""Tune exclusively on purged chronological development origins, then freeze selection."""

import time, os

os.environ.setdefault("OMP_NUM_THREADS", "2")
import pandas as pd, numpy as np, joblib
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits
from .common import *


def build(spec):
    if spec["algorithm"] == "rf":
        est = RandomForestRegressor(
            n_estimators=spec["trees"],
            max_depth=spec["depth"],
            min_samples_leaf=spec["leaf"],
            random_state=CONFIG["seed"],
            n_jobs=CONFIG["threads"],
        )
    elif spec["algorithm"] == "ridge":
        est = Ridge(alpha=spec["alpha"])
    else:
        est = MultiOutputRegressor(
            HistGradientBoostingRegressor(
                max_iter=spec["iterations"],
                max_leaf_nodes=spec["leaves"],
                min_samples_leaf=20,
                l2_regularization=spec["l2"],
                learning_rate=0.04,
                early_stopping=False,
                random_state=CONFIG["seed"],
            ),
            n_jobs=1,
        )
    pre = ColumnTransformer(
        [
            (
                "num",
                make_pipeline(
                    SimpleImputer(
                        strategy="median", add_indicator=True, keep_empty_features=True
                    ),
                    StandardScaler(),
                ),
                FEATURES,
            ),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ["area", "market"],
            ),
        ]
    )
    return Pipeline([("pre", pre), ("est", est)])


def split(f, q, window):
    oo = pd.Period(q).ordinal
    pool = f[f.label_available_ord < oo]
    latest = pool.origin_ord.max()
    tr = pool[pool.origin_ord >= latest - window + 1]
    te = f[f.origin.eq(q)]
    assert len(tr) > 0 and tr.label_available_ord.max() < oo
    return tr, te


def fit_model(tr, spec):
    m = build(spec)
    y = np.log(tr[TARGETS].to_numpy() / tr.known_price.to_numpy()[:, None])
    w = tr.series_id.map(1 / tr.series_id.value_counts())
    m.fit(tr, y, est__sample_weight=w / w.mean())
    return m


def forecast(m, te):
    return te.known_price.to_numpy()[:, None] * np.exp(m.predict(te))


def baselines(tr, te):
    logs = np.log(tr[TARGETS].to_numpy() / tr.known_price.to_numpy()[:, None])
    tmp = pd.DataFrame(logs, columns=range(5))
    tmp["series_id"] = tr.series_id.to_numpy()
    means = tmp.groupby("series_id").mean()
    return {
        "historical_mean": te.known_price.to_numpy()[:, None]
        * np.exp(means.reindex(te.series_id).to_numpy()),
        "no_change": np.repeat(te.known_price.to_numpy()[:, None], 5, axis=1),
        "momentum": te.known_price.to_numpy()[:, None]
        * (1 + te.local_yoy_known2.to_numpy()[:, None] / 100)
        ** ((np.arange(5)[None, :] + te.price_lag.to_numpy()[:, None]) / 4),
    }


def records(te, values, name, phase):
    rows = []
    for i, r in enumerate(te.itertuples()):
        for h in range(5):
            rows.append(
                dict(
                    phase=phase,
                    model=name,
                    origin=r.origin,
                    series_id=r.series_id,
                    area=r.area_clean,
                    market=r.market,
                    horizon=h,
                    actual=getattr(r, f"price_h{h}"),
                    prediction=float(values[i, h]),
                    known_price=r.known_price,
                )
            )
    return rows


def main():
    f = pd.read_csv(PROCESSED / "training_wide.csv")
    rows = []
    pred = []
    protocol = dict(
        config=CONFIG,
        feature_hash=digest(PROCESSED / "training_wide.csv"),
        independent_unseen_test=False,
        disclosure="Historical data and previous price models had already been inspected. Test2025Q2 is locked for this package, not a pristine prospective holdout.",
        selection="minimum mean h4 MAPE across six development origins, tie ID; no test selection",
        label_rule="origin+6 strictly before decision; latest matured origins window",
        test_cases=34,
        test_path_points=170,
    )
    save_json(ROOT / "models/protocol.json", protocol)
    with threadpool_limits(limits=CONFIG["threads"]):
        for spec in CONFIG["trials"]:
            for q in CONFIG["validation_origins"]:
                tr, te = split(f, q, spec["window"])
                assert len(te) == 34
                start = time.perf_counter()
                m = fit_model(tr, spec)
                v = forecast(m, te)
                sec = time.perf_counter() - start
                ape = np.abs(v / te[TARGETS].to_numpy() - 1) * 100
                rows.append(
                    dict(
                        trial=spec["id"],
                        algorithm=spec["algorithm"],
                        origin=q,
                        window=spec["window"],
                        n_train=len(tr),
                        max_train_label=int(tr.label_available_ord.max()),
                        decision_ord=pd.Period(q).ordinal,
                        MAPE_h4=ape[:, 4].mean(),
                        MAPE_all=ape.mean(),
                        seconds=sec,
                    )
                )
                pred += records(te, v, spec["id"], "validation")
            print("Tuned", spec["id"], flush=True)
    trials = pd.DataFrame(rows)
    trials.to_csv(TABLES / "tuning_all_trials.csv", index=False)
    pd.DataFrame(pred).to_csv(TABLES / "validation_predictions.csv", index=False)
    scores = (
        trials.groupby("trial")
        .agg(
            MAPE_h4=("MAPE_h4", "mean"),
            MAPE_all=("MAPE_all", "mean"),
            seconds=("seconds", "sum"),
        )
        .sort_values(["MAPE_h4", "trial"])
    )
    scores.to_csv(TABLES / "tuning_summary.csv")
    winner = scores.index[0]
    spec = next(s for s in CONFIG["trials"] if s["id"] == winner)
    save_json(
        ROOT / "models/selection.json",
        dict(
            winner=winner,
            spec=spec,
            selection_before_test=True,
            feature_hash=protocol["feature_hash"],
            validation_score=float(scores.loc[winner, "MAPE_h4"]),
        ),
    )
    print("Validation winner:", winner, flush=True)


if __name__ == "__main__":
    main()
