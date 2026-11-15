import argparse, time
from .common import ROOT, save_json


def main():
    p = argparse.ArgumentParser()
    p.add_argument("stage", choices=["all", "data", "train", "evaluate"])
    a = p.parse_args()
    start = time.perf_counter()
    if a.stage in ["all", "data"]:
        from .prepare_data import main as prepare
        from .features import main as features

        prepare()
        features()
    if a.stage in ["all", "train"]:
        from .train import main as train

        train()
    if a.stage in ["all", "evaluate"]:
        from .evaluate import main as evaluate
        from .report import main as report
        from .resource_audit import main as resources

        evaluate()
        resources()
        report()
    save_json(
        ROOT / f"reports/logs/{a.stage}.json",
        dict(stage=a.stage, elapsed_seconds=time.perf_counter() - start),
    )


if __name__ == "__main__":
    main()
