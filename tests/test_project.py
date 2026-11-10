from pathlib import Path
import pandas as pd
from src.generate_data import generate_dataset
from src.validate_data import validate_data
from src.reproducibility import verify_reproducibility

def test_generator_creates_all_core_entities_and_plan_events(tmp_path):
    tables = generate_dataset(customers=100,seed=123,output_dir=tmp_path)
    expected = {"customers","subscriptions","usage_snapshots","billing_events","support_cases",
                "offers","eligibility_rules","campaign_contacts","churn_outcomes","retention_outcomes",
                "plan_change_events","ground_truth"}
    assert expected.issubset(set(tables))
    assert len(tables["customers"]) == 100
    assert set(tables["customers"].usage_pattern).issubset({"seasonal","steady"})
    assert set(tables["plan_change_events"].subscription_id).issubset(set(tables["subscriptions"].subscription_id))

def test_primary_keys_and_parent_links(tmp_path):
    tables = generate_dataset(customers=100,seed=123,output_dir=tmp_path)
    assert tables["customers"].customer_id.is_unique
    assert tables["subscriptions"].subscription_id.is_unique
    assert set(tables["subscriptions"].customer_id).issubset(set(tables["customers"].customer_id))
    assert set(tables["usage_snapshots"].subscription_id).issubset(set(tables["subscriptions"].subscription_id))
    assert set(tables["billing_events"].subscription_id).issubset(set(tables["subscriptions"].subscription_id))

def test_all_four_known_anomalies_are_detected(tmp_path):
    generate_dataset(customers=100,seed=20261022,output_dir=tmp_path)
    issues = validate_data(tmp_path)
    kinds = set(issues.issue_type)
    expected = {"churn_before_prediction_date","offer_sent_to_ineligible_customer",
                "treatment_control_leakage","multiple_offer_attribution"}
    assert expected.issubset(kinds)

def test_reproducibility_hashes_match(tmp_path):
    report = verify_reproducibility(customers=50, months=18, seed=20261022, output_dir=tmp_path)
    assert report["all_checksums_match"]

def test_eighteen_month_history_and_pre_prediction_features(tmp_path):
    tables = generate_dataset(customers=25,months=18,seed=123,prediction_month=18,output_dir=tmp_path)
    assert tables["usage_snapshots"].groupby("subscription_id").size().eq(18).all()
    assert tables["features"].prediction_date.nunique() == 1
    cutoff = pd.to_datetime(tables["features"].prediction_date.iloc[0])
    assert pd.to_datetime(tables["usage_snapshots"].snapshot_date).max() <= cutoff
