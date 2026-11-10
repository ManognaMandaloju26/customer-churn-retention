
"""Campaign reporting using the original generated contacts and outcomes."""
import numpy as np
import pandas as pd


def run_campaign(decisions, contacts, retention_outcomes, seed=20261022, treatment_ratio=.5):
    # Keep the original generated campaign assignments authoritative.
    decision_cols = [
        "customer_id", "prediction_date", "churn_probability",
        "risk_category", "eligible", "offer_id", "offer_name",
        "offer_cost", "estimated_margin", "decision_reason"
    ]

    decision_data = decisions[
        [c for c in decision_cols if c in decisions.columns]
    ].copy()

    decision_data = decision_data.rename(columns={
        "offer_id": "eligibility_offer_id",
        "offer_name": "eligibility_offer_name",
        "offer_cost": "estimated_offer_cost",
        "decision_reason": "eligibility_decision_reason"
    })

    campaign = contacts.merge(
        decision_data,
        on="customer_id",
        how="left"
    )

    # Contact records are the source of truth for assignment and delivery.
    campaign["offer_name"] = np.where(
        campaign["offer_id"] == campaign["eligibility_offer_id"],
        campaign["eligibility_offer_name"],
        None
    )

    campaign["offer_cost"] = np.where(
        campaign["offer_id"] == campaign["eligibility_offer_id"],
        campaign["estimated_offer_cost"].fillna(0),
        0.0
    )

    # Attach the actual generated retention outcomes by contact ID.
    outcomes = retention_outcomes.rename(columns={
        "offer_cost": "actual_offer_cost"
    })

    campaign = campaign.merge(
        outcomes,
        on="contact_id",
        how="left",
        suffixes=("", "_outcome")
    )

    campaign["actual_offer_cost"] = campaign["actual_offer_cost"].fillna(0)
    campaign["incremental_margin"] = campaign["incremental_margin"].fillna(0)
    campaign["realized_revenue"] = campaign["realized_revenue"].fillna(0)

    return campaign


def campaign_metrics(campaign):
    if campaign.empty:
        return {
            "treatment_retention": 0,
            "control_retention": 0,
            "incremental_lift_pp": 0,
            "treatment_n": 0,
            "control_n": 0,
            "offer_cost": 0,
            "incremental_margin": 0,
            "roi_pct": 0
        }

    measured = campaign[
        campaign["experiment_group"].isin(["treatment", "control"])
        & campaign["retained_status"].notna()
    ]

    summary = measured.groupby("experiment_group")["retained_status"].agg(
        ["mean", "count"]
    )

    tr = float(summary.loc["treatment", "mean"]) if "treatment" in summary.index else 0
    cr = float(summary.loc["control", "mean"]) if "control" in summary.index else 0

    treatment_n = int(summary.loc["treatment", "count"]) if "treatment" in summary.index else 0
    control_n = int(summary.loc["control", "count"]) if "control" in summary.index else 0

    cost = float(campaign["actual_offer_cost"].sum())
    margin = float(campaign["incremental_margin"].sum())

    incremental_customers = (tr - cr) * treatment_n
    avg_contribution = (
        float(measured.loc[
            measured["experiment_group"] == "treatment",
            "estimated_margin"
        ].mean() * 3)
        if treatment_n else 0
    )

    incremental_profit = incremental_customers * avg_contribution - cost
    roi = incremental_profit / cost * 100 if cost > 0 else 0

    return {
        "treatment_retention": tr * 100,
        "control_retention": cr * 100,
        "incremental_lift_pp": (tr - cr) * 100,
        "treatment_n": treatment_n,
        "control_n": control_n,
        "offer_cost": cost,
        "incremental_margin": margin,
        "incremental_retained_customers_est": float(incremental_customers),
        "incremental_profit_est": float(incremental_profit),
        "roi_pct": roi
    }
