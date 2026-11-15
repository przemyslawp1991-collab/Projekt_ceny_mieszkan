"""Remove generated tabular/figure artifacts only; immutable raw/model snapshots retained."""

from .common import ROOT

for folder in ["data/processed", "reports/tables", "reports/figures"]:
    for p in (ROOT / folder).iterdir():
        if p.is_file() and p.suffix in [".csv", ".json", ".png"]:
            p.unlink()
