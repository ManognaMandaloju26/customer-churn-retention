import json
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
from src.pipeline import run_pipeline

st.set_page_config(page_title="Customer Retention Intelligence",page_icon="📊",layout="wide")
st.title("📊 Customer Churn & Retention Intelligence")
st.caption("Predict churn, enforce offer eligibility, run retention experiments and measure business impact.")

data_dir = Path("data")
required = ["customers.csv","churn_predictions.csv","eligibility_decisions.csv","campaign_results.csv","validation_issues.csv","run_summary.json"]

with st.sidebar:
    st.header("Project controls")
    n = st.selectbox("Dataset size", [1000,2000,5000,20000], index=1)
    seed = st.number_input("Random seed", value=20261022, step=1)
    if st.button("Generate / Run complete pipeline",type="primary"):
        with st.spinner("Generating data, training model and evaluating campaign..."):
            try:
                summary = run_pipeline(customers=int(n),seed=int(seed))
                st.success("Pipeline completed successfully.")
                st.json(summary)
            except Exception as e:
                st.error(f"Pipeline failed: {e}")
                st.stop()

if not all((data_dir/f).exists() for f in required):
    st.info("No generated results found. Use the sidebar button to run the complete pipeline.")
    st.markdown("### What this application does")
    st.markdown("1. Generates synthetic customer and event history.\\n2. Validates IDs, relationships and deliberate anomalies.\\n3. Predicts churn risk using a Random Forest model.\\n4. Checks offer eligibility and margin limits.\\n5. Randomizes eligible customers into treatment/control groups.\\n6. Calculates retention lift, campaign cost and ROI.")
    st.stop()

customers = pd.read_csv(data_dir/"customers.csv")
pred = pd.read_csv(data_dir/"churn_predictions.csv")
elig = pd.read_csv(data_dir/"eligibility_decisions.csv")
camp = pd.read_csv(data_dir/"campaign_results.csv")
issues = pd.read_csv(data_dir/"validation_issues.csv")
summary = json.loads((data_dir/"run_summary.json").read_text())
cm = summary["campaign_metrics"]

pages = ["Overview","Customer Churn","Offer Eligibility","Campaign Results","Data Quality"]
page = st.sidebar.radio("Navigate",pages)

if page == "Overview":
    st.subheader("Business overview")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Customers",f"{len(customers):,}")
    c2.metric("High-risk customers",f"{(pred.risk_category=='High').sum():,}")
    c3.metric("Offer eligible",f"{elig.eligible.sum():,}")
    c4.metric("Detected exceptions",f"{len(issues):,}")
    left,right = st.columns(2)
    with left:
        risk = pred.risk_category.value_counts().rename_axis("Risk").reset_index(name="Customers")
        st.plotly_chart(px.pie(risk,names="Risk",values="Customers",title="Customer churn risk distribution"),use_container_width=True)
    with right:
        if not camp.empty:
            grp = camp.groupby("experiment_group").retained_status.mean().mul(100).reset_index(name="Retention %")
            st.plotly_chart(px.bar(grp,x="experiment_group",y="Retention %",title="Treatment vs control retention"),use_container_width=True)
    st.subheader("Model evaluation")
    st.json(summary["model_metrics"])

elif page == "Customer Churn":
    st.subheader("Customer churn predictions")
    merged = customers.merge(pred,on="customer_id",how="left")
    risk_filter = st.multiselect("Risk category",["Low","Medium","High"],default=["High","Medium","Low"])
    filtered = merged[merged.risk_category.isin(risk_filter)]
    st.dataframe(filtered[["customer_id","customer_segment","city","churn_probability","risk_category","usage_change_pct","failed_payment_count","unresolved_cases"]],use_container_width=True)
    st.download_button("Download predictions",pred.to_csv(index=False),"churn_predictions.csv","text/csv")

elif page == "Offer Eligibility":
    st.subheader("Offer eligibility decisions")
    st.metric("Eligible customers",int(elig.eligible.sum()))
    st.dataframe(elig,use_container_width=True)
    st.bar_chart(elig.decision_reason.value_counts())
    st.download_button("Download decisions",elig.to_csv(index=False),"eligibility_decisions.csv","text/csv")

elif page == "Campaign Results":
    st.subheader("Retention experiment")
    a,b,c,d = st.columns(4)
    a.metric("Treatment retention",f"{cm['treatment_retention']:.1f}%")
    b.metric("Control retention",f"{cm['control_retention']:.1f}%")
    c.metric("Incremental lift",f"{cm['incremental_lift_pp']:.1f} pp")
    d.metric("Campaign offer cost",f"₹{cm['offer_cost']:,.0f}")
    st.metric("Estimated ROI",f"{cm['roi_pct']:.1f}%")
    if not camp.empty:
        st.dataframe(camp,use_container_width=True)
        st.download_button("Download campaign results",camp.to_csv(index=False),"campaign_results.csv","text/csv")
    st.caption("Synthetic experiment: results are illustrative and should not be represented as real-world causal evidence.")

elif page == "Data Quality":
    st.subheader("Data quality and exception monitoring")
    st.metric("Detected issues",len(issues))
    if not issues.empty:
        st.dataframe(issues,use_container_width=True)
        st.bar_chart(issues.issue_type.value_counts())
    gt = pd.read_csv(data_dir/"ground_truth.csv")
    st.subheader("Separate anomaly ground truth")
    st.dataframe(gt,use_container_width=True)
    st.download_button("Download validation report",issues.to_csv(index=False),"validation_issues.csv","text/csv")
