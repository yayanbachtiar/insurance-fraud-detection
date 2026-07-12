"""
Rule-based fraud detection logic.

Konsep dasar yang dipakai:
- Z-score: seberapa jauh (dalam satuan standar deviasi) sebuah nilai dari rata-rata.
  |z| > 3 dianggap ekstrem outlier (aturan umum di statistik).
- IQR (Interquartile Range): Q3 - Q1. Nilai di luar [Q1 - 1.5*IQR, Q3 + 1.5*IQR]
  dianggap outlier. Lebih robust dibanding z-score kalau datanya skewed
  (dan biaya medis BIASANYA skewed - banyak klaim kecil, sedikit klaim gede).

Kita pakai KEDUANYA untuk 3 pola deteksi berbeda, supaya kelihatan bedanya
kapan pakai yang mana.
"""

import pandas as pd
import numpy as np


def flag_provider_outliers(df: pd.DataFrame, z_threshold: float = 2.5) -> pd.DataFrame:
    """
    Pola 1: Provider outlier.
    Bandingkan rata-rata biaya klaim per provider terhadap rata-rata seluruh provider.
    Provider yang rata-rata biayanya jauh di atas "normal" (z-score tinggi) di-flag.

    Kenapa z-score cocok di sini: kita membandingkan AGREGAT per grup (rata-rata
    provider), bukan data mentah individual, jadi distribusinya cenderung lebih
    mendekati normal (Central Limit Theorem).
    """
    provider_stats = df.groupby("provider_id")["claim_amount"].agg(["mean", "count"]).reset_index()
    provider_stats.columns = ["provider_id", "avg_claim_amount", "claim_count"]

    overall_mean = provider_stats["avg_claim_amount"].mean()
    overall_std = provider_stats["avg_claim_amount"].std()
    provider_stats["z_score"] = (provider_stats["avg_claim_amount"] - overall_mean) / overall_std

    provider_stats["flagged_provider"] = provider_stats["z_score"] > z_threshold

    df = df.merge(
        provider_stats[["provider_id", "z_score", "flagged_provider"]],
        on="provider_id", how="left"
    )
    df = df.rename(columns={"z_score": "provider_z_score"})
    return df


def flag_amount_outliers(df: pd.DataFrame, iqr_multiplier: float = 1.5) -> pd.DataFrame:
    """
    Pola 2: Amount outlier PER kategori diagnosis.
    Kenapa per kategori, bukan global: biaya "Cardiology" wajar 12 juta,
    tapi biaya "General Checkup" 12 juta itu aneh banget. Jadi threshold
    harus relatif terhadap kategori masing-masing, bukan dibandingkan
    semua klaim campur aduk.

    IQR dipilih (bukan z-score) karena lebih tahan terhadap outlier ekstrem
    yang bisa "menarik" rata-rata dan std dev jadi bias (z-score gampang
    "tertipu" data yang sudah aneh dari awal).
    """
    def compute_bounds(group):
        q1 = group["claim_amount"].quantile(0.25)
        q3 = group["claim_amount"].quantile(0.75)
        iqr = q3 - q1
        upper_bound = q3 + iqr_multiplier * iqr
        lower_bound = q1 - iqr_multiplier * iqr
        return pd.Series({"upper_bound": upper_bound, "lower_bound": lower_bound})

    bounds = df.groupby("diagnosis_category").apply(compute_bounds).reset_index()
    df = df.merge(bounds, on="diagnosis_category", how="left")
    df["flagged_amount"] = (df["claim_amount"] > df["upper_bound"]) | (df["claim_amount"] < df["lower_bound"])
    return df


def flag_frequency_outliers(df: pd.DataFrame, window_days: int = 30, min_claims: int = 4) -> pd.DataFrame:
    """
    Pola 3: Frequency outlier ("doctor shopping").
    Pasien dengan >= min_claims klaim dalam window_days hari berturut-turut
    di-flag. Ini bukan statistik z-score/IQR murni, tapi rule sederhana
    berbasis domain knowledge (masuk kategori "business rule", bentuk lain
    dari rule-based detection selain metode statistik).
    """
    df["visit_date"] = pd.to_datetime(df["visit_date"])
    flagged_patients = set()

    for patient_id, group in df.groupby("patient_id"):
        dates = group["visit_date"].sort_values().tolist()
        for i in range(len(dates) - min_claims + 1):
            window = dates[i:i + min_claims]
            if (window[-1] - window[0]).days <= window_days:
                flagged_patients.add(patient_id)
                break

    df["flagged_frequency"] = df["patient_id"].isin(flagged_patients)
    return df


def run_all_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Jalankan semua rule dan buat kolom ringkasan is_flagged + flag_reasons."""
    df = flag_provider_outliers(df)
    df = flag_amount_outliers(df)
    df = flag_frequency_outliers(df)

    def get_reasons(row):
        reasons = []
        if row["flagged_provider"]:
            reasons.append("Provider outlier (biaya rata-rata jauh di atas normal)")
        if row["flagged_amount"]:
            reasons.append("Nominal klaim jauh di luar wajar untuk kategori diagnosis")
        if row["flagged_frequency"]:
            reasons.append("Frekuensi klaim pasien mencurigakan (potential doctor shopping)")
        return "; ".join(reasons) if reasons else "-"

    df["flag_reasons"] = df.apply(get_reasons, axis=1)
    df["is_flagged"] = df["flagged_provider"] | df["flagged_amount"] | df["flagged_frequency"]

    return df
