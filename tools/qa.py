"""書き出したスライドをブラウザで開いて確かめる（要 playwright）。

  python3 tools/qa.py                 全部
  python3 tools/qa.py 01-swiss 05     名前の先頭が一致するものだけ

  各スライドの画像を build/qa/<名前>/NN.png（全部並べたものは sheet.png）に保存し、次を報告する：
  ・JavaScript のエラー
  ・スライドの枠（1280×720）からはみ出した要素
  ・data-calc の入力を動かしても数字が変わらない箇所
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs" / "slides"
OUT = ROOT / "build" / "qa"

OVERFLOW_JS = """(i) => {
  const s = document.querySelectorAll('.deck > .slide')[i];
  const box = s.getBoundingClientRect();
  const k = box.width / 1280;
  const bad = [];
  s.querySelectorAll('*').forEach(el => {
    if (el.closest('.bg,.notes,details:not([open]) > .body,[hidden]')) return;
    const st = getComputedStyle(el);
    if (st.position === 'fixed' || st.visibility === 'hidden' || st.display === 'none') return;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) return;
    const over = Math.max(r.right - box.right, r.bottom - box.bottom, box.left - r.left, box.top - r.top) / k;
    if (over > 4 && el.children.length === 0 && el.textContent.trim()) bad.push(el.tagName.toLowerCase() + '.' + el.className + ' 「' + el.textContent.trim().slice(0, 20) + '」 +' + Math.round(over) + 'px');
  });
  return bad.slice(0, 5);
}"""

CALC_JS = """() => {
  const res = [];
  document.querySelectorAll('[data-calc]').forEach((box, bi) => {
    const outs = [...box.querySelectorAll('[data-out]')];
    box.querySelectorAll('input[type=range],input[type=checkbox]').forEach(inp => {
      const before = outs.map(o => o.textContent);
      const old = inp.type === 'checkbox' ? inp.checked : inp.value;
      if (inp.type === 'checkbox') inp.checked = !inp.checked;
      const read = v => {
        if (inp.type === 'checkbox') inp.checked = v; else inp.value = v;
        outs.forEach(o => { o._v = NaN; });
        inp.dispatchEvent(new Event('input', {bubbles: true}));
        return outs.map(o => o.textContent);
      };
      // 最大と最小の両方で試す（しきい値のある式は片方だけ変わることがある）
      const tries = inp.type === 'checkbox' ? [read(!old)] : [read(inp.max), read(inp.min)];
      const after = tries[tries.length - 1];
      if (outs.length && tries.every(a => before.every((t, i) => t === a[i]))) res.push('calc#' + bi + ' ' + inp.name + ' を動かしても数字が変わらない');
      if (tries.some(a => a.some(t => t.includes('NaN') || t === '—'))) res.push('calc#' + bi + ' ' + inp.name + ' で計算できない式がある');
      if (inp.type === 'checkbox') inp.checked = old; else inp.value = old;
      outs.forEach(o => { o._v = NaN; });
      inp.dispatchEvent(new Event('input', {bubbles: true}));
    });
  });
  return res;
}"""


def sheet(out):
    """全スライドを1枚に並べた一覧画像 sheet.png を作る（Pillow があれば）"""
    try:
        from PIL import Image
    except ImportError:
        return
    shots = sorted(out.glob("[0-9][0-9].png"))
    ims = [Image.open(p).resize((640, 360)) for p in shots]
    board = Image.new("RGB", (1280, 360 * ((len(ims) + 1) // 2)), "white")
    for i, im in enumerate(ims):
        board.paste(im, ((i % 2) * 640, (i // 2) * 360))
    board.save(out / "sheet.png")


def main():
    pats = sys.argv[1:]
    files = [p for p in sorted(DOCS.glob("*.html")) if not pats or any(p.stem.startswith(x) for x in pats)]
    problems = 0
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = pw.chromium.launch(headless=True)  # Chrome が無ければ playwright の Chromium
        for f in files:
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            page.set_default_timeout(90000)  # Google Fonts が遅いときがある
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.goto(f.as_uri(), wait_until="domcontentloaded")
            page.wait_for_timeout(800)  # フォントを待ちすぎない
            page.wait_for_timeout(700)
            n = page.evaluate("document.querySelectorAll('.deck > .slide').length")
            out = OUT / f.stem
            out.mkdir(parents=True, exist_ok=True)
            report = []
            for i in range(n):
                page.evaluate(f"location.hash = '#{i + 1}'")
                page.wait_for_timeout(1100)
                page.screenshot(path=str(out / f"{i + 1:02d}.png"))
                for b in page.evaluate(OVERFLOW_JS, i):
                    report.append(f"  {i + 1}枚目 はみ出し: {b}")
            sheet(out)
            report += ["  " + r for r in page.evaluate(CALC_JS)]
            report += ["  エラー: " + e for e in errors if "fonts.g" not in e]
            print(f"{'NG' if report else 'OK'} {f.stem}（{n}枚）")
            for r in report:
                print(r)
            problems += bool(report)
            page.close()
        browser.close()
    print(f"\n{len(files)} 本中 {problems} 本に指摘あり。画像は {OUT.relative_to(ROOT)}/")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
