from playwright.sync_api import sync_playwright

p = sync_playwright().start()
b = p.chromium.launch(headless=True)
page = b.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
page.goto("https://www.flipkart.com/search?q=Apple+iPhone+16", wait_until="domcontentloaded")
page.wait_for_timeout(3000)

links = page.query_selector_all("a[href*='/p/']")
print(f"Found {len(links)} links with /p/")
for i, l in enumerate(links[:8]):
    text = l.inner_text().replace('\n', ' ')[:80]
    href = l.get_attribute("href") or ""
    target = l.get_attribute("target") or ""
    print(f"[{i}] target={target} | text={text} | href={href[:50]}")

b.close()
p.stop()
