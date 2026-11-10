"""Repeat a fixed-seed generation twice and compare CSV SHA-256 hashes."""
from pathlib import Path
import hashlib, json, tempfile
from src.generate_data import generate_dataset

def verify_reproducibility(customers=200, months=18, seed=20261022, output_dir="data"):
    base = Path(output_dir)
    run_a, run_b = base / "_repro_run_a", base / "_repro_run_b"
    for folder in (run_a, run_b):
        if folder.exists():
            import shutil
            shutil.rmtree(folder)
    generate_dataset(customers=customers, months=months, seed=seed, output_dir=run_a)
    generate_dataset(customers=customers, months=months, seed=seed, output_dir=run_b)
    results = {}
    for file_a in sorted(run_a.glob("*.csv")):
        file_b = run_b / file_a.name
        hash_a = hashlib.sha256(file_a.read_bytes()).hexdigest()
        hash_b = hashlib.sha256(file_b.read_bytes()).hexdigest()
        results[file_a.name] = {
            "rows_run_1": sum(1 for _ in file_a.open(encoding="utf-8")) - 1,
            "rows_run_2": sum(1 for _ in file_b.open(encoding="utf-8")) - 1,
            "sha256_run_1": hash_a, "sha256_run_2": hash_b,
            "match": hash_a == hash_b
        }
    report = {"seed": seed, "customers": customers, "months": months,
              "all_checksums_match": all(x["match"] for x in results.values()),
              "files": results}
    base.mkdir(parents=True, exist_ok=True)
    (base / "reproducibility_report.json").write_text(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    print(json.dumps(verify_reproducibility(), indent=2))
