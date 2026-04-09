"""
04_tripadvisor_scraper.py
--------------------------
TripAdvisor Review Scraper — Back Bay NWR
Collects review date, title, reviewer location, star rating, and full
review text using Selenium-based browser automation.

Output: tripadvisor_backbay_raw.csv
        Columns: review_id, source, date, title, reviewer_location,
                 rating, reviews

Usage
-----
    python 04_tripadvisor_scraper.py

Requirements
------------
    pip install selenium webdriver-manager pandas tqdm

    Chrome must be installed on your machine.
    webdriver-manager downloads the matching ChromeDriver automatically.

Notes
-----
    - This script was developed for academic research purposes.
    - TripAdvisor's robots.txt and Terms of Service restrict automated
      data collection. Ensure your use complies with applicable terms
      before running. Add delays (PAUSE_SECONDS) to reduce server load.
    - The output CSV uses the same column conventions as the rest of
      this pipeline (review_id, source, reviews) for direct compatibility
      with 02_ces_classification_visualization.R and 01_bert_sentiment.py.

Citation for method:
    Mokgehle, S. L., & Fitchett, J. M. (2024). Use of TripAdvisor
    reviews as a data source for tourism and climate research.
    Current Issues in Tourism.
"""

import time
import re
import pandas as pd
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
)
from webdriver_manager.chrome import ChromeDriverManager

# ── Configuration ─────────────────────────────────────────────────────────────

# TripAdvisor URL for Back Bay NWR — update if the URL changes
TARGET_URL = (
    "https://www.tripadvisor.com/Attraction_Review-g58439-d109738-Reviews-"
    "Back_Bay_National_Wildlife_Refuge-Virginia_Beach_Virginia.html"
)

OUTPUT_PATH   = "tripadvisor_backbay_raw.csv"
SOURCE_LABEL  = "TripAdvisor"          # value written to 'source' column
MAX_PAGES     = 999                    # set lower to limit collection during testing
PAUSE_SECONDS = 3.0                    # wait between page loads (be courteous)
HEADLESS      = False                  # set True to run without opening a browser window


# ── Browser setup ─────────────────────────────────────────────────────────────

