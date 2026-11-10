
-- Customer Churn Prediction & Retention Offer Optimization
-- Database schema: 16 tables
-- SQLite

PRAGMA foreign_keys = ON;

-- 1. Customers
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT,
    email TEXT,
    city TEXT,
    customer_segment TEXT,
    usage_pattern TEXT,
    signup_date TEXT,
    created_at TEXT
);

-- 2. Offers
CREATE TABLE offers (
    offer_id TEXT PRIMARY KEY,
    offer_name TEXT,
    discount_percentage INTEGER,
    offer_cost REAL,
    minimum_margin REAL,
    status TEXT
);

-- 3. Subscriptions
CREATE TABLE subscriptions (
    subscription_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    product_id TEXT,
    plan_type TEXT,
    monthly_fee REAL,
    start_date TEXT,
    end_date TEXT,
    status TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 4. Usage snapshots
CREATE TABLE usage_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    subscription_id TEXT NOT NULL,
    snapshot_date TEXT,
    usage_minutes INTEGER,
    login_count INTEGER,
    data_consumption_gb REAL,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id)
);

-- 5. Billing events
CREATE TABLE billing_events (
    billing_event_id TEXT PRIMARY KEY,
    subscription_id TEXT NOT NULL,
    invoice_date TEXT,
    due_date TEXT,
    amount REAL,
    paid_amount REAL,
    payment_status TEXT,
    overdue_days INTEGER,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id)
);

-- 6. Support cases
CREATE TABLE support_cases (
    support_case_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    created_at TEXT,
    issue_category TEXT,
    priority TEXT,
    resolution_status TEXT,
    resolution_date TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 7. Eligibility rules
CREATE TABLE eligibility_rules (
    rule_id TEXT PRIMARY KEY,
    offer_id TEXT,
    minimum_risk_score INTEGER,
    minimum_margin INTEGER,
    allowed_segment TEXT,
    max_discount INTEGER
);

-- 8. Features
CREATE TABLE features (
    customer_id TEXT NOT NULL,
    prediction_date TEXT NOT NULL,
    usage_change_pct REAL,
    login_count_latest INTEGER,
    failed_payment_count INTEGER,
    avg_overdue_days REAL,
    support_case_count INTEGER,
    unresolved_cases INTEGER,
    plan_downgrade_signal INTEGER,
    rule_risk_score REAL,
    PRIMARY KEY (customer_id, prediction_date)
);

-- 9. Churn predictions
CREATE TABLE churn_predictions (
    customer_id TEXT NOT NULL,
    prediction_date TEXT NOT NULL,
    usage_change_pct REAL,
    login_count_latest INTEGER,
    failed_payment_count INTEGER,
    avg_overdue_days REAL,
    support_case_count INTEGER,
    unresolved_cases INTEGER,
    plan_downgrade_signal INTEGER,
    rule_risk_score REAL,
    churn_probability REAL,
    risk_category TEXT,
    PRIMARY KEY (customer_id, prediction_date)
);

-- 10. Churn outcomes
CREATE TABLE churn_outcomes (
    churn_id TEXT PRIMARY KEY,
    customer_id TEXT,
    prediction_date TEXT,
    churn_date TEXT,
    churn_type TEXT,
    churn_label INTEGER,
    prediction_horizon_days INTEGER
);

-- 11. Eligibility decisions
CREATE TABLE eligibility_decisions (
    customer_id TEXT NOT NULL,
    prediction_date TEXT NOT NULL,
    churn_probability REAL,
    risk_category TEXT,
    eligible INTEGER,
    offer_id TEXT,
    offer_name TEXT,
    offer_cost REAL,
    estimated_margin REAL,
    decision_reason TEXT,
    PRIMARY KEY (customer_id, prediction_date)
);

-- 12. Campaign contacts
CREATE TABLE campaign_contacts (
    contact_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    offer_id TEXT NOT NULL,
    experiment_group TEXT,
    contact_date TEXT,
    delivery_status TEXT,
    decision_reason TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (offer_id) REFERENCES offers(offer_id)
);

-- 13. Retention outcomes
CREATE TABLE retention_outcomes (
    retention_id TEXT PRIMARY KEY,
    contact_id TEXT NOT NULL,
    observation_date TEXT,
    retained_status INTEGER,
    realized_revenue REAL,
    offer_cost REAL,
    incremental_margin REAL,
    FOREIGN KEY (contact_id) REFERENCES campaign_contacts(contact_id)
);

-- 14. Campaign results
CREATE TABLE campaign_results (
    customer_id TEXT NOT NULL,
    prediction_date TEXT NOT NULL,
    churn_probability REAL,
    risk_category TEXT,
    eligible INTEGER,
    offer_id TEXT,
    offer_name TEXT,
    offer_cost REAL,
    estimated_margin REAL,
    decision_reason TEXT,
    experiment_group TEXT,
    contact_id TEXT,
    delivery_status TEXT,
    contact_date TEXT,
    retained_status INTEGER,
    retention_id TEXT,
    observation_date TEXT,
    realized_revenue REAL,
    actual_offer_cost REAL,
    incremental_margin REAL,
    PRIMARY KEY (customer_id, prediction_date)
);

-- 15. Ground truth
CREATE TABLE ground_truth (
    issue_id TEXT PRIMARY KEY,
    entity TEXT,
    entity_id TEXT,
    issue_type TEXT,
    ground_truth TEXT
);

-- 16. Validation issues
CREATE TABLE validation_issues (
    issue_type TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    detail TEXT NOT NULL,
    PRIMARY KEY (issue_type, entity, entity_id, detail)
);
