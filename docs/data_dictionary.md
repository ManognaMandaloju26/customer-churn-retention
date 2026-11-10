# Data Dictionary and Relational Schema

All records are synthetic. Dates use ISO-8601 (`YYYY-MM-DD`); monetary amounts are INR (₹); IDs are immutable strings. `required` means non-null in valid baseline records. Injected anomalies are explicitly listed in `ground_truth.csv`.

| Entity / CSV | Field | Type / unit | Required | Allowed values / validation | Key |
|---|---|---|---|---|---|
| Customer / customers | customer_id | string | Yes | `CUS-` + six digits; unique | PK |
| Customer | customer_name | string | Yes | Synthetic display name | |
| Customer | email | string | Yes | Unique `example.test` address | UQ |
| Customer | city | string | Yes | Hyderabad, Bengaluru, Chennai, Pune, Delhi, Mumbai | |
| Customer | customer_segment | enum | Yes | Basic, Standard, Premium | |
| Customer | usage_pattern | enum | Yes | seasonal, steady | |
| Customer | signup_date | date | Yes | Not after prediction date | |
| Customer | created_at | datetime | Yes | ISO datetime | |
| Subscription / subscriptions | subscription_id | string | Yes | `SUB-CUS-xxxxxx-01`; unique | PK |
| Subscription | customer_id | string | Yes | Must exist in Customer | FK |
| Subscription | product_id | string | Yes | STREAM-01 | |
| Subscription | plan_type | enum | Yes | Basic, Standard, Premium; current plan | |
| Subscription | monthly_fee | decimal INR | Yes | Positive; matches current plan | |
| Subscription | start_date | date | Yes | On/after customer signup | |
| Subscription | end_date | date/null | No | Null for active subscriptions; >= start | |
| Subscription | status | enum | Yes | active, cancelled, paused | |
| UsageSnapshot / usage_snapshots | snapshot_id | string | Yes | `SNAP-<subscription-id>-YYYY-MM`; unique | PK |
| UsageSnapshot | subscription_id | string | Yes | Must exist in Subscription | FK |
| UsageSnapshot | snapshot_date | date | Yes | Within subscription observation period | |
| UsageSnapshot | usage_minutes | integer minutes | Yes | >= 0 | |
| UsageSnapshot | login_count | integer | Yes | >= 0 | |
| UsageSnapshot | data_consumption_gb | decimal GB | Yes | >= 0 | |
| BillingEvent / billing_events | billing_event_id | string | Yes | Unique invoice event ID | PK |
| BillingEvent | subscription_id | string | Yes | Must exist in Subscription | FK |
| BillingEvent | invoice_date, due_date | date | Yes | due_date >= invoice_date | |
| BillingEvent | amount, paid_amount | decimal INR | Yes | 0 <= paid_amount <= amount | |
| BillingEvent | payment_status | enum | Yes | paid, partial, failed; reconciles to amounts | |
| BillingEvent | overdue_days | integer days | Yes | >= 0 | |
| SupportCase / support_cases | support_case_id | string | Yes | Unique case ID | PK |
| SupportCase | customer_id | string | Yes | Must exist in Customer | FK |
| SupportCase | created_at, resolution_date | date/null | Yes/No | Resolution date >= creation date | |
| SupportCase | issue_category | enum | Yes | Payment, Technical, Cancellation, Content, Other | |
| SupportCase | priority | enum | Yes | Low, Medium, High | |
| SupportCase | resolution_status | enum | Yes | resolved, open | |
| Offer / offers | offer_id | string | Yes | `OFF-2026-` + six digits | PK |
| Offer | offer_name | string | Yes | Non-empty | |
| Offer | discount_percentage | decimal % | Yes | 0–100 | |
| Offer | offer_cost | decimal INR | Yes | >= 0 | |
| Offer | minimum_margin | decimal INR | Yes | >= 0 | |
| Offer | status | enum | Yes | active, inactive | |
| EligibilityRule / eligibility_rules | rule_id | string | Yes | Unique rule ID | PK |
| EligibilityRule | offer_id | string | Yes | Must exist in Offer | FK |
| EligibilityRule | minimum_risk_score | decimal points | Yes | 0–100 | |
| EligibilityRule | minimum_margin | decimal INR | Yes | >= 0 | |
| EligibilityRule | allowed_segment | enum | Yes | ALL, Basic, Standard, Premium | |
| EligibilityRule | max_discount | decimal % | Yes | 0–100 | |
| CampaignContact / campaign_contacts | contact_id | string | Yes | Unique contact ID | PK |
| CampaignContact | customer_id | string | Yes | Must exist in Customer | FK |
| CampaignContact | offer_id | string/null | No | Null when not eligible; otherwise valid Offer | FK |
| CampaignContact | experiment_group | enum | Yes | treatment, control, not_eligible | |
| CampaignContact | contact_date | date | Yes | On/after prediction date | |
| CampaignContact | delivery_status | enum | Yes | sent, withheld_control, not_sent | |
| CampaignContact | decision_reason | string | Yes | Explicit eligibility reason | |
| ChurnOutcome / churn_outcomes | churn_id | string | Yes | `CHURN-<customer-id>-2026` | PK |
| ChurnOutcome | customer_id | string | Yes | Must exist in Customer | FK |
| ChurnOutcome | prediction_date | date | Yes | Feature cutoff | |
| ChurnOutcome | churn_date | date/null | No | Must be after prediction date for positive label | |
| ChurnOutcome | churn_type | enum | Yes | voluntary, involuntary, none | |
| ChurnOutcome | churn_label | integer | Yes | 0 or 1; derived from churn event | |
| ChurnOutcome | prediction_horizon_days | integer days | Yes | 90 | |
| RetentionOutcome / retention_outcomes | retention_id | string | Yes | Unique retention event ID | PK |
| RetentionOutcome | contact_id | string | Yes | Must exist in CampaignContact | FK |
| RetentionOutcome | observation_date | date | Yes | After contact date | |
| RetentionOutcome | retained_status | integer | Yes | 0 or 1 | |
| RetentionOutcome | realized_revenue, offer_cost, incremental_margin | decimal INR | Yes | Derived from observed outcome and offer | |

