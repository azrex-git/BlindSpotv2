import ctypes
import time
import sys
from playwright.sync_api import sync_playwright

user32 = ctypes.windll.user32

def force_foreground():
    def enum_cb(hwnd, extra):
        class_buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, class_buf, 256)
        if "Chrome_WidgetWin_1" in class_buf.value:
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            # Unhide, restore, maximize, and bring to foreground
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
            user32.SetForegroundWindow(hwnd)
        return True

    cb = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)(enum_cb)
    user32.EnumWindows(cb, 0)

print("[1/5] Launching headed Playwright Chromium browser on desktop...", flush=True)

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        slow_mo=1200,
        args=[
            "--start-maximized",
            "--disable-blink-features=AutomationControlled",
        ]
    )
    context = browser.new_context(no_viewport=True)
    page = context.new_page()

    print("[2/5] Navigating to https://www.flipkart.com/ ...", flush=True)
    page.goto("https://www.flipkart.com/", wait_until="domcontentloaded")
    time.sleep(1)
    force_foreground()

    print("[3/5] Handling popups and dismissals...", flush=True)
    page.keyboard.press("Escape")
    time.sleep(1)
    force_foreground()

    print("[4/5] Live Persona Action: Searching for 'laptops'...", flush=True)
    for sel in ("input[name='q']", "input[title*='Search']", "input[placeholder*='Search']"):
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=2000):
                loc.highlight()
                time.sleep(1)
                loc.fill("laptops")
                time.sleep(1)
                loc.press("Enter")
                break
        except Exception:
            pass

    page.wait_for_load_state("domcontentloaded")
    time.sleep(2)
    force_foreground()

    print("[5/5] Live Persona Action: Scrolling catalog and inspecting products...", flush=True)
    page.mouse.wheel(0, 600)
    time.sleep(2)
    page.mouse.wheel(0, 600)
    time.sleep(2)

    print("\n=======================================================", flush=True)
    print(">>> LIVE DEMO IS RUNNING ON YOUR DESKTOP! <<<", flush=True)
    print(">>> The browser window will stay OPEN for 10 minutes. <<<", flush=True)
    print(">>> Switch to the Chromium window to see it live! <<<", flush=True)
    print("=======================================================\n", flush=True)

    # Keep the browser open for 10 minutes so it never closes prematurely
    for remaining in range(600, 0, -10):
        print(f"Browser staying open... {remaining} seconds remaining", flush=True)
        time.sleep(10)

    browser.close()
    print("Demo closed after timeout.", flush=True)
