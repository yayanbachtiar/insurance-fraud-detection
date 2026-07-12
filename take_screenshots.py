"""Take screenshots of the Streamlit fraud dashboard for GitHub/portfolio."""
from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:8501"
OUTPUT_DIR = "screenshots"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 900})

    # Full dashboard
    page.goto(BASE_URL)
    time.sleep(4)
    page.screenshot(path=f"{OUTPUT_DIR}/dashboard-full.png", full_page=True)
    print("✅ screenshots/dashboard-full.png")

    # Expand validation section
    page.click("text=📊 Validasi Rule")
    time.sleep(1)
    page.screenshot(path=f"{OUTPUT_DIR}/validation-section.png", full_page=True)
    print("✅ screenshots/validation-section.png")

    browser.close()
    print("\nAll screenshots saved to screenshots/")
