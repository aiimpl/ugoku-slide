"""一覧ページの上部を撮って、SNS で共有されたときの画像 docs/og.png（1200×630）を作る（要 playwright）。"""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent

with sync_playwright() as pw:
    try:
        browser = pw.chromium.launch(channel="chrome", headless=True)
    except Exception:
        browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
    page.set_default_timeout(90000)
    page.goto((ROOT / "docs" / "index.html").as_uri(), wait_until="domcontentloaded")
    page.add_style_tag(content="header.top{display:none}.hero{padding-top:56px}.stage .hint,.pick,section{display:none}.hero{padding-top:80px}")
    page.wait_for_timeout(4000)
    page.screenshot(path=str(ROOT / "docs" / "og.png"))
    browser.close()
print("docs/og.png を書き出しました")
