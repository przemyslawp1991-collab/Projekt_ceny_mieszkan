"""Check a running deployment over HTTP using only the Python standard library."""

import argparse
import json
import math
import time
import urllib.error
import urllib.request


def check(base_url, wait_seconds=60):
    base_url = base_url.rstrip("/")

    def get(path):
        with urllib.request.urlopen(base_url + path, timeout=10) as response:
            return response.read().decode("utf-8")

    deadline = time.monotonic() + wait_seconds
    while True:
        try:
            assert json.loads(get("/health"))["status"] == "ok"
            break
        except (OSError, ValueError, AssertionError):
            if time.monotonic() >= deadline:
                raise RuntimeError("API did not become available in time") from None
            time.sleep(0.5)

    assert 'id="forecast-table"' in get("/")
    assert "segmented" in get("/static/style.css")
    assert "/predict" in get("/static/dashboard.js")
    assert get("/docs")
    catalog = json.loads(get("/catalog"))
    assert "Warszawa" in catalog["areas"]

    def request(area):
        return urllib.request.Request(
            base_url + "/predict",
            data=json.dumps({"area": area, "market": "secondary"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

    with urllib.request.urlopen(request("Warszawa"), timeout=20) as response:
        result = json.load(response)
    assert result["reference_origin"] == catalog["reference_origin"]
    assert len(result["forecasts"]) == 5
    assert all(
        math.isfinite(row["prediction_pln_m2"]) and row["prediction_pln_m2"] > 0
        for row in result["forecasts"]
    )
    try:
        urllib.request.urlopen(request("Atlantyda"), timeout=10)
    except urllib.error.HTTPError as error:
        assert error.code == 422
    else:
        raise AssertionError("Unknown city should be rejected")
    print("HTTP checks passed: panel, static assets, catalog, docs, prediction and validation")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--wait", type=float, default=60)
    args = parser.parse_args()
    check(args.base_url, args.wait)
