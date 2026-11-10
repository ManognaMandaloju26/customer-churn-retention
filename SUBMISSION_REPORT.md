\# SUBMISSION VERIFICATION REPORT



\## Project Title

\*\*Customer Churn Prediction \& Retention Offer Optimization\*\*



\*\*Hackathon:\*\* YottaFlex.ai Associate AI Forward Deployed Engineer Hackathon



\## 1. Package Contents



This submission package contains:



\- Python source code and project modules.

\- Interactive Streamlit dashboard.

\- Configuration files.

\- Project documentation and data dictionary.

\- Automated test suite.

\- Trained baseline machine learning model.

\- Generated synthetic CSV datasets.

\- SQLite database.

\- Portable SQL seed export.

\- SQL database schema with primary-key and foreign-key definitions.

\- Reproducibility and validation reports.



\## 2. Dataset Verification



The project contains the following generated datasets:



| Dataset | Records |

|---|---:|

| Customers | 20,000 |

| Subscriptions | 20,000 |

| Usage Snapshots | 360,000 |

| Billing Events | 360,000 |

| Support Cases | 18,848 |

| Campaign Contacts | 20,002 |

| Churn Outcomes | 20,000 |

| Retention Outcomes | 17,334 |

| Feature Rows | 20,000 |

| Ground-truth anomaly records | 4 |

| Validation issue records | 4 |



\*\*Observation period:\*\* 18 monthly periods, January 2025 through June 2026.



Campaign contacts include deliberately injected anomaly records for testing data-quality validation.



\## 3. Validation and Testing Status



\*\*Automated test command:\*\*



```powershell

python -m pytest -q

```



\*\*Latest test result:\*\*



```text

5 passed in 2.23s

```



Additional verification:



\- All four labelled anomaly categories are present in `validation\_issues.csv` and `ground\_truth.csv`.

\- Full-scale generated datasets are included in the `data/` directory.

\- The SQL schema successfully creates all 16 database tables.

\- Seven tested foreign-key relationships returned zero orphan records.

\- The reproducibility report compares two deterministic 200-customer runs.

\- The temporary schema test database returned no foreign-key violations.

\- Primary-key candidate checks found no duplicate values for the tested single-column and composite keys.



The schema was tested separately using a temporary database. The generated SQLite database should not be described as enforcing all schema constraints unless the schema has been applied to that database.



\## 4. Baseline Model Evaluation



The included baseline Random Forest evaluation reports the following metrics:



| Metric | Result |

|---|---:|

| Accuracy | 0.6258 |

| Precision | 0.2462 |

| Recall | 0.3979 |

| F1 Score | 0.3042 |

| ROC-AUC | 0.5597 |

| Test Rows | 5,000 |



These are modest baseline results.



The model should be described as a prototype trained and evaluated on synthetic data. Its results demonstrate the initial machine-learning workflow and provide a baseline for further experimentation. They should not be interpreted as evidence of production-level predictive performance or real-world customer churn accuracy.



\## 5. Campaign and Retention Evaluation



The campaign evaluation uses the generated campaign contacts and retention outcomes as the source of campaign assignment and outcome information.



| Metric | Result |

|---|---:|

| Treatment retention rate | 87.32% |

| Control retention rate | 82.43% |

| Incremental retention lift | 4.89 percentage points |

| Treatment records used | 8,659 |

| Control records used | 8,675 |

| Offer cost | ₹413,485 |

| Estimated incremental retained customers | 423.19 |

| Estimated incremental margin | ₹12,322,350.20 |

| Estimated incremental profit | -₹27,627.16 |

| Estimated ROI | -6.68% |



The treatment group shows a higher observed retention rate than the control group. However, the estimated incremental profit and ROI are negative under the current cost and margin assumptions.



These are synthetic campaign results and should not be treated as proof of causal impact or real-world financial performance. Further experimentation and business validation would be required before using these estimates for operational decisions.



\## 6. Campaign Data Consistency



The campaign consistency checks compared generated campaign contacts with campaign reporting results.



The latest checks reported:



\- Experiment group mismatches: 0

