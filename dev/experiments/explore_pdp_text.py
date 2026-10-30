import sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

p = sync_playwright().start()
b = p.chromium.launch(headless=True)
context = b.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
page = context.new_page()
page.goto("https://www.flipkart.com/apple-iphone-16-plus-black-128-gb/p/itm1abbae671f9ef", wait_until="domcontentloaded")
page.wait_for_timeout(3000)

body_text = page.inner_text("body")
lines = [l.strip() for l in body_text.splitlines() if l.strip()]
print(f"Total lines: {len(lines)}")
for l in lines:
    if any(w in l.lower() for w in ("cart", "buy", "out of stock", "unavailable", "₹", "rs")):
        print(" ->", l[:80])

b.close()
p.stop()
