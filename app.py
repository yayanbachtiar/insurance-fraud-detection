"""
Health Insurance Claims - Fraud Detection Dashboard (Learning POC)
Jalankan: streamlit run app.py
"""

import streamlit as st
import pandas as pd
# pyrefly: ignore [missing-import]
import plotly.express as px
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "analysis"))
# pyrefly: ignore [missing-import]
from fraud_rules import run_all_rules

st.set_page_config(page_title="Claims Fraud Detection POC", layout="wide")

st.title("🔍 Health Insurance Claims Fraud Detection")
st.caption("Learning POC — rule-based detection pakai Z-score & IQR. Data sintetis, bukan data riil perusahaan.")


@st.cache_data
def load_data():
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), "data", "claims.csv"))
    df = run_all_rules(df)
    return df


df = load_data()

# ============ SIDEBAR FILTERS ============
st.sidebar.header("Filter")
employer_filter = st.sidebar.multiselect("Employer", sorted(df["employer_id"].unique()))
only_flagged = st.sidebar.checkbox("Tampilkan yang ter-flag saja", value=False)

filtered = df.copy()
if employer_filter:
    filtered = filtered[filtered["employer_id"].isin(employer_filter)]
if only_flagged:
    filtered = filtered[filtered["is_flagged"]]

# ============ TOP METRICS ============
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Klaim", f"{len(filtered):,}")
col2.metric("Total Nilai Klaim", f"Rp {filtered['claim_amount'].sum():,.0f}")
flagged_count = filtered["is_flagged"].sum()
col3.metric("Ter-flag (Suspicious)", f"{flagged_count:,}", f"{flagged_count/len(filtered)*100:.1f}%" if len(filtered) else "0%")
col4.metric("Nilai Klaim Ter-flag", f"Rp {filtered.loc[filtered['is_flagged'], 'claim_amount'].sum():,.0f}")

st.divider()

# ============ CHARTS ============
c1, c2 = st.columns(2)

with c1:
    st.subheader("Distribusi Klaim per Kategori Diagnosis")
    diag_summary = filtered.groupby("diagnosis_category").agg(
        total_amount=("claim_amount", "sum"),
        flagged=("is_flagged", "sum")
    ).reset_index().sort_values("total_amount", ascending=False)
    fig = px.bar(diag_summary, x="diagnosis_category", y="total_amount",
                 color="flagged", color_continuous_scale="Reds",
                 labels={"total_amount": "Total Nilai Klaim (Rp)", "diagnosis_category": "Kategori"})
    st.plotly_chart(fig, width='stretch')

with c2:
    st.subheader("Top 10 Provider — Rata-rata Biaya Klaim (Z-score)")
    provider_z = filtered.drop_duplicates("provider_id")[["provider_id", "provider_z_score"]].dropna()
    provider_z = provider_z.sort_values("provider_z_score", ascending=False).head(10)
    fig2 = px.bar(provider_z, x="provider_id", y="provider_z_score",
                  color="provider_z_score", color_continuous_scale="Reds",
                  labels={"provider_z_score": "Z-score"})
    fig2.add_hline(y=2.5, line_dash="dash", line_color="red",
                   annotation_text="Threshold flag (z=2.5)")
    st.plotly_chart(fig2, width='stretch')

st.divider()

# ============ IQR BOXPLOT ============
st.subheader("Visualisasi Outlier Harga (Metode IQR)")
st.caption("Boxplot di bawah ini menunjukkan sebaran harga per kategori diagnosis. Titik-titik yang terpisah (warna merah) adalah klaim yang harganya melewati batas wajar IQR (terlalu mahal atau terlalu murah).")

fig_iqr = px.box(
    filtered, 
    x="claim_amount", 
    y="diagnosis_category", 
    color="flagged_amount",
    color_discrete_map={True: "red", False: "blue"},
    labels={"claim_amount": "Nominal Klaim (Rp)", "diagnosis_category": "Kategori", "flagged_amount": "Ter-flag IQR?"},
    orientation="h"
)
st.plotly_chart(fig_iqr, width='stretch')

st.divider()

# ============ FLAGGED CLAIMS TABLE ============
st.subheader("📋 Daftar Klaim Ter-flag")
flagged_df = filtered[filtered["is_flagged"]][[
    "claim_id", "patient_id", "provider_id", "employer_id",
    "diagnosis_category", "claim_amount", "visit_date", "flag_reasons"
]].sort_values("claim_amount", ascending=False)

st.dataframe(
    flagged_df.style.format({"claim_amount": "Rp {:,.0f}"}),
    width='stretch',
    height=400
)

st.divider()

# ============ MODEL VALIDATION (karena kita punya ground truth sintetis) ============
with st.expander("📊 Validasi Rule (dibanding ground truth sintetis)"):
    st.write(
        "Karena data ini sintetis, kita tahu klaim mana yang sengaja dibuat 'fraud' "
        "(`is_injected_fraud`). Ini dipakai untuk mengukur seberapa bagus rule kita — "
        "di dunia nyata kita nggak akan punya ground truth ini, makanya validasi biasanya "
        "dilakukan lewat audit manual sample."
    )
    tp = ((df["is_flagged"]) & (df["is_injected_fraud"])).sum()
    fp = ((df["is_flagged"]) & (~df["is_injected_fraud"])).sum()
    fn = ((~df["is_flagged"]) & (df["is_injected_fraud"])).sum()
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0

    vc1, vc2, vc3, vc4 = st.columns(4)
    vc1.metric("True Positive", tp)
    vc2.metric("False Positive", fp)
    vc3.metric("Precision", f"{precision:.1%}")
    vc4.metric("Recall", f"{recall:.1%}")

st.caption("Dibuat sebagai proyek belajar aktuaria & fraud analytics — Gamya.tech")
