"""Live Interactive Demonstration of BlindSpot Auditing Flipkart.

Opens a visible Chromium browser window on your desktop and simulates
the shopping journey with clear visual pacing (slow_mo).
"""

import sys
import time

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from playwright.sync_api import sync_playwright

def run_live_demo():
    print("=" * 60)
    print("[*] BLINDSPOT: Live Interactive Demonstration on Flipkart")
    print("=" * 60)
    print("Launching Chromium in headed mode on your desktop...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=800,  # 800ms between actions for clear visual observation
            args=[
                "--start-maximized",
                "--window-position=50,50",
                "--window-size=1280,900",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        context = browser.new_context(
            viewport=None,  # Use full window dimensions
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        )
        page = context.new_page()
        page.bring_to_front()

        print("\n[Step 1] Navigating to https://www.flipkart.com...")
        page.goto("https://www.flipkart.com", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(2000)

        # Check for and dismiss login modal if present
        try:
            close_btn = page.query_selector("button:has-text('✕'), span:has-text('✕'), ._30XB9F, ._2KpZ6l._2doB4z")
            if close_btn and close_btn.is_visible():
                print("  -> Dismissing initial login takeover modal...")
                close_btn.click()
                page.wait_for_timeout(1000)
        except Exception:
            pass

        print("\n[Step 2] Locating search input and querying 'Apple iPhone 16'...")
        search_input = page.query_selector("input[name='q'], input[title*='Search'], input[placeholder*='Search']")
        if search_input:
            search_input.click()
            search_input.fill("Apple iPhone 16")
            page.wait_for_timeout(1000)
            print("  -> Submitting query and navigating to product catalog...")
            page.keyboard.press("Enter")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
        else:
            print("  -> Search input not found, navigating directly to iPhone catalog...")
            page.goto("https://www.flipkart.com/search?q=Apple+iPhone+16", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

        print("\n[Step 3] Scrolling through product listings to evaluate price clarity & badges...")
        for i in range(1, 4):
            print(f"  -> Scroll cycle {i}: observing responsive cards, prices, and discount tags...")
            page.mouse.wheel(0, 500)
            page.wait_for_timeout(1500)

        print("\n[Step 4] Inspecting first product card...")
        first_product = page.query_selector("div[data-id] a, a._1fQZEK, a.CGtC58, a[href*='/apple-iphone-16']")
        if first_product:
            card_title = first_product.inner_text().split("\n")[0] if first_product.inner_text() else "iPhone 16"
            print(f"  -> Clicking target card: '{card_title[:45]}...'")
            # Open in same tab or handle new page
            try:
                with context.expect_page(timeout=5000) as new_page_info:
                    first_product.click()
                new_page = new_page_info.value
                new_page.wait_for_load_state("domcontentloaded")
                new_page.bring_to_front()
                target_page = new_page
            except Exception:
                target_page = page

            page.wait_for_timeout(2000)

            print("\n[Step 5] Checking Product Detail Page (PDP): Add to Cart & Buy Now...")
            target_page.mouse.wheel(0, 400)
            target_page.wait_for_timeout(2000)

            cart_btn = target_page.query_selector("button:has-text('Add to cart'), button:has-text('ADD TO CART')")
            if cart_btn:
                print("  [+] 'Add to Cart' button found on screen.")
            else:
                print("  [i] Checking alternative checkout actions...")

            print("\n[Audit Demo Completed] Keeping window open for 10 seconds for user inspection...")
            target_page.wait_for_timeout(10000)
            if target_page != page:
                target_page.close()
        else:
            print("  -> Card clicked directly on main page. Holding for 10 seconds...")
            page.wait_for_timeout(10000)

        browser.close()
        print("\n[OK] Live browsing session completed successfully.")

if __name__ == "__main__":
    run_live_demo()
