"""Deterministic synthetic customer churn and retention data generator."""
from pathlib import Path
import argparse
import json
import hashlib
import yaml
import numpy as np
import pandas as pd

def _month_end(start, offset):
    return (pd.Timestamp(start) + pd.DateOffset(months=offset) + pd.offsets.MonthEnd(0)).normalize()

def generate_dataset(customers=2000, months=18, seed=20261022, prediction_month=15,
                     treatment_ratio=0.5, output_dir="data", inject_anomalies=True):
    rng = np.random.default_rng(seed)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    start = pd.Timestamp("2025-01-01")

    # 1. Master data
    ids = [f"CUS-{i:06d}" for i in range(1, customers + 1)]
    segments = rng.choice(["Basic", "Standard", "Premium"], customers, p=[.45, .40, .15])
    cities = rng.choice(["Hyderabad", "Bengaluru", "Chennai", "Pune", "Delhi", "Mumbai"], customers)
    signup_offsets = rng.integers(0, 7, customers)
    customer_df = pd.DataFrame({
        "customer_id": ids,
        "customer_name": [f"Customer {i:06d}" for i in range(1, customers + 1)],
        "email": [f"customer{i:06d}@example.test" for i in range(1, customers + 1)],
        "city": cities, "customer_segment": segments,
        "usage_pattern": rng.choice(["seasonal", "steady"], customers, p=[.22, .78]),
        "signup_date": [(start + pd.DateOffset(months=int(x))).date().isoformat() for x in signup_offsets],
        "created_at": "2025-01-01T00:00:00"
    })

    plan_price = {"Basic": 299.0, "Standard": 599.0, "Premium": 999.0}
    subs, usage, bills, support, plan_changes = [], [], [], [], []
    churn_dates, churn_types, risk_latent = {}, {}, {}
    prediction_date = _month_end(start, prediction_month - 1)
    horizon_end = prediction_date + pd.Timedelta(days=90)

    # Create a latent behavioral risk; labels later derive from actual generated events.
    for i, cid in enumerate(ids):
        plan = segments[i]
        sid = f"SUB-{cid}-01"
        original_plan = plan
        change_month = None
        changed_plan = None
        if rng.random() < 0.18 and prediction_month >= 4:
            change_month = int(rng.integers(3, prediction_month + 1))
            alternatives = [p for p in plan_price if p != plan]
            changed_plan = str(rng.choice(alternatives))
            plan_changes.append({
                "plan_change_id": f"PLANCHANGE-{cid}-01",
                "subscription_id": sid, "customer_id": cid,
                "effective_date": _month_end(start, change_month - 1).date().isoformat(),
                "old_plan": original_plan, "new_plan": changed_plan,
                "change_reason": str(rng.choice(["customer_request", "retention_save", "usage_fit"])),
                "recorded_at": _month_end(start, change_month - 1).date().isoformat()
            })
        subs.append({
            "subscription_id": sid, "customer_id": cid, "product_id": "STREAM-01",
            "plan_type": changed_plan or original_plan, "monthly_fee": plan_price[changed_plan or original_plan],
            "start_date": customer_df.loc[i, "signup_date"],
            "end_date": None, "status": "active"
        })
        base_risk = rng.beta(2, 7)
        usage_decline = rng.uniform(0, 0.75) if rng.random() < 0.35 else rng.uniform(0, 0.25)
        payment_risk = rng.random()
        latent = min(0.95, max(0.02, base_risk + usage_decline * .30 + payment_risk * .12))
        risk_latent[cid] = latent

        actual_churn = rng.random() < min(0.45, 0.015 + latent * 0.55)
        churn_date = None
        if actual_churn:
            churn_date = prediction_date + pd.Timedelta(days=int(rng.integers(1, 91)))
            churn_dates[cid] = churn_date
            churn_types[cid] = "involuntary" if payment_risk > .78 else "voluntary"

        # Monthly usage snapshots, strictly before prediction date.
        customer_pattern = customer_df.loc[i, "usage_pattern"]
        for m in range(1, prediction_month + 1):
            dt = _month_end(start, m - 1)
            seasonal_amplitude = 0.35 if customer_pattern == "seasonal" else 0.08
            seasonal = 1.0 + seasonal_amplitude * np.sin((m / 12) * 2 * np.pi)
            if change_month is not None and m >= change_month:
                plan = changed_plan
            decline_factor = max(.18, 1 - usage_decline * (m / prediction_month))
            minutes = max(0, int(rng.normal(900 * seasonal * decline_factor, 180)))
            logins = max(0, int(rng.normal(18 * decline_factor, 4)))
            data_gb = round(max(.1, rng.normal(22 * decline_factor, 5)), 2)
            usage.append({
                "snapshot_id": f"SNAP-{sid}-{dt.strftime('%Y-%m')}",
                "subscription_id": sid, "snapshot_date": dt.date().isoformat(),
                "usage_minutes": minutes, "login_count": logins,
                "data_consumption_gb": data_gb
            })

            # Billing records, including occasional late/failed payments.
            amount = plan_price[plan]
            failed = rng.random() < (0.025 + payment_risk * .12)
            paid = 0.0 if failed else amount if rng.random() > .07 else round(amount * .5, 2)
            due = dt + pd.Timedelta(days=5)
            paid_date = None if paid == 0 else (due + pd.Timedelta(days=int(rng.integers(-4, 25)))).date().isoformat()
            bills.append({
                "billing_event_id": f"BILL-{sid}-{dt.strftime('%Y-%m')}",
                "subscription_id": sid, "invoice_date": dt.date().isoformat(),
                "due_date": due.date().isoformat(), "amount": amount,
                "paid_amount": paid, "payment_status": "failed" if paid == 0 else ("partial" if paid < amount else "paid"),
                "overdue_days": 0 if paid == amount else int(rng.integers(1, 35))
            })

        # Support events; more likely when latent risk is high.
        n_cases = int(rng.poisson(0.25 + latent * 2.0))
        for j in range(n_cases):
            m = int(rng.integers(1, prediction_month + 1))
            dt = _month_end(start, m - 1) - pd.Timedelta(days=int(rng.integers(0, 20)))
            resolved = rng.random() > (0.15 + latent * .25)
            support.append({
                "support_case_id": f"CASE-{cid}-{j+1:02d}", "customer_id": cid,
                "created_at": dt.date().isoformat(),
                "issue_category": rng.choice(["Payment", "Technical", "Cancellation", "Content", "Other"]),
                "priority": rng.choice(["Low", "Medium", "High"], p=[.45, .4, .15]),
                "resolution_status": "resolved" if resolved else "open",
                "resolution_date": (dt + pd.Timedelta(days=int(rng.integers(1, 8)))).date().isoformat() if resolved else None
            })

    subscription_df = pd.DataFrame(subs)
    usage_df = pd.DataFrame(usage)
    billing_df = pd.DataFrame(bills)
    support_df = pd.DataFrame(support, columns=["support_case_id","customer_id","created_at","issue_category","priority","resolution_status","resolution_date"])

    # Derived customer features from source records, no future data.
    u = usage_df.copy()
    u["snapshot_date"] = pd.to_datetime(u["snapshot_date"])
    u = u.sort_values("snapshot_date")
    usage_groups = {k:g for k,g in u.groupby("subscription_id", sort=False)}
    billing_groups = {k:g for k,g in billing_df.groupby("subscription_id", sort=False)}
    support_groups = {k:g for k,g in support_df.groupby("customer_id", sort=False)}
    features = []
    segment_lookup = dict(zip(ids, segments))
    for cid in ids:
        sid = f"SUB-{cid}-01"
        hist = usage_groups[sid]
        first = hist.iloc[0]
        last = hist.iloc[-1]
        early = hist.head(3).usage_minutes.mean()
        usage_change = (last.usage_minutes - early) / max(early, 1)
        b = billing_groups.get(sid, billing_df.iloc[0:0])
        s = support_groups.get(cid, support_df.iloc[0:0])
        failed_count = int((b.payment_status == "failed").sum())
        overdue_avg = float(b.overdue_days.mean()) if len(b) else 0
        open_cases = int((s.resolution_status == "open").sum())
        downgrade = bool(usage_change < -0.35 and segment_lookup[cid] != "Basic")
        score = min(100, max(0, 35 + (-usage_change * 55) + failed_count * 4 + open_cases * 5 + overdue_avg * .25))
        features.append({
            "customer_id": cid, "prediction_date": prediction_date.date().isoformat(),
            "usage_change_pct": round(usage_change * 100, 2),
            "login_count_latest": int(last.login_count),
            "failed_payment_count": failed_count, "avg_overdue_days": round(overdue_avg, 2),
            "support_case_count": int(len(s)), "unresolved_cases": open_cases,
            "plan_downgrade_signal": int(downgrade), "rule_risk_score": round(score, 2)
        })
    feature_df = pd.DataFrame(features)

    # Ground-truth churn labels from actual churn event dates.
    churn_rows = []
    for cid in ids:
        d = churn_dates.get(cid)
        churn_rows.append({
            "churn_id": f"CHURN-{cid}-2026", "customer_id": cid,
            "prediction_date": prediction_date.date().isoformat(),
            "churn_date": d.date().isoformat() if d is not None else None,
            "churn_type": churn_types.get(cid, "none"),
            "churn_label": int(d is not None), "prediction_horizon_days": 90
        })
    churn_df = pd.DataFrame(churn_rows)

    # Offer and eligibility rules.
    offers_df = pd.DataFrame([
        {"offer_id":"OFF-2026-000001","offer_name":"10% Renewal Discount","discount_percentage":10,"offer_cost":60.0,"minimum_margin":100.0,"status":"active"},
        {"offer_id":"OFF-2026-000002","offer_name":"20% Renewal Discount","discount_percentage":20,"offer_cost":120.0,"minimum_margin":180.0,"status":"active"},
        {"offer_id":"OFF-2026-000003","offer_name":"Loyalty Bonus","discount_percentage":5,"offer_cost":35.0,"minimum_margin":70.0,"status":"active"}
    ])
    rules_df = pd.DataFrame([
        {"rule_id":"RULE-001","offer_id":"OFF-2026-000001","minimum_risk_score":50,"minimum_margin":100,"allowed_segment":"ALL","max_discount":15},
        {"rule_id":"RULE-002","offer_id":"OFF-2026-000002","minimum_risk_score":70,"minimum_margin":180,"allowed_segment":"Premium","max_discount":25},
        {"rule_id":"RULE-003","offer_id":"OFF-2026-000003","minimum_risk_score":40,"minimum_margin":70,"allowed_segment":"ALL","max_discount":10}
    ])

    # Eligibility and experiment assignment.
    contacts, ret_outcomes = [], []
    customer_index = {r.customer_id: r for r in feature_df.itertuples(index=False)}
    segment_index = dict(zip(ids, segments))
    subscription_index = dict(zip(ids, [plan_price[s] for s in segments]))
    offer_counter = 0
    for cid in ids:
        f = customer_index[cid]
        plan = segment_index[cid]
        monthly_fee = subscription_index[cid]
        # Approximate contribution margin: monthly fee minus service cost.
        margin = monthly_fee * .55
        selected = None
        eligible_reasons = []
        for rule in rules_df.itertuples(index=False):
            offer = offers_df[offers_df.offer_id == rule.offer_id].iloc[0]
            segment_ok = rule.allowed_segment == "ALL" or rule.allowed_segment == plan
            ok = (f.rule_risk_score >= rule.minimum_risk_score and margin >= rule.minimum_margin
                  and segment_ok and offer.discount_percentage <= rule.max_discount)
            if ok:
                selected = offer
                break
            if f.rule_risk_score < rule.minimum_risk_score:
                eligible_reasons.append("Risk score below threshold")
            elif margin < rule.minimum_margin:
                eligible_reasons.append("Margin requirement failed")
            elif not segment_ok:
                eligible_reasons.append("Segment not eligible")
        if selected is None:
            # Keep a decision record even when no offer qualifies.
            contacts.append({
                "contact_id": f"CONTACT-{cid}-001", "customer_id": cid, "offer_id": None,
                "experiment_group":"not_eligible", "contact_date": prediction_date.date().isoformat(),
                "delivery_status":"not_sent", "decision_reason": eligible_reasons[0] if eligible_reasons else "No matching rule"
            })
            continue
        offer_counter += 1
        group = "treatment" if rng.random() < treatment_ratio else "control"
        # Treatment customers are assigned an offer; control gets the offer_id as experiment arm reference but not delivered.
        contact_id = f"CONTACT-{cid}-001"
        delivered = group == "treatment"
        contacts.append({
            "contact_id": contact_id, "customer_id":cid, "offer_id":selected.offer_id,
            "experiment_group":group, "contact_date":prediction_date.date().isoformat(),
            "delivery_status":"sent" if delivered else "withheld_control",
            "decision_reason":"Eligible"
        })
        base_prob = min(.85, .03 + risk_latent[cid] * .40)
        treatment_reduction = (selected.discount_percentage / 100) * .55 if delivered else 0
        churn_prob_after_offer = max(.01, base_prob - treatment_reduction)
        churned = bool(rng.random() < churn_prob_after_offer)
        retention_id = f"RET-{cid}-2026"
        ret_outcomes.append({
            "retention_id":retention_id, "contact_id":contact_id,
            "observation_date":horizon_end.date().isoformat(),
            "retained_status":int(not churned),
            "realized_revenue":round(monthly_fee * (3 if not churned else 0),2),
            "offer_cost":float(selected.offer_cost if delivered and not churned else 0),
            "incremental_margin":round((monthly_fee * .55 * 3 if not churned else 0) - (selected.offer_cost if delivered and not churned else 0),2)
        })

    contacts_df = pd.DataFrame(contacts)
    retention_df = pd.DataFrame(ret_outcomes)

    # Deliberately inject four labelled anomalies into a separate exception layer.
    ground_truth = []
    if inject_anomalies and customers >= 4:
        # A) Churn label before prediction date.
        churn_df.loc[0, "churn_date"] = (prediction_date - pd.Timedelta(days=2)).date().isoformat()
        ground_truth.append({"issue_id":"ISSUE-001","entity":"ChurnOutcome","entity_id":churn_df.loc[0,"churn_id"],"issue_type":"churn_before_prediction_date","ground_truth":"invalid_temporal_label"})
        # B) Offer sent to ineligible customer: change one not-eligible contact to a sent offer.
        not_elig = contacts_df.index[contacts_df.experiment_group == "not_eligible"].tolist()
        if not_elig:
            idx = not_elig[0]
            contacts_df.loc[idx, ["offer_id","experiment_group","delivery_status"]] = ["OFF-2026-000002","treatment","sent"]
            ground_truth.append({"issue_id":"ISSUE-002","entity":"CampaignContact","entity_id":contacts_df.loc[idx,"contact_id"],"issue_type":"offer_sent_to_ineligible_customer","ground_truth":"eligibility_violation"})
        # C) Treatment/control leakage: duplicate customer assignment to opposite arm.
        eligible_idx = contacts_df.index[contacts_df.experiment_group.isin(["treatment","control"])].tolist()
        if eligible_idx:
            idx = eligible_idx[0]
            original = contacts_df.loc[idx].copy()
            duplicate = original.copy()
            duplicate["contact_id"] = original["contact_id"] + "-LEAK"
            duplicate["experiment_group"] = "control" if original["experiment_group"] == "treatment" else "treatment"
            duplicate["delivery_status"] = "withheld_control" if duplicate["experiment_group"] == "control" else "sent"
            contacts_df = pd.concat([contacts_df, pd.DataFrame([duplicate])], ignore_index=True)
            ground_truth.append({"issue_id":"ISSUE-003","entity":"CampaignContact","entity_id":duplicate["contact_id"],"issue_type":"treatment_control_leakage","ground_truth":"conflicting_assignment"})
        # D) Duplicate retention attribution: second retention outcome for same customer via duplicate contact.
        if eligible_idx and len(retention_df):
            valid_idx = [idx for idx in eligible_idx if contacts_df.loc[idx, "contact_id"] in set(retention_df.contact_id)]
            if valid_idx:
                idx = valid_idx[0]
                original_ret = retention_df[retention_df.contact_id == contacts_df.loc[idx,"contact_id"]]
                if len(original_ret):
                    dup_ret = original_ret.iloc[0].copy()
                    dup_ret["retention_id"] = dup_ret["retention_id"] + "-DUP"
                    dup_contact = contacts_df.loc[idx].copy()
                    dup_contact["contact_id"] = contacts_df.loc[idx,"contact_id"] + "-ATTR"
                    dup_contact["offer_id"] = "OFF-2026-000003" if contacts_df.loc[idx,"offer_id"] != "OFF-2026-000003" else "OFF-2026-000001"
                    contacts_df = pd.concat([contacts_df, pd.DataFrame([dup_contact])], ignore_index=True)
                    dup_ret["contact_id"] = dup_contact["contact_id"]
                    retention_df = pd.concat([retention_df, pd.DataFrame([dup_ret])], ignore_index=True)
                    ground_truth.append({"issue_id":"ISSUE-004","entity":"RetentionOutcome","entity_id":dup_ret["retention_id"],"issue_type":"multiple_offer_attribution","ground_truth":"duplicate_attribution"})

    tables = {
        "customers":customer_df, "subscriptions":subscription_df, "usage_snapshots":usage_df,
        "billing_events":billing_df, "support_cases":support_df, "offers":offers_df,
        "eligibility_rules":rules_df, "campaign_contacts":contacts_df,
        "plan_change_events":pd.DataFrame(plan_changes, columns=["plan_change_id","subscription_id","customer_id","effective_date","old_plan","new_plan","change_reason","recorded_at"]),
        "churn_outcomes":churn_df, "retention_outcomes":retention_df,
        "features":feature_df, "ground_truth":pd.DataFrame(ground_truth)
    }
    manifest = {}
    for name, df in tables.items():
        path = out / f"{name}.csv"
        df.to_csv(path, index=False)
        raw = path.read_bytes()
        manifest[name] = {"rows":len(df), "sha256":hashlib.sha256(raw).hexdigest(), "file":str(path)}
    (out / "source_manifest.json").write_text(json.dumps(manifest, indent=2))
    return tables

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--customers", type=int, default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    cfg = yaml.safe_load(Path("config.yaml").read_text()) if Path("config.yaml").exists() else {}
    generate_dataset(
        customers=args.customers or cfg.get("customers", 2000),
        months=cfg.get("months",18), seed=args.seed if args.seed is not None else cfg.get("seed",20261022),
        prediction_month=cfg.get("prediction_month",15),
        treatment_ratio=cfg.get("treatment_ratio",.5),
        output_dir=args.output or cfg.get("output_dir","data")
    )
    print(f"Generated dataset in {args.output or cfg.get('output_dir','data')}")

if __name__ == "__main__":
    main()
