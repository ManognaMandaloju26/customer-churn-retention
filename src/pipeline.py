
"""Run the complete MVP pipeline."""

from pathlib import Path
import yaml
import json
import sqlite3

from src.generate_data import generate_dataset
from src.validate_data import validate_data
from src.churn_model import train_model
from src.eligibility import evaluate_eligibility
from src.campaign import run_campaign, campaign_metrics


def run_pipeline(customers=None, seed=None, output_dir=None):

    # 1. Load configuration
    cfg = yaml.safe_load(Path("config.yaml").read_text())

    n = customers or cfg.get("customers", 2000)
    sd = seed if seed is not None else cfg.get("seed", 20261022)
    out = output_dir or cfg.get("output_dir", "data")

    # 2. Generate master data and original campaign records
    tables = generate_dataset(
        customers=n,
        months=cfg.get("months", 18),
        seed=sd,
        prediction_month=cfg.get("prediction_month", 15),
        treatment_ratio=cfg.get("treatment_ratio", 0.5),
        output_dir=out
    )

    # 3. Validate generated data
    issues = validate_data(out)
    issues.to_csv(Path(out) / "validation_issues.csv", index=False)

    # 4. Store source entities in SQLite
    with sqlite3.connect(Path(out) / "customer_churn.db") as conn:

        for table_name, frame in tables.items():
            if table_name in {
                "features", "ground_truth",
                "customers", "subscriptions", "usage_snapshots",
                "billing_events", "support_cases", "offers",
                "eligibility_rules", "campaign_contacts",
                "churn_outcomes", "retention_outcomes"
            }:
                frame.to_sql(
                    table_name,
                    conn,
                    if_exists="replace",
                    index=False
                )

        issues.to_sql(
            "validation_issues",
            conn,
            if_exists="replace",
            index=False
        )

    # 5. Train churn prediction model
    metrics, predictions = train_model(out)

    # 6. Evaluate offer eligibility
    eligibility = evaluate_eligibility(
        predictions,
        tables["subscriptions"],
        tables["offers"],
        tables["eligibility_rules"]
    )

    eligibility.to_csv(
        Path(out) / "eligibility_decisions.csv",
        index=False
    )

    # 7. Build campaign results using original contacts and outcomes.
    # Do not independently randomize customers a second time.
    campaign = run_campaign(
        eligibility,
        tables["campaign_contacts"],
        tables["retention_outcomes"],
        seed=sd
    )

    campaign.to_csv(
        Path(out) / "campaign_results.csv",
        index=False
    )

    # 8. Save derived tables and portable SQL export
    with sqlite3.connect(Path(out) / "customer_churn.db") as conn:

        predictions.to_sql(
            "churn_predictions",
            conn,
            if_exists="replace",
            index=False
        )

        eligibility.to_sql(
            "eligibility_decisions",
            conn,
            if_exists="replace",
            index=False
        )

        campaign.to_sql(
            "campaign_results",
            conn,
            if_exists="replace",
            index=False
        )

        sql_dump = "\n".join(conn.iterdump())

    Path(out, "customer_churn_seed.sql").write_text(
        sql_dump,
        encoding="utf-8"
    )

    # 9. Calculate campaign metrics
    cm = campaign_metrics(campaign)

    summary = {
        "customers": n,
        "validation_issue_count": len(issues),
        "model_metrics": metrics,
        "campaign_metrics": cm
    }

    Path(out, "run_summary.json").write_text(
        json.dumps(summary, indent=2)
    )

    return summary


if __name__ == "__main__":
    print(json.dumps(run_pipeline(), indent=2))