def build_driver(headless: bool = False) -> webdriver.Chrome:
    """Configure and return a Chrome WebDriver instance."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1400,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)
    return driver


# ── Cookie / consent banner dismissal ────────────────────────────────────────

def dismiss_consent(driver: webdriver.Chrome, timeout: int = 8):
    """Click the cookie consent / GDPR accept button if it appears."""
    consent_xpaths = [
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
        "'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
        "//button[@id='onetrust-accept-btn-handler']",
        "//button[contains(@class,'evidon-banner-acceptbutton')]",
    ]
    for xpath in consent_xpaths:
        try:
            btn = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            btn.click()
            print("  Consent banner dismissed.")
            time.sleep(1)
            return
        except TimeoutException:
            continue


# ── "Read more" expansion ─────────────────────────────────────────────────────

def expand_reviews(driver: webdriver.Chrome):
    """
    Click all 'Read more' / 'More' buttons on the page to reveal full
    review text before extraction.
    """
    read_more_xpaths = [
        "//button[contains(@class,'taLnk') and contains(text(),'More')]",
        "//span[contains(@class,'_T') and contains(text(),'Read more')]",
        "//button[contains(text(),'Read more')]",
        "//span[contains(text(),'more')][@role='button']",
    ]
    for xpath in read_more_xpaths:
        buttons = driver.find_elements(By.XPATH, xpath)
        for btn in buttons:
            try:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.3)
            except Exception:
                continue


# ── Per-page extraction ───────────────────────────────────────────────────────

def extract_reviews_from_page(driver: webdriver.Chrome) -> list[dict]:
    """
    Parse all review cards on the current page and return a list of dicts.
    Handles TripAdvisor's evolving HTML structure with multiple fallback
    selectors for each field.
    """
    records = []

    # Review card containers
    card_xpaths = [
        "//div[contains(@class,'_c')][@data-reviewid]",
        "//div[contains(@class,'review-container')]",
        "//div[@data-automation='reviewCard']",
    ]
    cards = []
    for xpath in card_xpaths:
        cards = driver.find_elements(By.XPATH, xpath)
        if cards:
            break

    for card in cards:
        record = {"source": SOURCE_LABEL}

        # ── Review ID (from data attribute) ──────────────────────────────────
        record["review_id"] = (
            card.get_attribute("data-reviewid") or ""
        ).strip()

        # ── Date ─────────────────────────────────────────────────────────────
        date_xpaths = [
            ".//div[contains(@class,'biGQs') and contains(@class,'_P')]"
            "/span[contains(text(),'202') or contains(text(),'201')]",
            ".//span[@class='ratingDate']",
            ".//div[contains(@class,'cRVSd')]",
        ]
        record["date"] = _first_text(card, date_xpaths)

        # ── Title ─────────────────────────────────────────────────────────────
        title_xpaths = [
            ".//a[contains(@class,'BMQDV')]//span",
            ".//span[contains(@class,'noQuotes')]",
            ".//div[contains(@class,'title')]",
        ]
        record["title"] = _first_text(card, title_xpaths)

        # ── Reviewer location ─────────────────────────────────────────────────
        loc_xpaths = [
            ".//span[contains(@class,'default') and @data-tab='HREF_LOCATION_CARD']",
            ".//div[contains(@class,'hometown')]",
            ".//span[@class='reviewerBadge']",
        ]
        record["reviewer_location"] = _first_text(card, loc_xpaths)

        # ── Star rating (bubble rating 1–5) ───────────────────────────────────
        rating_xpaths = [
            ".//svg[contains(@class,'UctUV')]",
            ".//span[contains(@class,'ui_bubble_rating')]",
        ]
        rating_raw = ""
        for xpath in rating_xpaths:
            els = card.find_elements(By.XPATH, xpath)
            if els:
                # Try aria-label first ("4 of 5 bubbles"), then class suffix
                aria = els[0].get_attribute("aria-label") or ""
                match = re.search(r"(\d+(\.\d+)?)\s*(of\s*5)?", aria)
                if match:
                    rating_raw = match.group(1)
                    break
                cls = els[0].get_attribute("class") or ""
                m2 = re.search(r"bubble_(\d+)", cls)
                if m2:
                    rating_raw = str(int(m2.group(1)) / 10)
                    break
        record["rating"] = rating_raw

        # ── Full review text ──────────────────────────────────────────────────
        text_xpaths = [
            ".//span[contains(@class,'yCeTE')]",
            ".//p[contains(@class,'partial_entry')]",
            ".//q[@class='IRsGHoPm']//span",
            ".//div[contains(@class,'prw_reviews_text_summary')]",
        ]
        record["reviews"] = _first_text(card, text_xpaths)

        # Only keep records that have at least some review text
        if record["reviews"]:
            records.append(record)

    return records


def _first_text(element, xpaths: list[str]) -> str:
    """Try each XPath in order; return the first non-empty text found."""
    for xpath in xpaths:
        try:
            el = element.find_element(By.XPATH, xpath)
            text = el.text.strip()
            if text:
                return text
        except NoSuchElementException:
            continue
    return ""


# ── Pagination ────────────────────────────────────────────────────────────────

def go_to_next_page(driver: webdriver.Chrome) -> bool:
    """
    Click the 'Next' pagination button.
    Returns True if navigation succeeded, False if no next page exists.
    """
    next_xpaths = [
        "//a[@aria-label='Next page']",
        "//a[contains(@class,'nav') and contains(text(),'Next')]",
        "//span[contains(@class,'next')]//a",
    ]
    for xpath in next_xpaths:
        try:
            btn = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(PAUSE_SECONDS)
            return True
        except (TimeoutException, ElementClickInterceptedException):
            continue
    return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  TripAdvisor Scraper — Back Bay NWR")
    print("=" * 60 + "\n")

    driver = build_driver(headless=HEADLESS)
    all_records: list[dict] = []

    try:
        print(f"Loading: {TARGET_URL}\n")
        driver.get(TARGET_URL)
        time.sleep(PAUSE_SECONDS)
        dismiss_consent(driver)

        for page_num in tqdm(range(1, MAX_PAGES + 1), desc="Pages"):
            expand_reviews(driver)
            page_records = extract_reviews_from_page(driver)
            all_records.extend(page_records)

            print(f"  Page {page_num}: {len(page_records)} reviews "
                  f"(total so far: {len(all_records)})")

            if not go_to_next_page(driver):
                print("\n  No further pages — scraping complete.")
                break

            # Polite pause between pages
            time.sleep(PAUSE_SECONDS)

    finally:
        driver.quit()

    if not all_records:
        print("\nWARNING: No reviews extracted. TripAdvisor's HTML structure "
              "may have changed. Inspect the page and update the XPath selectors.")
        return

    # ── Build dataframe ───────────────────────────────────────────────────────
    df = pd.DataFrame(all_records)

    # Assign sequential integer review_id if TripAdvisor IDs were not captured
    if df["review_id"].eq("").all():
        df["review_id"] = range(1, len(df) + 1)

    # Reorder columns to match pipeline convention
    col_order = ["review_id", "source", "date", "title",
                 "reviewer_location", "rating", "reviews"]
    df = df[[c for c in col_order if c in df.columns]]

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"\nSaved {len(df):,} reviews to: {OUTPUT_PATH}")
    print(f"Rating distribution:\n{df['rating'].value_counts().sort_index().to_string()}")
    print("\nSample record:")
    print(df.iloc[0].to_string())


if __name__ == "__main__":
    main()
