# Health Insurance Claims Fraud Detection (Learning POC)

Proyek belajar rule-based fraud detection untuk klaim asuransi kesehatan, dibuat
sebagai eksplorasi pribadi soal actuarial science & claims analytics.

**Data sepenuhnya sintetis** — tidak ada data perusahaan/nasabah riil yang dipakai.

## Cara jalanin di lokal

```bash
pip install -r requirements.txt
python data/generate_data.py   # generate ulang dataset (opsional, sudah ada data/claims.csv)
streamlit run app.py
```

Browser akan otomatis buka `http://localhost:8501`.

## Konsep yang dipelajari

1. **Z-score** — dipakai untuk deteksi provider (rumah sakit/klinik) dengan
   rata-rata biaya klaim jauh di atas normal. Cocok karena kita membandingkan
   rata-rata per grup (mendekati distribusi normal).

2. **IQR (Interquartile Range)** — dipakai untuk deteksi nominal klaim outlier
   PER kategori diagnosis. Lebih robust dibanding z-score untuk data yang skewed
   (kebanyakan klaim kecil, sedikit yang besar — pola umum di biaya medis).

3. **Business rule / frequency check** — deteksi pola "doctor shopping"
   (pasien klaim terlalu sering dalam waktu singkat). Bukan statistik murni,
   tapi domain knowledge yang di-encode jadi rule.

4. **Precision & Recall** — cara mengukur seberapa bagus detection logic kita.
   - Precision tinggi = sedikit "salah tuduh" (false positive)
   - Recall tinggi = sedikit fraud yang lolos (false negative)
   - Di dunia nyata biasanya ada trade-off; makin ketat threshold, precision naik
     tapi recall turun (atau sebaliknya).

## Struktur

```
claims-fraud-poc/
├── data/
│   ├── generate_data.py   # generate dataset sintetis + inject pola fraud
│   └── claims.csv          # output dataset
├── analysis/
│   └── fraud_rules.py      # logic z-score, IQR, frequency rules
├── app.py                  # Streamlit dashboard
└── requirements.txt
```

## Next steps (kalau mau lanjut level up)

- Ganti rule-based dengan ML (Isolation Forest / DBSCAN) dan bandingkan hasilnya
- Coba dataset klaim publik dari Kaggle untuk validasi di data "lebih riil"
- Tambah fitur time-series (tren klaim per bulan, seasonality)
- Deploy ke Streamlit Community Cloud biar bisa dilink di LinkedIn/portofolio
