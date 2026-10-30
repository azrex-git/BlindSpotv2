from playwright.sync_api import sync_playwright

p = sync_playwright().start()
b = p.chromium.launch(headless=True)
context = b.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
page = context.new_page()
page.goto("https://www.flipkart.com/apple-iphone-16-plus-black-128-gb/p/itm1abbae671f9ef", wait_until="domcontentloaded")
page.wait_for_timeout(3000)

buttons = page.query_selector_all("button, ul button, a")
print(f"Total buttons/links: {len(buttons)}")
for btn in buttons:
    txt = (btn.inner_text() or "").strip().replace("\n", " ")
    if any(w in txt.lower() for w in ("cart", "buy", "order", "unavailable", "stock", "pincode")):
        print(f"Tag: {btn.evaluate('el => el.tagName')} | Text: {repr(txt[:60])} | Visible: {btn.is_visible()}")

b.close()
p.stop()
