"""
Neobank Customer Churn Analysis
Portfolio Project — Ebinum
Dataset: neobank_churn_dataset.csv (1,500 customers)

Sections:
  1. Data loading & validation
  2. Churn rate overview
  3. Churn by plan tier
  4. Churn by engagement signals
  5. Churn by balance behaviour
  6. Churn by customer tenure
  7. At-risk segment identification
  8. Revenue impact estimate
"""

import pandas as pd
import numpy as np

# ── 1. Load & validate ────────────────────────────────────────────────────────

df = pd.read_csv("neobank_churn_dataset.csv")

print("=" * 60)
print("NEOBANK CHURN ANALYSIS")
print("=" * 60)
print(f"\nDataset: {df.shape[0]:,} customers | {df.shape[1]} features")
print(f"Missing values: {df.isnull().sum().sum()}")
print(f"\nFeature summary:")
print(df.describe(include="all").T[["count", "unique", "mean", "min", "max"]].to_string())


# ── 2. Churn rate overview ────────────────────────────────────────────────────

churned = df["churned"].sum()
total = len(df)
churn_rate = churned / total

print("\n" + "=" * 60)
print("1. CHURN OVERVIEW")
print("=" * 60)
print(f"  Total customers : {total:,}")
print(f"  Churned         : {churned:,}")
print(f"  Retained        : {total - churned:,}")
print(f"  Overall churn rate: {churn_rate:.1%}")


# ── 3. Churn by plan tier ─────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("2. CHURN BY PLAN TIER")
print("=" * 60)

plan_summary = (
    df.groupby("plan_tier")
    .agg(
        customers=("churned", "count"),
        churned=("churned", "sum"),
        churn_rate=("churned", "mean"),
        avg_balance=("avg_monthly_balance_cad", "mean"),
        avg_products=("num_products", "mean"),
    )
    .round({"churn_rate": 3, "avg_balance": 0, "avg_products": 2})
    .sort_values("churn_rate", ascending=False)
)
plan_summary["churn_rate_pct"] = plan_summary["churn_rate"].map("{:.1%}".format)
print(plan_summary.drop(columns="churn_rate").to_string())

insight = (
    "\n>> Free-tier users churn at "
    + plan_summary.loc["Free", "churn_rate_pct"]
    + " vs Premium at "
    + plan_summary.loc["Premium", "churn_rate_pct"]
    + ". Plan tier is the single strongest churn predictor."
)
print(insight)


# ── 4. Engagement signals ─────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("3. ENGAGEMENT SIGNALS")
print("=" * 60)

# Days since login buckets
df["login_recency"] = pd.cut(
    df["days_since_last_login"],
    bins=[0, 7, 21, 45, 120],
    labels=["Active (≤7d)", "Moderate (8-21d)", "Lapsing (22-45d)", "Dormant (45d+)"],
    right=True,
)

login_churn = (
    df.groupby("login_recency", observed=True)["churned"]
    .agg(["count", "mean"])
    .rename(columns={"count": "customers", "mean": "churn_rate"})
)
login_churn["churn_rate"] = login_churn["churn_rate"].map("{:.1%}".format)
print("\nChurn by login recency:")
print(login_churn.to_string())

# Transaction activity
df["txn_segment"] = pd.cut(
    df["monthly_txn_count"],
    bins=[0, 4, 12, 25, 100],
    labels=["Very Low (<5)", "Low (5-12)", "Moderate (13-25)", "High (25+)"],
    right=True,
)
txn_churn = (
    df.groupby("txn_segment", observed=True)["churned"]
    .agg(["count", "mean"])
    .rename(columns={"count": "customers", "mean": "churn_rate"})
)
txn_churn["churn_rate"] = txn_churn["churn_rate"].map("{:.1%}".format)
print("\nChurn by monthly transaction volume:")
print(txn_churn.to_string())

print(
    "\n>> Dormant customers (45+ days since login) are the highest-risk "
    "engagement segment. Low transaction users (<5/month) show elevated churn."
)


