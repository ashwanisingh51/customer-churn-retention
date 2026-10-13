"""Leakage-aware, customer-disjoint temporal churn prediction prototype."""
import hashlib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,roc_auc_score,average_precision_score,confusion_matrix
from scripts.common import ROOT, AS_OF, read_csv, write_csv, write_json

NUMERIC=["customer_age_months","monthly_revenue","support_tickets","complaints","login_frequency",
         "monthly_usage","feature_usage_score","payment_failures","late_payments","auto_renew",
         "discount_percentage","engagement_score","recent_usage_decline"]
CATEGORICAL=["plan_type","contract_type","acquisition_channel","region","payment_method"]
FEATURES=NUMERIC+CATEGORICAL

def modeling_frame():
    s=read_csv("monthly_snapshots"); c=read_csv("customers_clean")
    p=s.merge(c[["customer_id","churn_date"]],on="customer_id",validate="many_to_one")
    p=p[p.is_active_end.eq(1) & p.snapshot_month.lt(AS_OF.to_period("M").start_time)].copy()
    p["label_month"]=p.snapshot_month+pd.offsets.MonthBegin(1)
    p["next_month_churn"]=(p.churn_date.dt.to_period("M")==p.label_month.dt.to_period("M")).astype(int)
    p["customer_bucket"]=p.customer_id.map(lambda x:int(hashlib.sha256(x.encode()).hexdigest()[:8],16)%10)
    p["split"]="unused"
    p.loc[p.customer_bucket.lt(6) & p.snapshot_month.le("2025-12-01"),"split"]="train"
    p.loc[p.customer_bucket.between(6,7) & p.snapshot_month.between("2026-02-01","2026-03-01"),"split"]="validation"
    p.loc[p.customer_bucket.ge(8) & p.snapshot_month.between("2026-05-01","2026-07-01"),"split"]="test"
    return p

def evaluate(y,prob,threshold):
    pred=(prob>=threshold).astype(int)
    return {"accuracy":accuracy_score(y,pred),"precision":precision_score(y,pred,zero_division=0),
            "recall":recall_score(y,pred,zero_division=0),"f1":f1_score(y,pred,zero_division=0),
            "roc_auc":roc_auc_score(y,prob),"pr_auc":average_precision_score(y,prob),
            "confusion_matrix":confusion_matrix(y,pred,labels=[0,1]).tolist(),"threshold":threshold}

def train_model():
    p=modeling_frame()
    train=p[p.split.eq("train")]; val=p[p.split.eq("validation")]; test=p[p.split.eq("test")]
    def transform():
        return ColumnTransformer([
            ("numeric",Pipeline([("impute",SimpleImputer(strategy="median")),("scale",StandardScaler())]),NUMERIC),
            ("categorical",Pipeline([("impute",SimpleImputer(strategy="most_frequent")),
                                     ("encode",OneHotEncoder(handle_unknown="ignore"))]),CATEGORICAL)])
    models={"logistic_regression":LogisticRegression(class_weight="balanced",max_iter=1200,random_state=42),
            "decision_tree":DecisionTreeClassifier(max_depth=5,min_samples_leaf=150,class_weight="balanced",random_state=42),
            "baseline":DummyClassifier(strategy="prior")}
    fitted={}; results={}
    for name,est in models.items():
        pipe=Pipeline([("preprocess",transform()),("model",est)])
        pipe.fit(train[FEATURES],train.next_month_churn)
        prob=pipe.predict_proba(val[FEATURES])[:,1]
        thresholds=np.linspace(.05,.85,81) if name!="baseline" else [.5]
        threshold=float(max(thresholds,key=lambda t:f1_score(val.next_month_churn,prob>=t,zero_division=0)))
        fitted[name]=pipe
        results[name]={"validation":evaluate(val.next_month_churn,prob,threshold)}
    selected=max(["logistic_regression","decision_tree"],key=lambda n:results[n]["validation"]["pr_auc"])
    for name,pipe in fitted.items():
        prob=pipe.predict_proba(test[FEATURES])[:,1]
        results[name]["test"]=evaluate(test.next_month_churn,prob,results[name]["validation"]["threshold"])
    prob=fitted[selected].predict_proba(test[FEATURES])[:,1]
    preds=test[["customer_id","snapshot_month","label_month","next_month_churn"]].copy()
    preds["predicted_probability"]=prob
    preds["predicted_churn"]=(prob>=results[selected]["validation"]["threshold"]).astype(int)
    write_csv(preds,ROOT/"outputs/model/test_predictions.csv")
    write_csv(p[["customer_id","snapshot_month","label_month","split","next_month_churn"]],ROOT/"outputs/model/split_audit.csv")
    summary={"prototype":True,"target":"Cancellation in next calendar month among active month-end customers",
             "features":FEATURES,"selection_metric":"Validation PR-AUC","threshold_selection":"Validation F1 only",
             "selected_model":selected,"models":results,
             "splits":{label:{"rows":len(df),"customers":df.customer_id.nunique(),"positive_labels":int(df.next_month_churn.sum()),
                      "feature_min":str(df.snapshot_month.min().date()),"feature_max":str(df.snapshot_month.max().date()),
                      "label_min":str(df.label_month.min().date()),"label_max":str(df.label_month.max().date())}
                       for label,df in [("train",train),("validation",val),("test",test)]},
             "limitations":["Synthetic data reflects the generator's assumptions.",
                            "Repeated customer-months are correlated; no independent-sample confidence intervals are claimed.",
                            "Balanced-class scores are not calibrated operational probabilities.",
                            "No churn date, final status, final tenure, future revenue or customer ID is a feature.",
                            "No deployment, realized impact or production readiness claimed."]}
    write_json(summary,ROOT/"outputs/model/model_metrics.json")
    lr=fitted["logistic_regression"]
    coef=pd.DataFrame({"feature":lr.named_steps["preprocess"].get_feature_names_out(),
                       "coefficient":lr.named_steps["model"].coef_[0]})
    write_csv(coef.sort_values("coefficient",ascending=False),ROOT/"outputs/model/logistic_coefficients.csv")
    print(f"Model: {selected}; test ROC-AUC {results[selected]['test']['roc_auc']:.3f}; PR-AUC {results[selected]['test']['pr_auc']:.3f}.")
    return summary

if __name__=="__main__": train_model()
