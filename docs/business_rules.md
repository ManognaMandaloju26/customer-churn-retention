# \# Business Rules

# 

# 1\. Churn is defined as a subscription cancellation within 90 days after the prediction date.

# 2\. The prediction date is the end of month 18. Historical features use usage, billing and support data from the 18-month observation period only.

# 3\. No information occurring after the prediction date is used as a model input.

# 4\. Churn labels are derived from generated cancellation events within the 90-day prediction horizon.

# 5\. Churn probability is produced by a Random Forest model.

# 6\. Offer eligibility requires an appropriate risk score, active subscription, minimum estimated contribution margin, matching customer segment and discount limit.

# 7\. Eligible customers are randomly assigned to treatment or control groups.

# 8\. Only treatment customers receive offers. Control customers are withheld from offers.

# 9\. Retention outcomes are simulated using baseline churn risk and offer-response behavior.

# 10\. Four deliberate anomaly categories are injected and documented separately in ground\_truth.csv.

# 11\. Synthetic campaign results are illustrative and are not evidence of real-world causal impact.