## Additional event table

`plan_change_events.csv` records subscription plan changes. Fields: `plan_change_id` (PK, unique string), `subscription_id` (FK), `customer_id` (FK), `effective_date` (date), `old_plan` and `new_plan` (Basic/Standard/Premium and must differ), `change_reason` (customer_request/retention_save/usage_fit), and `recorded_at` (datetime/date, not before effective date).

## Relationships and cardinality

- Customer 1:N Subscription (current generator creates one subscription per customer).
- Subscription 1:N UsageSnapshot and BillingEvent.
- Customer 1:N SupportCase and ChurnOutcome.
- Subscription 1:N PlanChangeEvent.
- Offer 1:N EligibilityRule and CampaignContact.
- Customer 1:N CampaignContact (one clean baseline campaign contact per customer).
- CampaignContact 1:0..1 RetentionOutcome in the clean baseline; duplicate attribution is deliberately injected as a labelled anomaly.
- EligibilityRule and Offer are related 1:N; CampaignContact is the bridge-like event connecting Customer and Offer.

## Lifecycle, time and integrity rules

1. Create Customer and Subscription master records before dependent records.
2. Usage, billing, support and plan-change events reference existing parent IDs.
3. Features are computed only from events dated on/before the prediction date.
4. Churn labels use the documented 90-day horizon after the prediction date.
5. Offer delivery requires an eligible decision; controls are assigned but offers are withheld.
6. A customer may belong to only one experiment arm in the clean baseline.
7. Retention attribution is one contact per customer in the clean baseline.
8. Injected exceptions are identified in `ground_truth.csv` with issue type and expected classification; do not interpret them as clean baseline records.
