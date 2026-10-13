"""Generate a dated subscription panel, then deliberately corrupt source copies.

The data-generating process is synthetic, not an estimate of a real business.
There is one subscription per customer, no reactivation, and no plan changes.
Annual contracts are normalized to monthly fees; early termination is permitted.
"""
import argparse
import numpy as np
import pandas as pd
from scripts.common import ROOT, AS_OF, FIRST_MONTH, SEED, ensure_dirs, write_csv, write_json

def generate(customers=12000, seed=SEED):
    if customers < 10000:
        raise ValueError("Generate at least 10,000 customers for this portfolio.")
    ensure_dirs()
    rng = np.random.default_rng(seed)
    months = pd.date_range(FIRST_MONTH, AS_OF, freq="MS")
    c = pd.DataFrame({"customer_id": [f"C{i:06d}" for i in range(1, customers + 1)]})
    start_idx = rng.choice(len(months), customers, p=np.linspace(0.75, 1.25, len(months)) / len(months))
    c["subscription_start_date"] = months[start_idx] + pd.to_timedelta(rng.integers(0, 20, customers), unit="D")
    c["signup_date"] = c.subscription_start_date - pd.to_timedelta(rng.integers(0, 15, customers), unit="D")
    c["plan_type"] = rng.choice(["Basic", "Standard", "Premium"], customers, p=[.42, .38, .20])
    c["contract_type"] = rng.choice(["Monthly", "Annual"], customers, p=[.72, .28])
    c["monthly_fee"] = c.plan_type.map({"Basic": 29., "Standard": 59., "Premium": 109.})
    c["payment_method"] = rng.choice(["Credit Card", "Bank Transfer", "Digital Wallet"], customers, p=[.55,.25,.20])
    c["auto_renew"] = rng.binomial(1, .73, customers)
    c["acquisition_channel"] = rng.choice(["Organic", "Paid Search", "Referral", "Social", "Partner"], customers, p=[.28,.27,.18,.17,.10])
    locations = {"New York":"Northeast", "Boston":"Northeast", "Chicago":"Midwest", "Detroit":"Midwest",
                 "Austin":"South", "Atlanta":"South", "Seattle":"West", "Denver":"West"}
    c["city"] = rng.choice(list(locations), customers)
    c["region"] = c.city.map(locations)
    c["age_group"] = rng.choice(["18-24", "25-34", "35-44", "45-54", "55+"], customers)
    c["discount_percentage"] = rng.choice([0., .05, .10, .20], customers, p=[.50,.15,.25,.10])
    c["subscription_end_date"] = pd.NaT
    engagement = np.clip(rng.normal(60, 18, customers) + c.acquisition_channel.map({"Organic":3,"Paid Search":-3,"Referral":9,"Social":-6,"Partner":4}), 5, 95).to_numpy(copy=True)
    friction = rng.beta(1.5, 5, customers)
    last_activity = c.subscription_start_date.to_numpy().copy()
    alive = np.ones(customers, dtype=bool)
    panels = []
    for mi, month in enumerate(months):
        end = month + pd.offsets.MonthEnd(0)
        idx = np.where(alive & (start_idx <= mi))[0]
        age = mi - start_idx[idx]
        engagement[idx] = np.clip(.82 * engagement[idx] + .18 * (60 - 30 * friction[idx]) + rng.normal(0, 12, len(idx)), 0, 100)
        login = np.clip(rng.poisson(np.maximum(engagement[idx] / 4, .2)), 0, 31)
        usage = np.round(np.maximum(0, engagement[idx] * 2.6 + rng.normal(0, 35, len(idx))), 2)
        feature = np.round(np.clip(engagement[idx] + rng.normal(0, 12, len(idx)), 0, 100), 2)
        tickets = rng.poisson(.30 + 3.8 * friction[idx])
        complaints = rng.binomial(np.minimum(tickets, 4), .22 + friction[idx] * .35)
        failures = rng.binomial(3, np.clip(.025 + friction[idx] * .21 + (c.loc[idx, "payment_method"].to_numpy() == "Digital Wallet") * .035, 0, .8))
        late = rng.binomial(2, np.clip(.04 + friction[idx] * .25, 0, .8))
        logit = (-4.0 + .038 * (50 - engagement[idx]) + .42 * failures + .24 * complaints
                 + .13 * tickets + .40 * (age < 3) + .35 * (1 - c.loc[idx, "auto_renew"].to_numpy())
                 - .65 * (c.loc[idx, "contract_type"].to_numpy() == "Annual") + .45 * friction[idx])
        churn = rng.random(len(idx)) < 1 / (1 + np.exp(-logit))
        first_day = c.loc[idx, "subscription_start_date"].where(age == 0, month).to_numpy()
        elapsed = ((end.to_datetime64() - first_day) / np.timedelta64(1, "D")).astype(int)
        cancellation = pd.to_datetime(first_day) + pd.to_timedelta([rng.integers(0, d + 1) for d in elapsed], unit="D")
        effective_end = pd.Series(end, index=idx)
        effective_end.loc[idx[churn]] = cancellation[churn].to_numpy()
        gaps = rng.integers(0, 8, len(idx)) + np.maximum(0, (48 - engagement[idx]) / 2).astype(int)
        candidate = effective_end.to_numpy() - pd.to_timedelta(gaps, unit="D").to_numpy()
        last_activity[idx] = np.maximum(last_activity[idx], np.maximum(first_day, candidate))
        fee = np.round(c.loc[idx, "monthly_fee"].to_numpy() * (1-c.loc[idx, "discount_percentage"].to_numpy()), 2)
        active_days = ((effective_end.to_numpy() - first_day) / np.timedelta64(1, "D")).astype(int) + 1
        due = (age > 0) & ((c.loc[idx, "contract_type"].to_numpy() == "Monthly") | (age % 12 == 0))
        p = c.loc[idx, ["customer_id", "plan_type", "contract_type", "acquisition_channel", "region", "payment_method", "auto_renew", "monthly_fee", "discount_percentage"]].copy()
        p["snapshot_month"] = month
        p["customer_age_months"] = age
        p["is_active_start"] = (age > 0).astype(int)
        p["new_customer"] = (age == 0).astype(int)
        p["churn_event"] = churn.astype(int)
        p["is_active_end"] = (~churn).astype(int)
        p["opening_customer_churn"] = (churn & (age > 0)).astype(int)
        p["new_customer_churn"] = (churn & (age == 0)).astype(int)
        p["renewal_due"] = due.astype(int)
        p["renewal_success"] = (due & ~churn).astype(int)
        p["monthly_revenue"] = fee
        p["start_mrr"] = fee * (age > 0)
        p["new_mrr"] = fee * (age == 0)
        p["churned_mrr"] = fee * churn
        p["end_mrr"] = fee * ~churn
        p["recognized_revenue"] = np.round(fee * active_days / end.day, 2)
        p["active_days"] = active_days
        p["support_tickets"] = tickets
        p["complaints"] = complaints
        p["login_frequency"] = login
        p["monthly_usage"] = usage
        p["feature_usage_score"] = feature
        p["payment_failures"] = failures
        p["late_payments"] = late
        p["last_activity_date"] = last_activity[idx]
        panels.append(p)
        c.loc[idx[churn], "subscription_end_date"] = cancellation[churn].to_numpy()
        alive[idx[churn]] = False
    s = pd.concat(panels, ignore_index=True).sort_values(["customer_id", "snapshot_month"])
    latest = s.groupby("customer_id", sort=False).tail(1).set_index("customer_id")
    for col in ["support_tickets", "complaints", "login_frequency", "monthly_usage", "feature_usage_score", "payment_failures", "late_payments", "last_activity_date"]:
        c[col] = c.customer_id.map(latest[col])
    c["churn_date"] = c.subscription_end_date
    c["churn_flag"] = c.subscription_end_date.notna().astype(int)
    c["customer_status"] = np.where(c.churn_flag.eq(1), "Cancelled", "Active")
    c["tenure_months"] = ((c.subscription_end_date.fillna(AS_OF) - c.subscription_start_date).dt.days / 30.4375).round(4)
    # Disjoint corruption groups make the cleaning audit independently countable.
    ids = rng.permutation(customers)
    groups = {name: ids[i*30:(i+1)*30] for i, name in enumerate([
        "missing_payment", "missing_region", "plan_alias", "negative_fee", "invalid_tenure",
        "early_churn_date", "impossible_start", "status_mismatch", "invalid_discount"])}
    c.loc[groups["missing_payment"], "payment_method"] = None
    c.loc[groups["missing_region"], "region"] = None
    c.loc[groups["plan_alias"], "plan_type"] = c.loc[groups["plan_alias"], "plan_type"].str.lower().map(lambda x: f"  {x} plan  ")
    c.loc[groups["negative_fee"], "monthly_fee"] = -59.
    c.loc[groups["invalid_tenure"], "tenure_months"] = -12.
    c.loc[groups["early_churn_date"], "churn_date"] = c.loc[groups["early_churn_date"], "signup_date"] - pd.Timedelta(days=10)
    c.loc[groups["impossible_start"], "subscription_start_date"] = AS_OF + pd.Timedelta(days=45)
    c.loc[groups["status_mismatch"], "churn_flag"] = 1-c.loc[groups["status_mismatch"], "churn_flag"]
    c.loc[groups["status_mismatch"], "customer_status"] = "Inconsistent"
    c.loc[groups["invalid_discount"], "discount_percentage"] = 1.5
    raw = pd.concat([c, c.iloc[ids[-120:]].copy()], ignore_index=True)
    raw_s = pd.concat([s, s.iloc[:50].copy()], ignore_index=True)
    write_csv(raw, ROOT / "data/raw/customers.csv")
    write_csv(raw_s, ROOT / "data/raw/monthly_snapshots.csv")
    write_json({"seed":seed,"customers_generated":customers,"as_of_date":AS_OF.date().isoformat(),
                "first_month":FIRST_MONTH.date().isoformat(),"months":len(months),"currency":"USD",
                "source":"Synthetic; generated locally", "injected_issues":{k:len(v) for k,v in groups.items()},
                "duplicate_customers":120,"duplicate_snapshots":50,
                "raw_customer_rows":len(raw),"raw_snapshot_rows":len(raw_s)}, ROOT / "data/raw/generation_metadata.json")
    print(f"Generated {customers:,} customers and {len(s):,} customer-month records.")

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--customers",type=int,default=12000)
    parser.add_argument("--seed",type=int,default=SEED)
    args=parser.parse_args()
    generate(args.customers,args.seed)
