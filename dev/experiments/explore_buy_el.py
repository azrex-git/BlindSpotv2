import sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

p = sync_playwright().start()
b = p.chromium.launch(headless=True)
context = b.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
page = context.new_page()
page.goto("https://www.flipkart.com/apple-iphone-16-plus-black-128-gb/p/itm1abbae671f9ef", wait_until="domcontentloaded")
page.wait_for_timeout(3000)

els = page.evaluate("""() => {
    const res = [];
    document.querySelectorAll('*').forEach(el => {
        const t = (el.innerText || '').trim();
        if (t.toLowerCase() === 'buy now' || t.toLowerCase().startsWith('buy at')) {
            res.push({
                tag: el.tagName,
                className: el.className,
                text: t,
                role: el.getAttribute('role'),
                parentTag: el.parentElement ? el.parentElement.tagName : null,
                parentClass: el.parentElement ? el.parentElement.className : null
            });
        }
    });
    return res;
}""")
print("Matching elements:", els)

b.close()
p.stop()
