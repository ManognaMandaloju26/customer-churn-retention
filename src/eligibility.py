"""Offer eligibility decisions with explicit rejection reasons."""
import pandas as pd

def evaluate_eligibility(predictions, subscriptions, offers, rules):
    df = predictions.merge(subscriptions[["customer_id","status","monthly_fee","plan_type"]],on="customer_id",how="left")
    rows = []
    for r in df.itertuples(index=False):
        margin = float(r.monthly_fee) * .55
        chosen = None
        reason = "No matching offer rule"
        for rule in rules.itertuples(index=False):
            offer = offers[offers.offer_id == rule.offer_id]
            if offer.empty:
                continue
            o = offer.iloc[0]
            segment_ok = rule.allowed_segment == "ALL" or rule.allowed_segment == r.plan_type
            if r.churn_probability * 100 < rule.minimum_risk_score:
                reason = "Risk score below threshold"
            elif r.status != "active":
                reason = "Subscription inactive"
            elif margin < rule.minimum_margin:
                reason = "Margin requirement failed"
            elif not segment_ok:
                reason = "Customer segment not eligible"
            elif o.discount_percentage > rule.max_discount:
                reason = "Discount exceeds allowed limit"
            else:
                chosen = o
                reason = "Eligible"
                break
        rows.append({
            "customer_id":r.customer_id,
            "prediction_date":r.prediction_date if hasattr(r, "prediction_date") else None,
            "churn_probability":float(r.churn_probability),
            "risk_category":r.risk_category,
            "eligible":chosen is not None,
            "offer_id":chosen.offer_id if chosen is not None else None,
            "offer_name":chosen.offer_name if chosen is not None else None,
            "offer_cost":float(chosen.offer_cost) if chosen is not None else 0.0,
            "estimated_margin":margin,
            "decision_reason":reason
        })
    return pd.DataFrame(rows)
