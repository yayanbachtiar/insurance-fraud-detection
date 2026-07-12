"""
Generate synthetic health insurance claims data (Employee Benefit context).
Realistic structure mirip yang biasa ada di industri asuransi kesehatan Indonesia,
lengkap dengan beberapa pola fraud yang SENGAJA disisipkan supaya bisa dideteksi
di tahap analysis (jadi kita punya "ground truth" buat validasi rule kita).

Jalankan: python data/generate_data.py
Output: data/claims.csv
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

N_EMPLOYERS = 15
N_PROVIDERS = 40
N_PATIENTS = 3000
N_CLAIMS = 12000

DIAGNOSIS_CATEGORIES = {
    # kategori: (rata-rata biaya, std dev biaya) dalam Rupiah
    "General Checkup": (500_000, 150_000),
    "Respiratory (ISPA/Flu)": (750_000, 300_000),
    "Digestive": (1_200_000, 500_000),
    "Dental": (900_000, 400_000),
    "Orthopedic": (5_000_000, 2_000_000),
    "Cardiology": (12_000_000, 5_000_000),
    "Maternity": (15_000_000, 6_000_000),
    "Diabetes Management": (2_500_000, 1_000_000),
    "Minor Surgery": (8_000_000, 3_000_000),
    "Physiotherapy": (600_000, 200_000),
}

employers = [f"EMP{str(i).zfill(3)}" for i in range(1, N_EMPLOYERS + 1)]
providers = [f"PROV{str(i).zfill(3)}" for i in range(1, N_PROVIDERS + 1)]

# beberapa provider "normal" dan beberapa yang nanti sengaja dibuat outlier
normal_providers = providers[:35]
suspicious_providers = providers[35:]  # 5 provider akan disisipi pola fraud

patients = []
for i in range(1, N_PATIENTS + 1):
    patients.append({
        "patient_id": f"PAT{str(i).zfill(5)}",
        "employer_id": random.choice(employers),
        "age": max(0, min(70, int(np.random.normal(35, 12)))),
        "gender": random.choice(["M", "F"]),
    })
patients_df = pd.DataFrame(patients)

def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

start_date = datetime(2025, 1, 1)
end_date = datetime(2026, 6, 30)

rows = []
claim_id = 1

for _ in range(N_CLAIMS):
    patient = patients_df.sample(1).iloc[0]
    diag = random.choice(list(DIAGNOSIS_CATEGORIES.keys()))
    mean_cost, std_cost = DIAGNOSIS_CATEGORIES[diag]

    # 5% chance pakai provider "suspicious" -> nanti kita inject pola aneh
    if random.random() < 0.08:
        provider = random.choice(suspicious_providers)
    else:
        provider = random.choice(normal_providers)

    visit_date = random_date(start_date, end_date)
    # delay reporting: kebanyakan cepat, sebagian lama (buat konsep IBNR)
    report_delay = int(np.random.exponential(scale=10))
    report_date = visit_date + timedelta(days=report_delay)

    amount = max(50_000, np.random.normal(mean_cost, std_cost))

    rows.append({
        "claim_id": f"CLM{str(claim_id).zfill(6)}",
        "patient_id": patient["patient_id"],
        "employer_id": patient["employer_id"],
        "provider_id": provider,
        "age": patient["age"],
        "gender": patient["gender"],
        "diagnosis_category": diag,
        "claim_amount": round(amount, -3),  # bulatkan ke ribuan
        "visit_date": visit_date.date(),
        "report_date": report_date.date(),
    })
    claim_id += 1

df = pd.DataFrame(rows)

# ============================================================
# INJECT POLA FRAUD (ground truth, buat validasi rule nanti)
# ============================================================
df["is_injected_fraud"] = False

# Pola 1: Provider outlier - suspicious providers dikasih markup biaya 3-5x
mask_suspicious_provider = df["provider_id"].isin(suspicious_providers)
markup = np.random.uniform(2.5, 4.5, mask_suspicious_provider.sum())
df.loc[mask_suspicious_provider, "claim_amount"] = (
    df.loc[mask_suspicious_provider, "claim_amount"] * markup
).round(-3)
df.loc[mask_suspicious_provider, "is_injected_fraud"] = True

# Pola 2: Amount outlier acak - beberapa klaim normal provider tapi nominal aneh
random_outlier_idx = df.sample(frac=0.015, random_state=1).index
df.loc[random_outlier_idx, "claim_amount"] = (
    df.loc[random_outlier_idx, "claim_amount"] * np.random.uniform(5, 8, len(random_outlier_idx))
).round(-3)
df.loc[random_outlier_idx, "is_injected_fraud"] = True

# Pola 3: Frequency outlier - beberapa pasien "doctor shopping"
# ambil beberapa pasien random, kasih mereka banyak klaim dalam waktu berdekatan
shopper_patients = patients_df.sample(15, random_state=2)["patient_id"].tolist()
extra_rows = []
for pid in shopper_patients:
    prow = patients_df[patients_df["patient_id"] == pid].iloc[0]
    base_date = random_date(start_date, end_date - timedelta(days=20))
    for _ in range(random.randint(6, 10)):
        diag = random.choice(list(DIAGNOSIS_CATEGORIES.keys()))
        mean_cost, std_cost = DIAGNOSIS_CATEGORIES[diag]
        visit_date = base_date + timedelta(days=random.randint(0, 15))
        extra_rows.append({
            "claim_id": f"CLM{str(claim_id).zfill(6)}",
            "patient_id": pid,
            "employer_id": prow["employer_id"],
            "provider_id": random.choice(providers),
            "age": prow["age"],
            "gender": prow["gender"],
            "diagnosis_category": diag,
            "claim_amount": round(max(50_000, np.random.normal(mean_cost, std_cost)), -3),
            "visit_date": visit_date.date(),
            "report_date": (visit_date + timedelta(days=random.randint(1, 10))).date(),
            "is_injected_fraud": True,
        })
        claim_id += 1

df = pd.concat([df, pd.DataFrame(extra_rows)], ignore_index=True)
df = df.sample(frac=1, random_state=3).reset_index(drop=True)  # shuffle

df.to_csv("data/claims.csv", index=False)
print(f"Generated {len(df)} claims -> data/claims.csv")
print(f"Injected fraud claims: {df['is_injected_fraud'].sum()} ({df['is_injected_fraud'].mean()*100:.1f}%)")
