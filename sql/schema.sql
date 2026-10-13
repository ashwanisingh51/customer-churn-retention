PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS channel_performance (
  "acquisition_channel" TEXT,
  "total_customers" INTEGER,
  "active_customers" INTEGER,
  "churned_customers" INTEGER,
  "active_mrr" REAL,
  "revenue_at_risk" REAL,
  "observed_revenue" REAL,
  "average_clv" REAL,
  "average_tenure" REAL,
  "churn_rate" REAL,
  "retention_rate" REAL,
  "arpu" REAL,
  PRIMARY KEY ("acquisition_channel")
);

CREATE TABLE IF NOT EXISTS churn_driver_associations (
  "driver" TEXT,
  "category" TEXT,
  "exposures" INTEGER,
  "distinct_customers" INTEGER,
  "next_month_churns" INTEGER,
  "next_month_churn_rate" REAL,
  PRIMARY KEY ("driver", "category")
);

CREATE TABLE IF NOT EXISTS cohort_retention (
  "cohort_month" TEXT,
  "cohort_age" INTEGER,
  "cohort_size" INTEGER,
  "retained_customers" REAL,
  "retention_rate" REAL,
  "is_observed" INTEGER,
  PRIMARY KEY ("cohort_month", "cohort_age")
);

CREATE TABLE IF NOT EXISTS customer_risk_scores (
  "customer_id" TEXT,
  "as_of_date" TEXT,
  "plan_type" TEXT,
  "contract_type" TEXT,
  "acquisition_channel" TEXT,
  "region" TEXT,
  "monthly_revenue" REAL,
  "tenure_months" REAL,
  "observed_clv" REAL,
  "engagement_score" REAL,
  "customer_segment" TEXT,
  "churn_flag" INTEGER,
  "active_flag" INTEGER,
  "risk_score" REAL,
  "risk_band" TEXT,
  "high_value_flag" INTEGER,
  "high_risk_flag" INTEGER,
  "active_mrr" REAL,
  "revenue_at_risk" REAL,
  "retention_priority" TEXT,
  "risk_inactivity" REAL,
  "risk_engagement" REAL,
  "risk_support" REAL,
  "risk_complaints" REAL,
  "risk_payment" REAL,
  "risk_usage" REAL,
  "risk_new" REAL,
  "risk_renewal" REAL,
  "risk_decline" REAL,
  PRIMARY KEY ("customer_id"),
  FOREIGN KEY ("customer_id") REFERENCES customers_clean(customer_id)
);

CREATE TABLE IF NOT EXISTS customer_segments (
  "customer_id" TEXT,
  "as_of_date" TEXT,
  "plan_type" TEXT,
  "contract_type" TEXT,
  "acquisition_channel" TEXT,
  "region" TEXT,
  "monthly_revenue" REAL,
  "tenure_months" REAL,
  "observed_clv" REAL,
  "engagement_score" REAL,
  "customer_segment" TEXT,
  "churn_flag" INTEGER,
  "active_flag" INTEGER,
  "risk_score" REAL,
  "risk_band" TEXT,
  "high_value_flag" INTEGER,
  "high_risk_flag" INTEGER,
  "active_mrr" REAL,
  "revenue_at_risk" REAL,
  "retention_priority" TEXT,
  PRIMARY KEY ("customer_id"),
  FOREIGN KEY ("customer_id") REFERENCES customers_clean(customer_id)
);

CREATE TABLE IF NOT EXISTS customers_clean (
  "customer_id" TEXT,
  "subscription_start_date" TEXT,
  "signup_date" TEXT,
  "plan_type" TEXT,
  "contract_type" TEXT,
  "monthly_fee" REAL,
  "payment_method" TEXT,
  "auto_renew" INTEGER,
  "acquisition_channel" TEXT,
  "city" TEXT,
  "region" TEXT,
  "age_group" TEXT,
  "discount_percentage" REAL,
  "subscription_end_date" TEXT,
  "support_tickets" INTEGER,
  "complaints" INTEGER,
  "login_frequency" INTEGER,
  "monthly_usage" REAL,
  "feature_usage_score" REAL,
  "payment_failures" INTEGER,
  "late_payments" INTEGER,
  "last_activity_date" TEXT,
  "churn_date" TEXT,
  "churn_flag" INTEGER,
  "customer_status" TEXT,
  "tenure_months" REAL,
  "engagement_score" REAL,
  "recent_usage_decline" REAL,
  "as_of_date" TEXT,
  "observation_date" TEXT,
  "customer_tenure" REAL,
  "customer_age_months" INTEGER,
  "days_since_last_activity" INTEGER,
  "monthly_revenue" REAL,
  "observed_clv" REAL,
  "support_ticket_band" TEXT,
  "usage_band" TEXT,
  "engagement_band" TEXT,
  "tenure_band" TEXT,
  "acquisition_cohort" TEXT,
  "churn_month" TEXT,
  "risk_score" REAL,
  "risk_band" TEXT,
  "high_value_flag" INTEGER,
  "active_flag" INTEGER,
  "high_risk_flag" INTEGER,
  "active_mrr" REAL,
  "revenue_at_risk" REAL,
  "customer_segment" TEXT,
  "retention_priority" TEXT,
  PRIMARY KEY ("customer_id"),
  CHECK (monthly_fee >= 0),
  CHECK (discount_percentage BETWEEN 0 AND 1),
  CHECK (active_flag + churn_flag = 1),
  CHECK (risk_score IS NULL OR risk_score BETWEEN 0 AND 100)
);

