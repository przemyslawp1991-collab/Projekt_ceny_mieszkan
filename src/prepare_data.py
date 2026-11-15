"""Read immutable provider files. No interpolation, backfill or train imputation here."""

import re, unicodedata
import pandas as pd, numpy as np
from .common import RAW, PROCESSED, TABLES, verify_sources, save_json


def slug(s):
    s = (
        unicodedata.normalize("NFKD", s.replace("ł", "l").replace("Ł", "L"))
        .encode("ascii", "ignore")
        .decode()
        .lower()
    )
    return re.sub("[^a-z0-9]+", "_", s).strip("_")


def quarter(s):
    m = re.fullmatch(r"(I|II|III|IV)\s+(\d{4})", str(s).strip())
    return f"{m[2]}Q{dict(I=1, II=2, III=3, IV=4)[m[1]]}" if m else None


def read_prices():
    rows = []
    for market, sheet in [
        ("primary", "Rynek pierwotny"),
        ("secondary", "Rynek wtórny"),
    ]:
        z = pd.read_excel(RAW / "NBP_prices.xlsx", sheet_name=sheet, header=None)
        for typ, cols, qcol in [
            ("transaction", range(24, 44), 0),
            ("offer", range(1, 21), 0),
        ] + (
            [("hedonic_qoq", range(47, 66), 46), ("hedonic_yoy", range(68, 87), 46)]
            if market == "secondary"
            else []
        ):
            for c in cols:
                name = str(z.iloc[6, c]).strip()
                for i in range(7, len(z)):
                    q = quarter(z.iloc[i, qcol])
                    v = pd.to_numeric(z.iloc[i, c], errors="coerce")
                    if q is None or pd.isna(v):
                        continue
                    rows.append(
                        dict(
                            quarter=q,
                            area=name,
                            area_clean=name.rstrip("*").strip(),
                            market=market,
                            series_type=typ,
                            value=float(v),
                            series_id=market + "_avg_" + slug(name),
                            is_aggregate=c
                            not in (
                                range(24, 41)
                                if typ == "transaction"
                                else range(1, 18)
                                if typ == "offer"
                                else range(47, 63)
                                if typ == "hedonic_qoq"
                                else range(68, 84)
                            ),
                            sheet=sheet,
                            row_excel=i + 1,
                            column_excel=c + 1,
                        )
                    )
    f = pd.DataFrame(rows)
    assert not f.duplicated(["quarter", "area", "market", "series_type"]).any()
    assert f[f.series_type.isin(["transaction", "offer"])].value.gt(0).all()
    return f


def bis_quarter(filename, cpi=False):
    z = pd.read_csv(RAW / filename, low_memory=False)
    z.columns = [c.split(":")[0] for c in z.columns]
    z = z[z.FREQ.str.startswith("M:")].copy()
    if cpi:
        z = z[z.UNIT_MEASURE.str.startswith("628:")]
    z["quarter"] = pd.PeriodIndex(z.TIME_PERIOD, freq="M").asfreq("Q").astype(str)
    z["OBS_VALUE"] = pd.to_numeric(z.OBS_VALUE, errors="coerce")
    z = z.sort_values("TIME_PERIOD")
    if z.duplicated("TIME_PERIOD").any():
        raise ValueError("Multiple monthly BIS series")
    g = z.groupby("quarter").OBS_VALUE
    v = g.mean() if cpi else g.last()
    return v.where(g.count().eq(3))


def read_macro():
    idx = pd.period_range("1993Q1", "2026Q3", freq="Q").astype(str)
    out = pd.DataFrame(index=idx)
    out["policy_rate"] = bis_quarter("WS_CBPOL_PL.csv")
    out["cpi"] = bis_quarter("WS_LONG_CPI_PL.csv", True)
    out["inflation"] = out.cpi.pct_change(4, fill_method=None) * 100
    out["policy_change"] = out.policy_rate.diff(4)
    z = pd.read_excel(
        RAW / "GUS_quarterly.xlsx", sheet_name="WARUNKI ŻYCIA LUDNOŚCI", header=None
    )
    years = z.iloc[3].ffill()
    for c in range(3, z.shape[1]):
        if not re.match(r"[1-4] kw\.", str(z.iloc[4, c])):
            continue
        vals = pd.to_numeric(z.iloc[[5, 6], c], errors="coerce").dropna()
        if len(vals):
            assert vals.max() - vals.min() < 1e-6
            out.loc[f"{int(years.iloc[c])}Q{str(z.iloc[4, c])[0]}", "wage"] = vals.iloc[
                -1
            ]
    out["wage_yoy"] = out.wage.pct_change(4, fill_method=None) * 100
    z = pd.read_excel(RAW / "NBP_SLOOS.xlsx", sheet_name="Szeregi", header=None)
    for c in range(2, z.shape[1]):
        m = re.fullmatch(r"(I|II|III|IV)\.(\d{4})", str(z.iloc[2, c]).strip())
        if not m:
            continue
        q = f"{m[2]}Q{dict(I=1, II=2, III=3, IV=4)[m[1]]}"
        for name, r in [("sloos_easing", 63), ("sloos_demand", 105)]:
            out.loc[q, name] = pd.to_numeric(z.iloc[r, c], errors="coerce") * 100
    z = pd.read_excel(RAW / "NBP_MIR.xlsx", sheet_name="4 OPN2PLN", header=None)
    months = []
    for c in range(6, z.shape[1]):
        d = z.iloc[1, c]
        if not isinstance(d, (pd.Timestamp, __import__("datetime").datetime)):
            continue
        rate = pd.to_numeric(z.iloc[3, c], errors="coerce") * 100
        value = pd.to_numeric(z.iloc[11, c], errors="coerce")
        if pd.notna(rate) and pd.notna(value):
            months.append(
                dict(quarter=str(pd.Period(d, freq="Q")), rate=rate, value=value)
            )
    mm = pd.DataFrame(months)
    for q, g in mm.groupby("quarter"):
        if len(g) == 3 and q >= "2015Q1":
            out.loc[q, "mortgage_rate"] = np.average(g.rate, weights=g.value)
            out.loc[q, "mortgage_flow"] = g.value.sum()
    out["real_flow_yoy"] = (out.mortgage_flow / out.cpi).pct_change(
        4, fill_method=None
    ) * 100
    return out.rename_axis("quarter")


def main():
    verify_sources()
    f = read_prices()
    f.to_csv(PROCESSED / "prices_long.csv", index=False)
    m = read_macro()
    m.to_csv(PROCESSED / "macro.csv")
    c = pd.read_csv(RAW / "AMRON_counts_audited.csv")
    assert not c.quarter.duplicated().any()
    annual = c.assign(year=c.quarter.str[:4]).groupby("year").mortgage_count.sum()
    for y, v in {
        "2020": 204170,
        "2021": 256456,
        "2022": 126315,
        "2023": 162375,
        "2024": 202661,
    }.items():
        assert annual[y] == v, (y, annual[y])
    save_json(
        TABLES / "source_audit.json",
        dict(
            raw_provider_observations=len(f),
            price_min_quarter=f.quarter.min(),
            price_max_quarter=f.quarter.max(),
            duplicate_keys=int(
                f.duplicated(["quarter", "area", "market", "series_type"]).sum()
            ),
            nonpositive_prices=int(
                f[f.series_type.eq("transaction")].value.le(0).sum()
            ),
            mortgage_count_quarters=len(c),
            macro_missing=m.isna().sum().to_dict(),
        ),
    )
    print("Prepared provider observations:", len(f), flush=True)


if __name__ == "__main__":
    main()
