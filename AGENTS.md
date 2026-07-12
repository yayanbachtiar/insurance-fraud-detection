# Health Insurance Claims Fraud Detection (Learning POC)

Streamlit dashboard for rule-based fraud detection. Data is synthetic.

## Quick start

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
python generate_data.py        # regenerates data/claims.csv
streamlit run app.py           # opens http://localhost:8501
```

## Critical gotchas

- **`generate_data.py` lives at the repo root**, not under `data/`. The README shows `python data/generate_data.py` — that's wrong. Run `python generate_data.py` instead.
- **`generate_data.py` has a hardcoded output path** on line 148: `/home/claude/claims-fraud-poc/data/claims.csv`. This path does not exist on other machines. **Fix before running:** change it to `os.path.join(os.path.dirname(__file__), "data", "claims.csv")`.
- **No `.streamlit/config.toml` exists.** The app uses all defaults. To customize theme, server port, or other Streamlit settings, create `.streamlit/config.toml`.
- **No root `.gitignore`.** Before committing, create `.gitignore` that excludes `.venv/`, `__pycache__/`, `.DS_Store`, `.codegraph/`, `.agents/`, `.claude/`, `screenshots/`, and any skill/dotfile artifacts.
- **Not yet a git repo.** Run `git init && git add -A && git commit -m "init"` to start tracking.
- **`scikit-learn` listed in requirements.txt but unused** in the current codebase. It's a placeholder for future ML-based detection.

## Project structure

```
├── app.py                  # Streamlit entrypoint (single page)
├── generate_data.py        # Script to generate synthetic claims data + inject fraud patterns
├── take_screenshots.py     # Playwright script to capture dashboard screenshots
├── analysis/
│   └── fraud_rules.py      # Z-score, IQR, and frequency detection logic
├── data/
│   └── claims.csv          # Synthetic dataset (output of generate_data.py)
└── requirements.txt        # pandas, numpy, streamlit, plotly, scikit-learn
```

## Detection methods

- **Z-score** (provider-level): flags providers whose avg claim cost is >2.5σ above the mean of all providers.
- **IQR** (claim-level per diagnosis category): flags individual claims outside Q1-1.5×IQR / Q3+1.5×IQR bounds.
- **Frequency check** (patient-level): flags ≥4 claims in any 30-day window ("doctor shopping").

## Screenshots for publishing

Screenshots have been taken and saved to `screenshots/`:

| File | What it captures |
|---|---|
| `screenshots/dashboard-full.png` | Full page — metrics row, charts, flagged claims table |
| `screenshots/validation-section.png` | Model validation expander (precision & recall) |

To re-take screenshots (e.g. after changes), run:
```bash
.venv/bin/python take_screenshots.py
```

Requires Playwright (`uv pip install playwright` + `.venv/bin/python -m playwright install chromium`).

Target views: top metrics row, per-category bar chart, IQR boxplot, flagged claims table, and the model validation expander.

## Working with OpenCode

- Load the `developing-with-streamlit` skill for any Streamlit work (the skill is already installed in `.agents/skills/`).
- The `ui-ux-pro-max` skill is also available for UI polish.
- To run and visually verify the app in a Playwright browser session inside OpenCode, use the `agent-browser` skill.