CREATE TABLE IF NOT EXISTS geography_performance (
  "region" TEXT,
  "total_customers" INTEGER,
  "active_customers" INTEGER,
  "churned_customers" INTEGER,
  "active_mrr" REAL,
  "revenue_at_risk" REAL,
  "observed_revenue" REAL,
  "average_clv" REAL,
  "average_tenure" REAL,
  "churn_rate" REAL,
  "retention_rate" REAL,
  "arpu" REAL,
  PRIMARY KEY ("region")
);

CREATE TABLE IF NOT EXISTS monthly_churn_kpis (
  "month" TEXT,
  "is_active_start" INTEGER,
  "new_customer" INTEGER,
  "churn_event" INTEGER,
  "is_active_end" INTEGER,
  "opening_customer_churn" INTEGER,
  "new_customer_churn" INTEGER,
  "renewal_due" INTEGER,
  "renewal_success" INTEGER,
  "start_mrr" REAL,
  "new_mrr" REAL,
  "churned_mrr" REAL,
  "end_mrr" REAL,
  "recognized_revenue" REAL,
  "retained_opening_customers" INTEGER,
  "churn_rate" REAL,
  "retention_rate" REAL,
  "renewal_rate" REAL,
  "net_customer_growth" INTEGER,
  "customer_growth_rate" REAL,
  "arpu" REAL,
  PRIMARY KEY ("month")
);

CREATE TABLE IF NOT EXISTS monthly_retention_kpis (
  "month" TEXT,
  "is_active_start" INTEGER,
  "retained_opening_customers" INTEGER,
  "opening_customer_churn" INTEGER,
  "retention_rate" REAL,
  "renewal_due" INTEGER,
  "renewal_success" INTEGER,
  "renewal_rate" REAL,
  PRIMARY KEY ("month")
);

CREATE TABLE IF NOT EXISTS monthly_snapshots (
  "customer_id" TEXT,
  "plan_type" TEXT,
  "contract_type" TEXT,
  "acquisition_channel" TEXT,
  "region" TEXT,
  "payment_method" TEXT,
  "auto_renew" INTEGER,
  "monthly_fee" REAL,
  "discount_percentage" REAL,
  "snapshot_month" TEXT,
  "customer_age_months" INTEGER,
  "is_active_start" INTEGER,
  "new_customer" INTEGER,
  "churn_event" INTEGER,
  "is_active_end" INTEGER,
  "opening_customer_churn" INTEGER,
  "new_customer_churn" INTEGER,
  "renewal_due" INTEGER,
  "renewal_success" INTEGER,
  "monthly_revenue" REAL,
  "start_mrr" REAL,
  "new_mrr" REAL,
  "churned_mrr" REAL,
  "end_mrr" REAL,
  "recognized_revenue" REAL,
  "active_days" INTEGER,
  "support_tickets" INTEGER,
  "complaints" INTEGER,
  "login_frequency" INTEGER,
  "monthly_usage" REAL,
  "feature_usage_score" REAL,
  "payment_failures" INTEGER,
  "late_payments" INTEGER,
  "last_activity_date" TEXT,
  "engagement_score" REAL,
  "prior_usage_mean" REAL,
  "recent_usage_decline" REAL,
  PRIMARY KEY ("customer_id", "snapshot_month"),
  FOREIGN KEY ("customer_id") REFERENCES customers_clean(customer_id)
);

CREATE TABLE IF NOT EXISTS plan_performance (
  "plan_type" TEXT,
  "total_customers" INTEGER,
  "active_customers" INTEGER,
  "churned_customers" INTEGER,
  "active_mrr" REAL,
  "revenue_at_risk" REAL,
  "observed_revenue" REAL,
  "average_clv" REAL,
  "average_tenure" REAL,
  "churn_rate" REAL,
  "retention_rate" REAL,
  "arpu" REAL,
  PRIMARY KEY ("plan_type")
);

CREATE TABLE IF NOT EXISTS retention_by_dimension (
  "dimension" TEXT,
  "category" TEXT,
  "eligible_customers" INTEGER,
  "retained_customers" INTEGER,
  "retention_rate" REAL,
  PRIMARY KEY ("dimension", "category")
);

CREATE TABLE IF NOT EXISTS revenue_churn_impact (
  "month" TEXT,
  "start_mrr" REAL,
  "new_mrr" REAL,
  "churned_mrr" REAL,
  "end_mrr" REAL,
  "recognized_revenue" REAL,
  "is_active_end" INTEGER,
  "arpu" REAL,
  PRIMARY KEY ("month")
);

CREATE TABLE IF NOT EXISTS support_usage_analysis (
  "support_ticket_band" TEXT,
  "usage_band" TEXT,
  "customers" INTEGER,
  "churned_customers" INTEGER,
  "active_mrr" REAL,
  "average_engagement" REAL,
  "revenue_at_risk" REAL,
  "churn_rate" REAL,
  PRIMARY KEY ("support_ticket_band", "usage_band")
);

CREATE INDEX IF NOT EXISTS idx_snapshot_month ON monthly_snapshots(snapshot_month);

CREATE INDEX IF NOT EXISTS idx_churn_date ON customers_clean(churn_date);
