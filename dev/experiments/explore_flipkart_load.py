from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    page = context.new_page()
    response = page.goto("https://www.flipkart.com", wait_until="domcontentloaded", timeout=15000)
    print("Status:", response.status if response else "No response")
    print("Page title:", page.title())
    print("Body length:", len(page.inner_html("body")))
    page.wait_for_timeout(3000)
    print("After 3s wait - Body length:", len(page.inner_html("body")))
    print("Inputs count:", len(page.query_selector_all("input")))
    print("Links count:", len(page.query_selector_all("a")))
    browser.close()

