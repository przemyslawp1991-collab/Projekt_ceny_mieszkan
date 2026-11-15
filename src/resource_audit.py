"""Fixed-candidate CPU/time/model-size audit on a development fold; no reselection."""

import io, time
import pandas as pd, joblib
from threadpoolctl import threadpool_limits
from .common import *
from .train import split, fit_model, forecast


def main():
    f = pd.read_csv(PROCESSED / "training_wide.csv")
    rows = []
    with threadpool_limits(limits=CONFIG["threads"]):
        for spec in CONFIG["trials"]:
            tr, te = split(f, CONFIG["validation_origins"][-1], spec["window"])
            start = time.perf_counter()
            m = fit_model(tr, spec)
            fit_seconds = time.perf_counter() - start
            start = time.perf_counter()
            forecast(m, te)
            predict_seconds = time.perf_counter() - start
            buffer = io.BytesIO()
            joblib.dump(m, buffer)
            rows.append(
                dict(
                    trial=spec["id"],
                    fit_seconds=fit_seconds,
                    predict_34_paths_seconds=predict_seconds,
                    serialized_model_bytes=len(buffer.getvalue()),
                    threads=CONFIG["threads"],
                )
            )
    score = pd.read_csv(TABLES / "tuning_summary.csv")
    score.merge(pd.DataFrame(rows), on="trial", validate="one_to_one").to_csv(
        TABLES / "accuracy_time_size.csv", index=False
    )


if __name__ == "__main__":
    main()
