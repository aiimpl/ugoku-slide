"""動くスライドを1本、ブラウザで開いて確かめる。

  python3 check.py スライド.html            問題の一覧と、各ページの画像
  python3 check.py スライド.html --morph    ページ送りの途中のコマ（0.1・0.25・0.45 秒）も撮る

  画像はスライドと同じフォルダの check/<名前>/ に出る。
    NN.png          → で出す部分を全部出した状態
    NN-0.png        そのページを開いた直後（→ で出す部分がまだ隠れている状態。ある時だけ）
    NN-t100.png など 前のページから送った途中のコマ（--morph のとき）
    NN-why.png      根拠（details.why）を全部開いた状態（ある時だけ）
    NN-sheet.png    表（data-sheet）に、1.4倍の数字で3行多い表を貼った状態（ある時だけ）

  確かめること
    ・JavaScript のエラー
    ・1280×720 の枠からはみ出した文字
    ・スライダーを動かしても変わらない数字、計算できない式（— と出る）
    ・根拠を開いたとき・表を貼り替えたときのはみ出しと、表の集計が計算できない所
    ・枠の中で文字どうしが重なっている所（要確認。字間を詰めた見出しなど、見た目では重なっていないこともある）
  枠の中の重なりや、図と文字の重なりは、最後は画像を見て確かめること。

  要 playwright：pip install playwright のあと、Chrome が無ければ playwright install chromium
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

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


OVERLAP_JS = """(i) => {
  const s = document.querySelectorAll('.deck > .slide')[i];
  const k = s.getBoundingClientRect().width / 1280;
  const leaves = [];
  s.querySelectorAll('*').forEach(el => {
    if (el.closest('.bg,.notes,details:not([open]) > .body,[hidden],[aria-hidden=true],svg,.ugk-ghost')) return;
    if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return;
    if (el.checkVisibility && !el.checkVisibility({opacityProperty: true, visibilityProperty: true})) return;
    let op = 1; for (let e = el; e && e !== s; e = e.parentElement) op *= parseFloat(getComputedStyle(e).opacity);
    if (op < .5) return;
    const r = document.createRange(); r.selectNodeContents(el);
    // 行ごとの箱を、文字の大きさの範囲（上下の行間を除く）に縮める
    const fs = parseFloat(getComputedStyle(el).fontSize);
    [...r.getClientRects()].forEach(b => {
      if (b.width < 2 || b.height < 2) return;
      const pad = Math.max(0, (b.height - fs * 0.78) / 2);
      leaves.push([el, { left: b.left, right: b.right, top: b.top + pad, bottom: b.bottom - pad, width: b.width, height: b.height - 2 * pad }]);
    });
  });
  const bad = [];
  for (let a = 0; a < leaves.length; a++) for (let c = a + 1; c < leaves.length; c++) {
    const [e1, r1] = leaves[a], [e2, r2] = leaves[c];
    if (e1 === e2 || e1.contains(e2) || e2.contains(e1)) continue;
    const w = Math.min(r1.right, r2.right) - Math.max(r1.left, r2.left), h = Math.min(r1.bottom, r2.bottom) - Math.max(r1.top, r2.top);
    if (w <= 0 || h <= 0) continue;
    const area = w * h, m = Math.min(r1.width * r1.height, r2.width * r2.height);
    if (h > Math.min(r1.height, r2.height) * 0.35 && w > Math.min(r1.width, r2.width) * 0.2 && w / k > 6 && h / k > 4) bad.push('「' + e1.textContent.trim().slice(0, 12) + '」と「' + e2.textContent.trim().slice(0, 12) + '」');
  }
  return bad.slice(0, 5);
}"""

# そのページで → を押す回数（.step の数と、コードの強調の段数）
STEPS_JS = """(i) => { const s = document.querySelectorAll('.deck > .slide')[i];
  return s.querySelectorAll('.step').length + [...s.querySelectorAll('pre.code[data-highlight]')].reduce((a, p) => a + p.dataset.highlight.split('|').length, 0); }"""

OPEN_WHY_JS = "(i) => { const d = [...document.querySelectorAll('.deck > .slide')[i].querySelectorAll('details.why')]; d.forEach(x => { x.open = true; x.dispatchEvent(new Event('toggle')); }); return d.length; }"

# 表（data-sheet）に、今の表の1.4倍の数字と3行多い表を貼る。集計が「—」になる所を返す
SHEET_JS = r"""(i) => {
  const s = document.querySelectorAll('.deck > .slide')[i], bad = [];
  s.querySelectorAll('[data-sheet]').forEach((fig, k) => {
    const t = fig.querySelector('table');
    const head = [...t.querySelectorAll('thead th')].map(x => x.textContent.trim());
    const rows = [...t.querySelectorAll('tbody tr')].map(tr => [...tr.children].map(x => x.textContent.trim()));
    const num = v => parseFloat(String(v).replace(/[,，]/g, ''));
    const more = rows.concat(rows.slice(0, 3).map((r, j) => [r[0] + '（追加' + (j + 1) + '）', ...r.slice(1)]));
    const tsv = [head, ...more.map(r => [r[0], ...r.slice(1).map(v => isFinite(num(v)) ? String(Math.round(num(v) * 1.4 * 10) / 10) : v)])].map(r => r.join('\t')).join('\n');
    const dt = new DataTransfer(); dt.setData('text/plain', tsv);
    fig.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true }));
    fig.querySelectorAll('[data-sheet-out]').forEach(o => { if (/NaN|—|undefined/.test(o.textContent)) bad.push('表' + (k + 1) + ' の集計「' + o.dataset.sheetOut + '」が計算できない'); });
  });
  return bad;
}"""


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    morph = "--morph" in sys.argv
    f = Path(args[0]).resolve()
    out = f.parent / "check" / f.stem
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.png"):
        old.unlink()
    report, notes = [], []
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.set_default_timeout(90000)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.goto(f.as_uri(), wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        n = page.evaluate("document.querySelectorAll('.deck > .slide').length")
        if not n:
            raise SystemExit("スライド（.deck > .slide）が見つかりません")
        for i in range(n):
            # 開いた直後（前のページから → で入る。#番号で開くと → で出す部分が全部出た状態になるため）
            if i:
                page.evaluate(f"location.hash = '#{i}'")
                page.wait_for_timeout(1100)
                page.keyboard.press("ArrowRight")
                if morph:
                    t0 = 0
                    for t in (100, 250, 450):
                        page.wait_for_timeout(t - t0)
                        t0 = t
                        page.screenshot(path=str(out / f"{i + 1:02d}-t{t}.png"))
            page.wait_for_timeout(1100)
            steps = page.evaluate(STEPS_JS, i)
            if steps:
                page.screenshot(path=str(out / f"{i + 1:02d}-0.png"))
                # → を押し切って、全部出した状態にする
                for _ in range(steps):
                    page.keyboard.press("ArrowRight")
                    page.wait_for_timeout(150)
                page.wait_for_timeout(900)
            page.screenshot(path=str(out / f"{i + 1:02d}.png"))
            report += [f"{i + 1}枚目 はみ出し: {b}" for b in page.evaluate(OVERFLOW_JS, i)]
            notes += [f"{i + 1}枚目 重なり（要確認）: {b}" for b in page.evaluate(OVERLAP_JS, i)]
        # 根拠（details.why）を全部開いた状態・表を貼り替えた状態
        for i in range(n):
            page.evaluate(f"location.hash = '#{i + 1}'")
            page.wait_for_timeout(900)
            if page.evaluate(OPEN_WHY_JS, i):
                page.wait_for_timeout(600)
                page.screenshot(path=str(out / f"{i + 1:02d}-why.png"))
                report += [f"{i + 1}枚目 根拠を開くとはみ出す: {b}" for b in page.evaluate(OVERFLOW_JS, i)]
                notes += [f"{i + 1}枚目 根拠を開くと重なる（要確認）: {b}" for b in page.evaluate(OVERLAP_JS, i)]
            if page.evaluate(f"document.querySelectorAll('.deck > .slide')[{i}].querySelector('[data-sheet]') !== null"):
                report += [f"{i + 1}枚目 {b}" for b in page.evaluate(SHEET_JS, i)]
                page.wait_for_timeout(900)
                page.screenshot(path=str(out / f"{i + 1:02d}-sheet.png"))
                report += [f"{i + 1}枚目 表を貼り替えるとはみ出す: {b}" for b in page.evaluate(OVERFLOW_JS, i)]
        report += page.evaluate(CALC_JS)
        report += ["エラー: " + e for e in errors if "fonts.g" not in e]
        browser.close()
    print(f"{f.name}（{n}枚）: " + ("問題なし" if not report else f"{len(report)} 件"))
    for r in report + notes:
        print("  " + r)
    print(f"画像: {out}/（重なり・変形の途中は画像を見て確かめる）")
    sys.exit(1 if report else 0)


if __name__ == "__main__":
    main()
