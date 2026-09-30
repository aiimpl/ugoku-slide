"""ページ送りの途中のコマを撮る（data-morph の確認用。要 playwright・Pillow）。

  python3 tools/morphqa.py 51                 51 で始まるスライドを、0.12・0.3・0.5・1.4 秒で撮る
  python3 tools/morphqa.py 51 100 250 450     撮る時刻（ミリ秒）を指定

  build/morph/<番号>_board.png に、行＝ページのつなぎ目、列＝時刻で並べる。
"""
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "morph"


def main():
    pat = sys.argv[1]
    times = [int(x) for x in sys.argv[2:]] or [120, 300, 500, 1400]
    f = next(p for p in sorted((ROOT / "docs" / "slides").glob("*.html")) if p.stem.startswith(pat))
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True)
        pg = b.new_page(viewport={"width": 1280, "height": 720})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto(f.as_uri())
        pg.wait_for_timeout(1500)
        n = pg.evaluate("document.querySelectorAll('.deck>.slide').length")
        rows = []
        for i in range(n - 1):
            # 手順（.step）を最後まで出してから、次のページへ送る
            pg.evaluate(f"location.hash='#{i + 1}'")
            pg.wait_for_timeout(1300)
            for _ in range(20):
                if pg.evaluate("document.querySelector('.slide.active').querySelectorAll('.step:not(.shown)').length") == 0:
                    break
                pg.keyboard.press("ArrowRight")
                pg.wait_for_timeout(120)
            pg.wait_for_timeout(600)
            t0, shots = 0, []
            pg.keyboard.press("ArrowRight")
            for t in times:
                pg.wait_for_timeout(t - t0)
                t0 = t
                p = OUT / f"{f.stem[:2]}_{i + 1}to{i + 2}_{t}.png"
                pg.screenshot(path=str(p))
                shots.append(p)
            rows.append(shots)
        b.close()
    ims = [[Image.open(p).resize((480, 270)) for p in r] for r in rows]
    board = Image.new("RGB", (480 * len(times), 270 * len(ims)), "white")
    for y, r in enumerate(ims):
        for x, im in enumerate(r):
            board.paste(im, (x * 480, y * 270))
    board.save(OUT / f"{f.stem[:2]}_board.png")
    print(f"{OUT.relative_to(ROOT)}/{f.stem[:2]}_board.png", "エラー:", errs or "なし")


if __name__ == "__main__":
    main()
