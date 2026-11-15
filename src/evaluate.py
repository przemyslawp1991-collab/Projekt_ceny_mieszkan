"""Frozen selection, historical reproduction, paired uncertainty, final test and export."""

import time, json
import pandas as pd, numpy as np, joblib
from sklearn.inspection import permutation_importance
from threadpoolctl import threadpool_limits
from .common import *
from .train import split, fit_model, forecast, baselines, records


def metrics(z):
    x = z.assign(
        APE_pct=np.abs(z.prediction / z.actual - 1) * 100,
        AE_pln_m2=np.abs(z.prediction - z.actual),
        SE=(z.prediction - z.actual) ** 2,
    )
    return (
        x.groupby(["phase", "model", "horizon"])
        .agg(
            n=("APE_pct", "size"),
            MAPE_pct=("APE_pct", "mean"),
            MAE_pln_m2=("AE_pln_m2", "mean"),
            MSE=("SE", "mean"),
        )
        .reset_index()
        .assign(RMSE_pln_m2=lambda t: np.sqrt(t.MSE))
        .drop(columns="MSE")
    )


def main():
    selection = json.loads((ROOT / "models/selection.json").read_text(encoding="utf-8"))
    spec = selection["spec"]
    f = pd.read_csv(PROCESSED / "training_wide.csv")
    assert selection["feature_hash"] == digest(PROCESSED / "training_wide.csv")
    rows = []
    audit = []
    timing = []
    legacy_rows = []
    with threadpool_limits(limits=CONFIG["threads"]):
        for q in pd.period_range(*CONFIG["historical_origins"], freq="Q").astype(str):
            tr, te = split(f, q, spec["window"])
            start = time.perf_counter()
            m = fit_model(tr, spec)
            v = forecast(m, te)
            timing.append(time.perf_counter() - start)
            rows += records(te, v, "selected_model", "historical_diagnostic")
            for name, b in baselines(tr, te).items():
                rows += records(te, b, name, "historical_diagnostic")
            audit.append(
                dict(
                    origin=q,
                    n_train=len(tr),
                    max_train_label=int(tr.label_available_ord.max()),
                    decision_ord=pd.Period(q).ordinal,
                )
            )
        legacy = pd.read_csv(ROOT / "data/reference/legacy_path_panel.csv")
        legacy_spec = CONFIG["trials"][0]
        for q in pd.period_range(*CONFIG["historical_origins"], freq="Q").astype(str):
            old_tr, old_te = split(legacy, q, 12)
            old_model = fit_model(old_tr, legacy_spec)
            legacy_rows += records(
                old_te,
                forecast(old_model, old_te),
                "isolated_original_rf",
                "legacy_reproduction",
            )
        pd.DataFrame(legacy_rows).to_csv(
            TABLES / "legacy_backtest_predictions.csv", index=False
        )
        legacy_scores = metrics(pd.DataFrame(legacy_rows))
        legacy_scores.to_csv(TABLES / "legacy_backtest_scores.csv", index=False)
        legacy_mape = float(
            legacy_scores.loc[legacy_scores.horizon.eq(4), "MAPE_pct"].iloc[0]
        )
        assert abs(legacy_mape - 5.6006585633) < 1e-7
        # One locked date. All algorithms are shown; selection remains unchanged.
        q = CONFIG["test_origin"]
        for candidate in CONFIG["trials"]:
            tr, te = split(f, q, candidate["window"])
            m = fit_model(tr, candidate)
            rows += records(te, forecast(m, te), candidate["id"], "locked_test")
        tr, te = split(f, q, spec["window"])
        test_model = fit_model(tr, spec)
        for name, b in baselines(tr, te).items():
            rows += records(te, b, name, "locked_test")
        # Permutation analysis on the final development fold, never on the locked test.
        tr_dev, dev = split(f, CONFIG["validation_origins"][-1], spec["window"])
        explainer = fit_model(tr_dev, spec)
        base = np.mean(np.abs(forecast(explainer, dev)[:, 4] / dev.price_h4 - 1)) * 100
        rng = np.random.default_rng(CONFIG["seed"])
        importance = []
        for col in FEATURES + ["area", "market"]:
            deltas = []
            for repeat in range(5):
                shuffled = dev.copy()
                shuffled[col] = rng.permutation(shuffled[col].to_numpy())
                deltas.append(
                    np.mean(
                        np.abs(forecast(explainer, shuffled)[:, 4] / dev.price_h4 - 1)
                    )
                    * 100
                    - base
                )
            importance.append(
                dict(feature=col, delta_MAPE_pp=np.mean(deltas), std=np.std(deltas))
            )
        pd.DataFrame(importance).sort_values("delta_MAPE_pp", ascending=False).to_csv(
            TABLES / "permutation_importance.csv", index=False
        )
        # Per-observation sensitivity is an explanation of model behavior, not causal SHAP.
        one = dev[dev.area_clean.eq("Warszawa") & dev.market.eq("secondary")].copy()
        local = []
        full = float(forecast(explainer, one)[0, 4])
        for col in FEATURES:
            changed = one.copy()
            changed[col] = tr_dev[col].median()
            local.append(
                dict(
                    feature=col,
                    prediction=full,
                    median_replaced_prediction=float(
                        forecast(explainer, changed)[0, 4]
                    ),
                )
            )
        pd.DataFrame(local).to_csv(TABLES / "local_sensitivity.csv", index=False)
        # Export at the reference origin, using only matured complete paths.
        q = CONFIG["reference_origin"]
        tr, _ = split(f, q, spec["window"])
        current = pd.read_csv(PROCESSED / "features_wide.csv")
        current = current[current.origin.eq(q)].copy()
        assert len(current) == 34
        start = time.perf_counter()
        production = fit_model(tr, spec)
        train_seconds = time.perf_counter() - start
        bundle = dict(
            estimator=production, features=FEATURES, reference_origin=q, spec=spec
        )
        joblib.dump(bundle, ROOT / "models/model.pkl")
        current.to_csv(PROCESSED / "current_input.csv", index=False)
        values = forecast(production, current)
        out = []
        for i, r in enumerate(current.itertuples()):
            for h in range(5):
                out.append(
                    dict(
                        area=r.area_clean,
                        market=r.market,
                        reference_origin=q,
                        horizon=h,
                        target_quarter=str(pd.Period(q) + h),
                        known_price=r.known_price,
                        known_price_quarter=r.known_price_quarter,
                        prediction_pln_m2=float(values[i, h]),
                    )
                )
        pd.DataFrame(out).to_csv(TABLES / "current_forecasts.csv", index=False)
    z = pd.DataFrame(rows)
    z.to_csv(TABLES / "predictions.csv", index=False)
    scores = metrics(z)
    scores.to_csv(TABLES / "scores.csv", index=False)
    pd.DataFrame(audit).to_csv(TABLES / "training_audit.csv", index=False)
    h = z[z.phase.eq("historical_diagnostic") & z.horizon.eq(4)].copy()
    h["APE"] = np.abs(h.prediction / h.actual - 1) * 100
    h.groupby(["model", "market"]).APE.agg(["size", "mean"]).to_csv(
        TABLES / "errors_market.csv"
    )
    h.groupby(["model", "area"]).APE.agg(["size", "mean"]).to_csv(
        TABLES / "errors_city.csv"
    )
    h.groupby(["model", "origin"]).APE.mean().to_csv(TABLES / "errors_origin.csv")
    wide = h.groupby(["origin", "model"]).APE.mean().unstack()
    delta = (wide.selected_model - wide.historical_mean).to_numpy()
    rng = np.random.default_rng(CONFIG["seed"])
    n = len(delta)
    idx = (
        rng.integers(n, size=(CONFIG["bootstrap_repetitions"], 7, 1)) + np.arange(6)
    ).reshape(CONFIG["bootstrap_repetitions"], -1)[:, :n] % n
    ci = np.quantile(delta[idx].mean(axis=1), [0.025, 0.975])
    save_json(
        TABLES / "paired_bootstrap.json",
        dict(
            delta_MAPE_pp=float(delta.mean()),
            CI95_low=float(ci[0]),
            CI95_high=float(ci[1]),
            block_length_quarters=6,
            resamples=CONFIG["bootstrap_repetitions"],
            interpretation="Retrospective diagnostic after prior inspection, not confirmatory evidence; overlapping paths and shared macro factors.",
        ),
    )
    # Verify the isolated original production estimator against its frozen input/forecast.
    old = joblib.load(ROOT / "models/isolated_original_rf.joblib")
    ref = pd.read_csv(ROOT / "data/reference/legacy_current_input.csv")
    v = forecast(old["estimator"], ref)
    r = pd.read_csv(ROOT / "data/reference/legacy_current_forecasts.csv")
    lookup = r.set_index(["series_id", "horizon"]).predicted_price_pln_m2
    expected = np.array([[lookup.loc[s, h] for h in range(5)] for s in ref.series_id])
    max_difference = float(np.max(np.abs(v - expected)))
    assert max_difference < 1e-7
    save_json(
        TABLES / "legacy_reproduction.json",
        dict(
            rows=len(ref),
            finite=bool(np.isfinite(v).all()),
            max_price_difference_pln_m2=max_difference,
            historical_h4_MAPE_pct=legacy_mape,
            prediction_matrix_sha256=__import__("hashlib")
            .sha256(v.tobytes())
            .hexdigest(),
            note="Original estimator retained independently and its historical41origins reproduced; the new model is rebuilt from original provider files and tuned separately.",
        ),
    )
    metadata = dict(
        model="multioutput log price path",
        selected_trial=spec,
        features=FEATURES,
        categoricals=["area", "market"],
        horizons=list(range(5)),
        reference_origin=CONFIG["reference_origin"],
        build_date="2026-11-15",
        reference_is_past=True,
        not_live_forecast=True,
        target="city-market mean transaction price PLN/m2, not individual property",
        known_price_quarters=sorted(current.known_price_quarter.unique().tolist()),
        training_max_label_ord=int(tr.label_available_ord.max()),
        training_rows=len(tr),
        training_seconds=train_seconds,
        model_bytes=(ROOT / "models/model.pkl").stat().st_size,
        threads=CONFIG["threads"],
        seed=CONFIG["seed"],
        source_manifest_sha256=digest(RAW / "source_manifest.json"),
        training_data_sha256=digest(PROCESSED / "training_wide.csv"),
        independent_unseen_test=False,
        intervals="No calibrated prediction interval claimed; point forecast only.",
        availability="Assumed quarterly lags; revised data, not historical vintages; reference2026Q3 generated November15. h0 is a nowcast of the reference quarter.",
        software={
            name: __import__("importlib.metadata").metadata.version(name)
            for name in ["pandas", "numpy", "scikit-learn", "joblib"]
        },
    )
    save_json(ROOT / "models/metadata.json", metadata)
    save_json(
        TABLES / "green_it.json",
        dict(
            production_train_seconds=train_seconds,
            mean_historical_fit_seconds=float(np.mean(timing)),
            model_bytes=metadata["model_bytes"],
            threads=CONFIG["threads"],
            gpu=False,
            carbon_emissions_measured=False,
        ),
    )
    print(scores[scores.horizon.eq(4)].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
