"""Train and evaluate a leakage-aware churn prediction model."""
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import joblib

FEATURES = ["usage_change_pct","login_count_latest","failed_payment_count",
            "avg_overdue_days","support_case_count","unresolved_cases",
            "plan_downgrade_signal","rule_risk_score"]

def train_model(data_dir="data", model_path="models/churn_model.joblib"):
    p = Path(data_dir)
    x = pd.read_csv(p/"features.csv")
    y = pd.read_csv(p/"churn_outcomes.csv")[["customer_id","churn_label"]]
    df = x.merge(y,on="customer_id",validate="one_to_one")
    X, target = df[FEATURES], df["churn_label"]
    if target.nunique() < 2:
        raise ValueError("Training requires both churn and non-churn examples.")
    stratify = target if target.value_counts().min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X,target,test_size=.25,random_state=42,stratify=stratify)
    model = Pipeline([
        ("imputer",SimpleImputer(strategy="median")),
        ("classifier",RandomForestClassifier(n_estimators=160,max_depth=7,
                    min_samples_leaf=5,class_weight="balanced",random_state=42))
    ])
    model.fit(X_train,y_train)
    prob = model.predict_proba(X_test)[:,1]
    pred = (prob >= .5).astype(int)
    metrics = {
        "accuracy":float(accuracy_score(y_test,pred)),
        "precision":float(precision_score(y_test,pred,zero_division=0)),
        "recall":float(recall_score(y_test,pred,zero_division=0)),
        "f1":float(f1_score(y_test,pred,zero_division=0)),
        "roc_auc":float(roc_auc_score(y_test,prob)) if y_test.nunique()>1 else None,
        "test_rows":int(len(y_test))
    }
    Path(model_path).parent.mkdir(parents=True,exist_ok=True)
    joblib.dump({"model":model,"features":FEATURES},model_path)
    # Generate all-customer predictions using only pre-prediction features.
    x["churn_probability"] = model.predict_proba(x[FEATURES])[:,1]
    x["risk_category"] = pd.cut(x.churn_probability,[-.001,.30,.60,1.0],labels=["Low","Medium","High"]).astype(str)
    x.to_csv(p/"churn_predictions.csv",index=False)
    return metrics, x

if __name__ == "__main__":
    metrics, _ = train_model()
    print(metrics)
