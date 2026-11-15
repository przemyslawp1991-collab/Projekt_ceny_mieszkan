from pathlib import Path
import json, hashlib, yaml

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
PROCESSED = ROOT / "data/processed"
TABLES = ROOT / "reports/tables"
CONFIG = yaml.safe_load((ROOT / "config/config.yaml").read_text(encoding="utf-8"))
LOCAL = [
    "local_yoy_known2",
    "local_qoq_known2",
    "local_yoy_acceleration_known2",
    "local_volatility4_known2",
    "relative_price_known2",
    "primary_secondary_ratio_known2",
    "peer_yoy_known2",
    "log_known_price",
]
MACRO = [
    "policy_rate_lag1",
    "policy_rate_change4q_lag1",
    "inflation_yoy_lag1",
    "national_wage_yoy_lag1",
    "national_mortgage_rate_lag1",
    "national_real_credit_flow_yoy_lag1",
    "national_sloos_demand_lag1",
    "national_sloos_easing_lag1",
]
EXTRA = [
    "market_decline_breadth_known",
    "market_negative_yoy_breadth_known",
    "hedonic_qoq_known",
    "hedonic_yoy_known",
]
CREDIT = [
    "credit_count_yoy_lag2",
    "credit_count_qoq_lag2",
    "credit_count_acceleration_lag2",
    "credit_count_t4_yoy_lag2",
]
FEATURES = LOCAL + MACRO + EXTRA + CREDIT
TARGETS = [f"price_h{h}" for h in range(5)]


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save_json(p, x):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(
        json.dumps(x, ensure_ascii=False, indent=2, default=str, allow_nan=False),
        encoding="utf-8",
    )


def verify_sources():
    manifest = json.loads((RAW / "source_manifest.json").read_text(encoding="utf-8"))
    for r in manifest["files"]:
        if digest(RAW / r["file"]) != r["sha256"]:
            raise ValueError("Raw source changed: " + r["file"])
    return manifest
