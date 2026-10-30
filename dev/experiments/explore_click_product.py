from playwright.sync_api import sync_playwright

p = sync_playwright().start()
b = p.chromium.launch(headless=True)
context = b.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
page = context.new_page()
page.goto("https://www.flipkart.com/search?q=Apple+iPhone+16", wait_until="domcontentloaded")
page.wait_for_timeout(3000)

print("Before click, pages count:", len(context.pages))
link = page.query_selector("a[href*='/apple-iphone-16-plus-black-128-gb/p/']")
if link:
    print("Clicking product link...")
    with context.expect_page() as new_page_info:
        link.click()
    new_page = new_page_info.value
    new_page.wait_for_load_state("domcontentloaded")
    print("New page opened! URL:", new_page.url)
    print("New page title:", new_page.title())
    print("Context pages count:", len(context.pages))

    # Test what elements are on the new page
    add_to_cart = new_page.query_selector("button:has-text('Add to Cart'), button:has-text('ADD TO CART')")
    buy_now = new_page.query_selector("button:has-text('Buy Now'), button:has-text('BUY NOW')")
    print("Add to cart button:", bool(add_to_cart))
    print("Buy now button:", bool(buy_now))
else:
    print("Link not found!")

b.close()
p.stop()
