# playstore_reviews_excel_split.py
# Usage:
#   pip install playwright pandas openpyxl
#   python -m playwright install
#   python playstore_reviews_excel_split.py --app in.stablemoney.app --max-reviews 800 --batch-size 200 --out-prefix stablemoney_reviews --pause 1.5 --headless

import re
import time
import argparse
from pathlib import Path
import pandas as pd
from playwright.sync_api import sync_playwright

# ---------- helpers ----------
def parse_int(text: str):
    if not text:
        return None
    m = re.search(r"\d+", text.replace(",", ""))
    return int(m.group(0)) if m else None

def parse_rating_from_aria(aria: str):
    if not aria:
        return None
    m = re.search(r"Rated\s+(\d+(?:\.\d+)?)\s+stars", aria, re.I)
    return int(float(m.group(1))) if m else None

def safe_text(locator):
    try:
        return locator.inner_text().strip() if locator.count() else ""
    except Exception:
        return ""

# ---------- navigation ----------
def click_see_all_reviews(page, timeout_ms=15000):
    page.locator('button span:has-text("See all reviews")').first.click(timeout=timeout_ms)

def get_reviews_list(modal):
    lst = modal.locator('div[aria-label="User reviews"]').first
    return lst if lst.count() else modal

def force_scroll_until(modal, page, target_total, pause=1.5, max_scrolls=5000, idle_limit=12):
    """Ensure at least target_total review cards exist in the dialog."""
    lst = get_reviews_list(modal)
    total_scrolls, prev_count, idle = 0, 0, 0

    while total_scrolls < max_scrolls:
        try:
            lst.evaluate("(el) => el.scrollBy(0, el.clientHeight * 0.92)")
        except Exception:
            page.keyboard.press("PageDown")

        cards = modal.locator('div.RHo1pe')
        if cards.count():
            try:
                cards.last.scroll_into_view_if_needed(timeout=1500)
            except Exception:
                pass

        time.sleep(pause)
        total_scrolls += 1

        now = cards.count()
        print(f"[Scroll {total_scrolls}] Reviews in DOM: {now}")

        if now >= target_total:
            break

        if now == prev_count:
            idle += 1
        else:
            idle, prev_count = 0, now

        if idle >= idle_limit:
            print("[Info] No growth; proceeding with what we have.")
            break

# ---------- harvesting ----------
def harvest_range(modal, start_index, limit):
    """Extract review rows from cards[start_index : start_index + limit]."""
    rows = []
    cards = modal.locator('div.RHo1pe')
    end = min(cards.count(), start_index + limit)
    for i in range(start_index, end):
        card = cards.nth(i)

        author = safe_text(card.locator('.X5PpBb'))
        date_text = safe_text(card.locator('.bp9Aid'))

        rating = None
        rn = card.locator('[aria-label*="Rated"]').first
        if rn.count():
            rating = parse_rating_from_aria(rn.get_attribute("aria-label"))

        review_text = safe_text(card.locator('.h3YV2d'))
        helpful_votes = parse_int(safe_text(card.locator('.AJTPZc')))

        rows.append({
            "author": author,
            "date": date_text,
            "rating": rating,
            "review_text": review_text,
            "helpful_votes": helpful_votes,
        })
    return rows

# ---------- saving ----------
def save_batch_to_new_workbook(rows, out_prefix: str, batch_num: int):
    df = pd.DataFrame(rows, columns=["author","date","rating","review_text","helpful_votes"])
    xlsx_path = Path(f"{out_prefix}_batch{batch_num}.xlsx")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl", mode="w") as xw:
        df.to_excel(xw, index=False, sheet_name="reviews")
    print(f"[Saved] {len(df)} reviews -> {xlsx_path.name}")

# ---------- main ----------
def run(app_id: str, out_prefix: str, max_reviews: int, batch_size: int,
        timeout: int, pause: float, headless: bool):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(viewport={'width': 1400, 'height': 900})

        url = f"https://play.google.com/store/apps/details?id={app_id}&hl=en_IN&pli=1"
        page.goto(url, timeout=timeout * 1000)

        click_see_all_reviews(page, timeout_ms=timeout * 1000)
        time.sleep(1.0)
        modal = page.locator('div[role="dialog"]').first

        written = 0
        batch_num = 1

        while True:
            if max_reviews and written >= max_reviews:
                print(f"[Stop] Reached max_reviews={max_reviews}.")
                break

            # Ensure enough cards are present to cover the next slice
            target_total = written + batch_size
            if max_reviews:
                target_total = min(target_total, max_reviews)

            force_scroll_until(
                modal, page,
                target_total=target_total,
                pause=pause,
                max_scrolls=5000,
                idle_limit=12,
            )

            # Harvest the slice and write immediately to a brand-new workbook
            to_take = batch_size if not max_reviews else min(batch_size, max_reviews - written)
            rows = harvest_range(modal, start_index=written, limit=to_take)

            if not rows:
                print("[Stop] No new reviews harvested; exiting.")
                break

            save_batch_to_new_workbook(rows, out_prefix, batch_num)
            written += len(rows)
            batch_num += 1

        browser.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True, help="e.g. in.stablemoney.app")
    ap.add_argument("--out-prefix", default="reviews", help="Prefix for Excel files (one file per batch)")
    ap.add_argument("--max-reviews", type=int, default=1000, help="Total review cap")
    ap.add_argument("--batch-size", type=int, default=200, help="Reviews per workbook")
    ap.add_argument("--timeout", type=int, default=60, help="Page load timeout (seconds)")
    ap.add_argument("--pause", type=float, default=1.5, help="Pause between scrolls (seconds)")
    ap.add_argument("--headless", action="store_true", help="Run browser headless")
    args = ap.parse_args()

    run(
        app_id=args.app,
        out_prefix=args.out_prefix,
        max_reviews=args.max_reviews,
        batch_size=args.batch_size,
        timeout=args.timeout,
        pause=args.pause,
        headless=args.headless,
    )
