from playwright.sync_api import sync_playwright
import time
import sys

print("Opening visible browser on desktop...")
sys.stdout.flush()

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=[
            "--start-maximized",
            "--window-size=1280,900",
            "--window-position=50,50",
            "--disable-blink-features=AutomationControlled"
        ]
    )
    context = browser.new_context(no_viewport=True)
    page = context.new_page()
    page.goto("https://www.flipkart.com", wait_until="domcontentloaded")
    print("Loaded Flipkart! Page title:", page.title())
    sys.stdout.flush()
    # Wait on page for 15 seconds so it is clearly visible on the screen
    time.sleep(15)
    browser.close()
    print("Browser closed.")

