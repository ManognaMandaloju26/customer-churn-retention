# Submission Checklist

- [ ] Run `python -m src.pipeline`
- [ ] Run `pytest -q`
- [ ] Run `streamlit run app.py`
- [ ] Check all 10 entity CSV files
- [ ] Check ground_truth.csv is separate from model features
- [ ] Verify four anomaly types appear in validation_issues.csv
- [ ] Run with 20,000 customers if machine/time permits
- [ ] Push source code and README to a public GitHub repository
- [ ] Do not commit virtual environments, secrets, or unnecessary generated bulk files