\- Offer ID mismatches: 0

\- Delivery status mismatches: 0



The generated package contains 20,002 campaign contact records and 17,334 retention outcome records.



There are 2,668 campaign contacts without a matching retention outcome. Of these, 2,666 are classified as not eligible and are expected to have no retention outcome because they were not assigned an offer. Two additional unmatched outcomes remain associated with injected or exceptional records.



Missing retention outcomes are not automatically treated as successful retention or churn. They are excluded from campaign retention-rate calculations where an outcome is unavailable.



\## 7. SQL Schema and Relationship Verification



The SQL schema contains definitions for 16 database tables.



Verification included:



\- Table creation in a temporary SQLite database.

\- Primary-key candidate duplicate checks.

\- Seven tested foreign-key relationships.

\- Orphan-record checks for the tested relationships.

\- SQLite foreign-key validation on the temporary schema database.



The seven tested foreign-key relationships returned zero orphan records.



Some reporting and audit fields are nullable or polymorphic. In particular, not every campaign result has a corresponding retention outcome. Therefore, the reporting data should not be represented as having a mandatory retention-outcome relationship for every campaign record.



The schema test confirms that the DDL can create the tables and that the temporary schema database has no foreign-key violations. It does not establish that every constraint is enforced by the pipeline-generated SQLite database.



\## 8. Reproducibility Verification



The reproducibility check was performed using two deterministic runs with:



\- Customer count: 200

\- Random seed: 20261022



The report compares generated row counts and SHA-256 hashes between the two runs.



The sample-scale runs produced matching results, supporting deterministic generation for the tested configuration.



\*\*Limitation:\*\* Full-scale reproducibility across two separate 20,000-customer runs has not been independently verified.



\## 9. Dashboard Verification



The project includes an interactive Streamlit dashboard with the following sections:



1\. \*\*Overview\*\* – Displays project-level metrics and summary information.

2\. \*\*Customer Churn\*\* – Supports exploration of churn-related customer information.

3\. \*\*Offer Eligibility\*\* – Displays offer eligibility information.

4\. \*\*Campaign Results\*\* – Presents treatment and control campaign results.

5\. \*\*Data Quality\*\* – Provides visibility into validation issues and injected anomalies.



The dashboard provides an interactive interface for exploring the generated datasets, model outputs, campaign results, and data-quality findings.



\## 10. Known Limitations



The following limitations are documented:



\- The datasets are synthetically generated and do not represent actual customer records.

\- Baseline model performance is modest and requires further improvement.

\- Campaign lift and financial estimates are based on synthetic experimental data and assumptions.

\- Missing retention outcomes are present for ineligible and exceptional campaign records.

\- Reproducibility was verified at a 200-customer sample scale, not through two full-scale runs.

\- The SQL schema was tested separately; complete database-level constraint enforcement in the pipeline-generated SQLite database has not been established.



These limitations are documented to ensure that the results are interpreted accurately.



\## 11. Final Verification Summary



| Verification Area | Status |

|---|---|

| Full-scale synthetic data generation | Completed |

| 18-month observation period | Completed |

| Baseline model training and evaluation | Completed |

| Campaign evaluation | Completed |

| Four labelled anomaly categories | Verified |

| Automated test suite | 5 tests passed |

| SQL schema creation | Verified |

| Seven foreign-key relationship checks | Passed |

| Sample-scale reproducibility | Verified |

| Interactive Streamlit dashboard | Included |

| Documentation and submission package | Included |



\## 12. Conclusion



The \*\*Customer Churn Prediction \& Retention Offer Optimization\*\* project delivers an end-to-end prototype covering synthetic data generation, customer churn prediction, offer eligibility, campaign evaluation, data-quality validation, SQL schema design, reproducibility checks, and interactive dashboard reporting.



The submission includes the generated datasets, source code, baseline model, database exports, schema definitions, automated tests, and supporting documentation.



The project demonstrates a complete prototype workflow while transparently documenting model performance, campaign economics, data-quality exceptions, and verification limitations.



\*\*Final Status:\*\* Submission package prepared for review.



