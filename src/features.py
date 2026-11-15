"""Origin-grouped features; targets are separate and never selected as inputs."""

import json
import pandas as pd, numpy as np
from .common import *


def main():
    raw = pd.read_csv(PROCESSED / "prices_long.csv")
    prices = raw[raw.series_type.eq("transaction") & ~raw.is_aggregate]
    look = prices.set_index(["series_id", "quarter"]).value.to_dict()
    cal = json.loads((RAW / "NBP_release_calendar.json").read_text(encoding="utf-8"))
    months = {
        "styczeń": 1,
        "marzec": 3,
        "czerwiec": 6,
        "wrzesień": 9,
        "październik": 10,
        "grudzień": 12,
    }
    ready = {
        r["reference_quarter"]: pd.Period(
            f"{r['publication_year']}-{months[r['publication_month_word'].lower()]:02d}",
            freq="M",
        ).asfreq("Q")
        for r in cal
        if r["publication_month_word"].lower() in months
    }
    rows = []
    for sid, g in prices.groupby("series_id"):
        for q in pd.period_range(g.quarter.min(), CONFIG["reference_origin"], freq="Q"):
            lag = 1 if str(q - 1) in ready and ready[str(q - 1)] <= q else 2

            def v(k):
                return look.get((sid, str(q - k)), np.nan)

            known = v(lag)
            if not np.isfinite(known) or not np.isfinite(v(lag + 4)):
                continue
            row = dict(
                origin=str(q),
                origin_ord=q.ordinal,
                series_id=sid,
                area=g.area.iloc[0],
                area_clean=g.area_clean.iloc[0],
                market=g.market.iloc[0],
                known_price=known,
                known_price_quarter=str(q - lag),
                price_lag=lag,
                label_available_ord=q.ordinal + 6,
                log_known_price=np.log(known),
                local_yoy_known2=(known / v(lag + 4) - 1) * 100,
                local_qoq_known2=(known / v(lag + 1) - 1) * 100,
                local_yoy_acceleration_known2=(
                    known / v(lag + 4) - v(lag + 4) / v(lag + 8)
                )
                * 100,
                local_volatility4_known2=pd.Series(
                    [(v(lag + j) / v(lag + j + 1) - 1) * 100 for j in range(4)]
                ).std(),
            )
            row.update(
                {f"price_h{h}": look.get((sid, str(q + h)), np.nan) for h in range(5)}
            )
            rows.append(row)
    f = pd.DataFrame(rows)
    f["relative_price_known2"] = f.known_price / f.groupby(
        ["market", "origin"]
    ).known_price.transform("median")
    ratio = f.pivot(index=["area", "origin"], columns="market", values="known_price")
    ratio = ratio.primary / ratio.secondary
    f["primary_secondary_ratio_known2"] = [
        ratio.get((a, q), np.nan) for a, q in zip(f.area, f.origin)
    ]
    g = f.groupby(["market", "origin"]).local_yoy_known2
    f["peer_yoy_known2"] = (g.transform("sum") - f.local_yoy_known2) / (
        g.transform("count") - 1
    )
    for source, dest in [
        ("local_qoq_known2", "market_decline_breadth_known"),
        ("local_yoy_known2", "market_negative_yoy_breadth_known"),
    ]:
        neg = f[source].lt(0).where(f[source].notna())
        f[dest] = neg.groupby([f.market, f.origin]).transform("mean")
    for typ, dest in [
        ("hedonic_qoq", "hedonic_qoq_known"),
        ("hedonic_yoy", "hedonic_yoy_known"),
    ]:
        h = (
            raw[raw.series_type.eq(typ) & raw.market.eq("secondary")]
            .set_index(["area_clean", "quarter"])
            .value.to_dict()
        )
        f[dest] = [
            h.get((a, q), np.nan) - 100 if m == "secondary" else np.nan
            for a, q, m in zip(f.area_clean, f.known_price_quarter, f.market)
        ]
    macro = pd.read_csv(PROCESSED / "macro.csv").set_index("quarter")
    names = [
        "policy_rate",
        "policy_change",
        "inflation",
        "wage_yoy",
        "mortgage_rate",
        "real_flow_yoy",
        "sloos_demand",
        "sloos_easing",
    ]
    prev = (pd.PeriodIndex(f.origin, freq="Q") - 1).astype(str)
    for col, src in zip(MACRO, names):
        f[col] = prev.map(macro[src])
    credit = (
        pd.read_csv(RAW / "AMRON_counts_audited.csv")
        .set_index("quarter")
        .mortgage_count
    )
    credit = credit.reindex(
        pd.period_range(
            credit.index.min(), CONFIG["reference_origin"], freq="Q"
        ).astype(str)
    )
    yoy = credit.pct_change(4, fill_method=None) * 100
    vals = [
        yoy,
        credit.pct_change(1, fill_method=None) * 100,
        yoy.diff(4),
        credit.rolling(4, min_periods=4).sum().pct_change(4, fill_method=None) * 100,
    ]
    prev2 = (pd.PeriodIndex(f.origin, freq="Q") - 2).astype(str)
    for col, v in zip(CREDIT, vals):
        f[col] = prev2.map(v)
    f = f.sort_values(["origin", "market", "area"]).reset_index(drop=True)
    assert not f.duplicated(["origin", "series_id"]).any()
    f.to_csv(PROCESSED / "features_wide.csv", index=False)
    labeled = f.dropna(subset=TARGETS)
    labeled.to_csv(PROCESSED / "training_wide.csv", index=False)
    long = labeled.melt(
        id_vars=[c for c in labeled if c not in TARGETS],
        value_vars=TARGETS,
        var_name="horizon",
        value_name="target_price_pln_m2",
    )
    long.horizon = long.horizon.str[-1].astype(int)
    long["target_quarter"] = [
        str(pd.Period(q) + h) for q, h in zip(long.origin, long.horizon)
    ]
    long.to_csv(PROCESSED / "supervised_long.csv", index=False)
    f[FEATURES].isna().mean().sort_values(ascending=False).rename(
        "missing_fraction"
    ).to_csv(TABLES / "feature_missing.csv")
    save_json(
        TABLES / "dataset_audit.json",
        dict(
            long_rows=len(long),
            independent_city_origin_groups=len(labeled),
            unique_origins=labeled.origin.nunique(),
            numeric_features=len(FEATURES),
            categorical_features=2,
            series=labeled.series_id.nunique(),
            cities=labeled.area_clean.nunique(),
            min_origin=labeled.origin.min(),
            max_origin=labeled.origin.max(),
            reference_origin=CONFIG["reference_origin"],
            test_origin=CONFIG["test_origin"],
            raw_price_observations=len(raw),
            warning="Five horizons share one origin vector; long rows are not independent markets or cycles.",
        ),
    )
    # All feature names and their provenance are explicit, including inherited lag2 naming.
    print("Training groups:", len(labeled), "long horizon rows:", len(long), flush=True)


if __name__ == "__main__":
    main()
