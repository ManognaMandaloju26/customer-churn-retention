"""Data quality checks and deliberate anomaly detection."""
from pathlib import Path
import pandas as pd

def validate_data(data_dir="data"):
    p = Path(data_dir)
    read = lambda name: pd.read_csv(p / f"{name}.csv")
    customers = read("customers")
    subs = read("subscriptions")
    usage = read("usage_snapshots")
    bills = read("billing_events")
    support = read("support_cases")
    contacts = read("campaign_contacts")
    churn = read("churn_outcomes")
    retention = read("retention_outcomes")
    offers = read("offers")
    issues = []

    def add(issue_type, entity, entity_id, detail):
        issues.append({"issue_type":issue_type,"entity":entity,"entity_id":str(entity_id),"detail":detail})

    # PK uniqueness
    pk_map = [(customers,"customer_id","Customer"),(subs,"subscription_id","Subscription"),
              (usage,"snapshot_id","UsageSnapshot"),(bills,"billing_event_id","BillingEvent"),
              (support,"support_case_id","SupportCase"),(contacts,"contact_id","CampaignContact"),
              (churn,"churn_id","ChurnOutcome"),(retention,"retention_id","RetentionOutcome"),
              (offers,"offer_id","Offer")]
    for df, col, entity in pk_map:
        dup = df[df[col].duplicated(keep=False)]
        for val in dup[col].unique():
            add("duplicate_primary_key",entity,val,f"Duplicate {col}")

    customer_ids = set(customers.customer_id)
    sub_ids = set(subs.subscription_id)
    offer_ids = set(offers.offer_id)
    for _, r in subs[~subs.customer_id.isin(customer_ids)].iterrows():
        add("foreign_key_error","Subscription",r.subscription_id,"Unknown customer_id")
    for df, col, entity in [(usage,"subscription_id","UsageSnapshot"),(bills,"subscription_id","BillingEvent")]:
        for _, r in df[~df[col].isin(sub_ids)].iterrows():
            add("foreign_key_error",entity,r.iloc[0],"Unknown subscription_id")
    for _, r in support[~support.customer_id.isin(customer_ids)].iterrows():
        add("foreign_key_error","SupportCase",r.support_case_id,"Unknown customer_id")
    for _, r in contacts[contacts.offer_id.notna() & ~contacts.offer_id.isin(offer_ids)].iterrows():
        add("foreign_key_error","CampaignContact",r.contact_id,"Unknown offer_id")

    # Temporal label leakage
    churn["prediction_date"] = pd.to_datetime(churn.prediction_date)
    churn["churn_date"] = pd.to_datetime(churn.churn_date, errors="coerce")
    bad = churn[churn.churn_date.notna() & (churn.churn_date <= churn.prediction_date)]
    for _, r in bad.iterrows():
        add("churn_before_prediction_date","ChurnOutcome",r.churn_id,"Churn date must be after prediction date")

    # Experiment assignment leakage
    assigned = contacts[contacts.experiment_group.isin(["treatment","control"])]
    for cid, group in assigned.groupby("customer_id"):
        if group.experiment_group.nunique() > 1:
            add("treatment_control_leakage","CampaignContact",cid,"Customer assigned to both experiment arms")

    # Multiple attribution
    joined = retention.merge(contacts[["contact_id","customer_id"]],on="contact_id",how="left")
    for cid, group in joined.groupby("customer_id"):
        if group.contact_id.nunique() > 1:
            add("multiple_offer_attribution","RetentionOutcome",cid,"Customer attributed to multiple contacts/offers")

    # Ineligible offer sent: flagged if a contact is sent but has a non-eligible decision reason.
    sent_bad = contacts[(contacts.delivery_status == "sent") & (contacts.decision_reason != "Eligible")]
    for _, r in sent_bad.iterrows():
        add("offer_sent_to_ineligible_customer","CampaignContact",r.contact_id,"Offer sent despite failed eligibility")

    # Arithmetic checks
    if ((bills.paid_amount < 0) | (bills.paid_amount > bills.amount)).any():
        add("billing_reconciliation","BillingEvent","multiple","Paid amount outside invoice amount")

    return pd.DataFrame(issues, columns=["issue_type","entity","entity_id","detail"])

if __name__ == "__main__":
    report = validate_data()
    Path("data").mkdir(exist_ok=True)
    report.to_csv("data/validation_issues.csv", index=False)
    print(f"Validation complete: {len(report)} issues detected")
    print(report.issue_type.value_counts().to_string() if len(report) else "No issues")
