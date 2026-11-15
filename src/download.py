"""Download provider originals to a NEW candidate snapshot, without changing experiment data."""

import argparse, json, urllib.request, zipfile, io
import pandas as pd
from .common import RAW, ROOT, digest, save_json


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="data/download_candidate")
    a = p.parse_args()
    dest = (ROOT / a.output).resolve()
    if not dest.is_relative_to(ROOT):
        raise ValueError("Output must remain inside project")
    dest.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((RAW / "source_manifest.json").read_text(encoding="utf-8"))
    downloaded = []
    for r in manifest["files"]:
        if r.get("kind"):
            if r["kind"] == "direct_file":
                req = urllib.request.Request(
                    r["url"], headers={"User-Agent": "CoursePriceProject/1.0"}
                )
                target = dest / r["file"]
                target.write_bytes(urllib.request.urlopen(req, timeout=120).read())
                downloaded.append(
                    dict(file=target.name, sha256=digest(target), url=r["url"])
                )
            elif r["kind"] == "bis_country_extract":
                data = urllib.request.urlopen(r["url"], timeout=180).read()
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    name = next(n for n in z.namelist() if n.endswith(".csv"))
                    parts = []
                    with z.open(name) as stream:
                        for chunk in pd.read_csv(
                            stream, chunksize=200000, low_memory=False
                        ):
                            area = next(c for c in chunk if c.startswith("REF_AREA"))
                            parts.append(
                                chunk[chunk[area].astype(str).str.startswith("PL:")]
                            )
                    target = dest / r["file"]
                    pd.concat(parts, ignore_index=True).to_csv(target, index=False)
                    downloaded.append(
                        dict(file=target.name, sha256=digest(target), url=r["url"])
                    )
    # Historical audited report extracts are supplied with page-level provenance, not claimed to be auto-downloadable tabular APIs.
    save_json(
        dest / "download_manifest.json",
        dict(
            files=downloaded,
            note="Live provider files may have revisions. Never overwrite frozen raw. AMRON/calendar require audited extraction; supplied local hashes reproduce this study.",
        ),
    )


if __name__ == "__main__":
    main()
