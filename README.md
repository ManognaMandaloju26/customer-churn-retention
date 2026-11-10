# Customer Churn Prediction & Retention Offer Optimization

An end-to-end AI-powered customer churn prediction and retention optimization solution developed for the YottaFlex.ai Associate AI Forward Deployed Engineer Hackathon.

The system generates synthetic customer data, identifies potential churn risks, evaluates retention-offer eligibility, simulates randomized treatment and control groups, and measures campaign performance through retention lift, cost and estimated ROI.

> **Disclaimer:** All customer records, predictions, offers and campaign outcomes are synthetic and simulated. They do not represent real customer data or verified real-world causal evidence.

## 1. Key Features

- Synthetic generation of 20,000 customers with a fixed random seed.
- 18 months of customer usage, billing and support history.
- Ten core business entities and plan-change event history.
- Seasonal and steady customer usage patterns.
- Churn prediction using a Random Forest classifier.
- Historical feature engineering with a prediction-date cutoff.
- Rule-based offer eligibility with rejection reasons and margin checks.
- Randomized treatment and control group assignment.
- Simulated retention outcomes and campaign ROI.
- Four deliberately injected and labelled data-quality anomalies.
- Separate ground-truth dataset.
- SQLite database and portable SQL seed export.
- Interactive Streamlit dashboard.
- Automated validation and reproducibility checks.

## 2. Technology Stack

- Python 3.10+
- Pandas and NumPy
- Scikit-learn
- SQLite
- Streamlit
- Plotly
- Pytest

## 3. Project Architecture

Synthetic Data Generation → Data Validation → Feature Engineering → Churn Prediction → Offer Eligibility → Treatment/Control Assignment → Retention Simulation → Business Metrics → Streamlit Dashboard.

## 4. Core Business Entities

1. Customer
2. Subscription
3. UsageSnapshot
4. BillingEvent
5. SupportCase
6. Offer
7. EligibilityRule
8. CampaignContact
9. ChurnOutcome
10. RetentionOutcome

Additional event history is maintained through `plan_change_events.csv`.

## 5. Installation

Python 3.10 or newer is recommended.

### Windows setup

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## 6. Run the Project

The default configuration uses 20,000 customers, 18 months of history and random seed `20261022`.

```powershell
python -m src.pipeline
```

The pipeline generates the datasets, validates records, trains the churn model, evaluates offer eligibility, simulates campaigns and exports database files.

To change the dataset size or random seed, edit `config.yaml` before running the pipeline.

## 7. Launch the Dashboard

```powershell
streamlit run app.py
```

The dashboard includes:

- **Overview:** Business KPIs and model evaluation.
- **Customer Churn:** Customer risk classifications.
- **Offer Eligibility:** Eligibility decisions and rejection reasons.
- **Campaign Results:** Treatment/control retention, campaign cost and ROI.
- **Data Quality:** Detected anomalies and validation results.

## 8. Data Outputs

The `data/` directory contains:

- Master and transaction CSV files.
- `features.csv`
- `churn_predictions.csv`
- `eligibility_decisions.csv`
- `campaign_results.csv`
- `validation_issues.csv`
- `ground_truth.csv`
- `plan_change_events.csv`
- `source_manifest.json`
- `run_summary.json`
- `customer_churn.db`
- `customer_churn_seed.sql`

## 9. Churn Prediction and Retention Methodology

- The prediction date follows the 18-month observation period.
- The churn outcome horizon is the subsequent 90 days.
- Model input features are derived from historical records available on or before the prediction date.
- Churn labels are derived from generated cancellation events.
- A Random Forest classifier estimates customer churn risk.
- Offer eligibility is evaluated using business rules, risk thresholds and margin restrictions.
- Eligible customers are assigned to treatment or control groups.
- Retention outcomes are simulated using documented business assumptions.

## 10. Required Anomaly Scenarios

The project deliberately includes four labelled anomaly cases:

| Anomaly | Ground-truth label |
|---|---|
| Churn before prediction date | `invalid_temporal_label` |
| Offer sent to an ineligible customer | `eligibility_violation` |
| Treatment/control leakage | `conflicting_assignment` |
| Multiple offer attribution | `duplicate_attribution` |

These cases are maintained separately in `ground_truth.csv`.

## 11. Validation and Testing

Run the automated tests:

```powershell
python -m pytest -q
```

The current test suite contains five tests.

Run the reproducibility comparison:

```powershell
python -m src.reproducibility
```

The default reproducibility check uses a smaller sample dataset and compares row counts and SHA-256 checksums between two generations.

A separate full-scale reproducibility check should be performed with 20,000 customers before final submission.

## 12. Reproducibility

The generator uses a fixed random seed (`20261022`) to support deterministic data generation.

The source manifest records generated data information, including row counts and checksums.

## 13. Model Limitations and Future Improvements

The current churn model is a baseline model trained on synthetic data. Its predictive performance requires further improvement.

Future improvements include:

- Time-based model evaluation.
- Feature selection and model optimization.
- Probability calibration.
- Confidence intervals for campaign lift.
- Persistent campaign event logging.
- Stronger causal inference methodology.
- Consent, security and privacy controls.

## 14. Project Objective

The objective is to demonstrate an end-to-end customer-retention workflow that combines synthetic data engineering, machine learning, business-rule enforcement, experimentation, data-quality monitoring and measurable business outputs.

**Developed for the YottaFlex.ai Associate AI Forward Deployed Engineer Hackathon.**