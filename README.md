Playstore Reviews Excel Scraper

A Python utility to scrape, scroll, and export Google Play Store reviews into clean, batch-based Excel files.
Built with Playwright for browser automation and Pandas/OpenPyXL for structured data handling.

Unlike most scrapers that dump everything into one giant sheet, this tool saves reviews in separate Excel workbooks per batch (e.g. reviews_batch1.xlsx, reviews_batch2.xlsx, …). This keeps datasets modular, lightweight, and easier to share or analyze.

Features

🚀 Automated navigation: opens Play Store, clicks See all reviews, and scrolls until reviews are loaded.

📂 Batch-based export: each batch is stored in its own Excel file.

⭐ Rich data fields: author, date, rating, review_text, helpful_votes.

⚙️ Fully configurable:

--max-reviews: cap the total reviews to fetch

--batch-size: number of reviews per Excel file

--pause: delay between scrolls

--headless: run without showing the browser

Installation

Clone this repo:

git clone https://github.com/yourusername/playstore_reviews_excel_split.git
cd playstore_reviews_excel_split


Install dependencies:

pip install playwright pandas openpyxl


Install Playwright browser binaries:

python -m playwright install

Usage

Run the script with required arguments:

python playstore_reviews_excel_split.py \
    --app in.stablemoney.app \
    --max-reviews 800 \
    --batch-size 200 \
    --out-prefix stablemoney_reviews \
    --pause 1.5 \
    --headless

Arguments
Argument	Required	Default	Description
--app	✅	–	App ID (e.g. in.stablemoney.app)
--out-prefix	❌	reviews	Prefix for Excel output files
--max-reviews	❌	1000	Total number of reviews to scrape
--batch-size	❌	200	Reviews per Excel file
--timeout	❌	60	Page load timeout (seconds)
--pause	❌	1.5	Pause between scrolls (seconds)
--headless	❌	False	Run browser in headless mode
Output

For the above example run, the script will generate:

stablemoney_reviews_batch1.xlsx
stablemoney_reviews_batch2.xlsx
...


Each Excel file contains structured rows with:

author

date

rating

review_text

helpful_votes

Example Use Cases

📝 Product teams: track user feedback in manageable chunks.

📊 Data analysts: import Excel files into BI tools or NLP models.

🔍 Market researchers: scrape competitor app reviews for insights.

Notes

Review loading on Play Store is dynamic. The script uses adaptive scrolling to maximize capture.

If no new reviews are found after repeated scrolls, it will stop gracefully.

To debug, run without --headless to see the browser in action.

License

MIT License – free to use, modify, and distribute.
