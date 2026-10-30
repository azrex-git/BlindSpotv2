import sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

p = sync_playwright().start()
b = p.chromium.launch(headless=True)
context = b.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
page = context.new_page()
page.goto("https://www.flipkart.com/apple-iphone-16-plus-black-128-gb/p/itm1abbae671f9ef", wait_until="domcontentloaded")
page.wait_for_timeout(3000)

for btn in page.query_selector_all("button, [role='button'], a"):
    txt = (btn.inner_text() or "").strip()
    if any(k in txt.lower() for k in ("buy now", "buy at", "add to cart", "cart")):
        html = btn.evaluate("el => el.outerHTML")
        print("BTN:", repr(txt[:50]), "-->", html[:120])

b.close()
p.stop()