# ── 5. Balance behaviour ──────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("4. BALANCE BEHAVIOUR")
print("=" * 60)

balance_churn = (
    df.groupby("balance_trend")
    .agg(
        customers=("churned", "count"),
        churn_rate=("churned", "mean"),
        avg_balance=("avg_monthly_balance_cad", "mean"),
    )
    .round({"churn_rate": 3, "avg_balance": 0})
    .sort_values("churn_rate", ascending=False)
)
balance_churn["churn_rate"] = balance_churn["churn_rate"].map("{:.1%}".format)
print(balance_churn.to_string())
print(
    "\n>> Customers with a declining balance trend are the highest-risk group "
    "by balance behaviour — a strong leading indicator of intent to leave."
)


# ── 6. Tenure cohort analysis ─────────────────────────────────────────────────

print("\n" + "=" * 60)
print("5. TENURE COHORT ANALYSIS")
print("=" * 60)

df["tenure_bucket"] = pd.cut(
    df["tenure_months"],
    bins=[0, 6, 18, 36, 72],
    labels=["<6 months", "6-18 months", "18-36 months", "36+ months"],
)
tenure_churn = (
    df.groupby("tenure_bucket", observed=True)
    .agg(
        customers=("churned", "count"),
        churn_rate=("churned", "mean"),
        avg_products=("num_products", "mean"),
    )
    .round({"churn_rate": 3, "avg_products": 2})
)
tenure_churn["churn_rate"] = tenure_churn["churn_rate"].map("{:.1%}".format)
print(tenure_churn.to_string())
print(
    "\n>> Early-tenure customers (<6 months) are most at risk — "
    "the onboarding window is critical for long-term retention."
)


# ── 7. At-risk segment ────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("6. HIGH-RISK SEGMENT IDENTIFICATION")
print("=" * 60)

at_risk = df[
    (df["plan_tier"] == "Free")
    & (df["balance_trend"] == "declining")
    & (df["days_since_last_login"] > 21)
    & (df["num_products"] == 1)
].copy()

print(f"\nHigh-risk segment definition:")
print(f"  • Free plan")
print(f"  • Declining balance trend")
print(f"  • No login in 21+ days")
print(f"  • Single product (no cross-sell)")
print(f"\nSegment size  : {len(at_risk):,} customers ({len(at_risk)/total:.1%} of base)")
print(f"Churn rate    : {at_risk['churned'].mean():.1%}")
print(f"Avg balance   : ${at_risk['avg_monthly_balance_cad'].mean():,.0f} CAD")
print(f"Avg tenure    : {at_risk['tenure_months'].mean():.0f} months")
print(
    "\n>> This segment churns at significantly elevated rates. "
    "A targeted re-engagement campaign (e.g., upgrade incentive, product education) "
    "could materially move overall retention."
)


# ── 8. Revenue impact ─────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("7. REVENUE IMPACT ESTIMATE")
print("=" * 60)

# Monthly recurring revenue lost to churn (paid plans only)
churned_df = df[df["churned"] == 1]
mrr_lost = churned_df["monthly_fee_cad"].sum()
retained_mrr = df[df["churned"] == 0]["monthly_fee_cad"].sum()

print(f"\nMRR lost to churn (paid plans) : ${mrr_lost:>10,.2f} CAD/month")
print(f"MRR retained                   : ${retained_mrr:>10,.2f} CAD/month")

# Simple LTV estimate: avg monthly fee / churn rate
avg_fee_paid = df[df["plan_tier"] != "Free"]["monthly_fee_cad"].mean()
estimated_ltv = avg_fee_paid / churn_rate
print(f"\nEst. avg LTV (paid customers)  : ${estimated_ltv:>10,.2f} CAD")
print(
    f"\n>> Reducing churn by 5 percentage points would retain "
    f"~{int(total * 0.05):,} additional customers, "
    f"recovering an estimated ${avg_fee_paid * int(total * 0.05):,.0f} CAD/month in MRR."
)

print("\n" + "=" * 60)
print("END OF ANALYSIS")
print("=" * 60)
