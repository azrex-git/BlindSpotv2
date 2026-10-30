from playwright.sync_api import sync_playwright

p = sync_playwright().start()
b = p.chromium.launch(headless=True)
context = b.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
page = context.new_page()
page.goto("https://www.flipkart.com/search?q=Apple+iPhone+16", wait_until="domcontentloaded")
page.wait_for_timeout(3000)

clean_href = "/apple-iphone-16-plus-black-128-gb/p/itm1abbae671f9ef"
locator = page.locator(f"a[href*='{clean_href}']").first
print("Locator exists:", locator.count())
with context.expect_page() as new_page_info:
    locator.click()
new_page = new_page_info.value
new_page.wait_for_load_state("domcontentloaded")
print("New page URL:", new_page.url)
print("New page Title:", new_page.title())

b.close()
p.stop()
