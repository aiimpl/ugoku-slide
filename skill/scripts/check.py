"""動くスライドを1本、ブラウザで開いて確かめる。

  python3 check.py スライド.html            確かめて、各ページの画像を撮る
  python3 check.py スライド.html --morph    ページ送りの途中のコマ（0.1・0.25・0.45 秒）も撮る
  python3 check.py スライド.html --final    仕上がり用。雛形の架空の社名や注記の消し忘れも見る

結果は3段で出る。「問題」は直す。「要確認」は画像を見て判断する。「情報」は参考。
問題が1つでもあれば終了コード 1。

画像はスライドと同じフォルダの check/<名前>/ に出る。
  NN.png       → で出す部分を全部出した状態
  NN-0.png     開いた直後（→ で出す部分がまだ隠れている）
  NN-why.png   根拠（details.why）を開いた状態（2つ以上なら NN-why1.png… と1つずつ）
  NN-sheet.png 表（data-sheet）に、1.4倍の数字で3行多い表を貼った状態
  NN-t100.png  前のページから送った途中のコマ（--morph のとき）

要 playwright：pip install playwright のあと、Chrome が無ければ playwright install chromium
"""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

CHECKS_JS = (Path(__file__).with_name("checks.js")).read_text()

# 文章の点検
PLACEHOLDER = re.compile(r"◯◯|〇〇|○○|ＸＸ|(?<![A-Za-z])xx(?![A-Za-z])|YYYY|Text \d|TODO|TBD|【|】")
SAMPLE = re.compile(r"サンプル|架空|SAMPLE|Sample")
AI_WORDS = ["まさに", "非常に", "シナジー", "シームレス", "ソリューション", "革新的", "画期的", "包括的", "多角的", "抜本的"]
COUNT = re.compile(r"([2-9２-９]|[二三四五六七八九])(つ|点|個|段階|項目|ステップ|案)")
KANJI_NUM = {"二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
DESU = re.compile(r"(です|ます|ました|でした|ません)[。！？]?$")

# はみ出した量ごとの直し方
def fix_hint(px):
    if px <= 40:
        return "間隔を少し詰める"
    if px <= 90:
        return "余白を詰める"
    if px <= 160:
        return "見出しか文字を少し小さくする"
    return "文を減らすか、ページを分ける"


def lum(c):
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0] / 255) + 0.7152 * f(c[1] / 255) + 0.0722 * f(c[2] / 255)


def ratio_on(fg, bg):
    a = fg[3]
    text = [fg[j] * a + bg[j] * (1 - a) for j in range(3)]
    L1, L2 = lum(text), lum(bg)
    return (max(L1, L2) + 0.05) / (min(L1, L2) + 0.05)


def contrast(png, inks):
    """撮った画像から、文字の後ろの色（文字の色に近い画素を除いた、いちばん多い色）を拾って比べる"""
    try:
        from PIL import Image
    except ImportError:
        return []
    im = Image.open(png).convert("RGB")
    out = []
    for ink in inks:
        l, t, w, h = ink["box"]
        crop = im.crop((max(0, int(l)), max(0, int(t)), min(1280, int(l + w)), min(720, int(t + h))))
        fg = ink["fg"]
        # 色ごとの画素数（8段ずつにまとめる）。文字の色に近い色は除いて、いちばん多い色を背景とみなす
        colors = crop.point(lambda v: v // 8 * 8 + 4).getcolors(1 << 16) or []
        colors = [(n, c) for n, c in colors if abs(c[0] - fg[0]) + abs(c[1] - fg[1]) + abs(c[2] - fg[2]) >= 90]
        if sum(n for n, _ in colors) < 8:
            continue
        bg = max(colors)[1]
        ratio = max(ratio_on(fg, bg), ratio_on(ink["stroke"], bg) if ink.get("stroke") else 0)
        need = 3 if ink["large"] else 4.5
        if ratio < need:
            out.append({"text": ink["text"], "ratio": round(ratio, 2), "need": need})
    return out[:5]


def lint_text(texts, final):
    """texts：ページごとの {heads, body, counts}。問題と要確認の一覧を返す"""
    problems, warns = [], []
    ends = []
    for i, t in enumerate(texts):
        page = f"{i + 1}枚目"
        allt = "\n".join(t["heads"]) + "\n" + t["body"]
        m = PLACEHOLDER.search(allt)
        if m:
            problems.append(f"{page} 仮の文字が残っている：「{m.group(0)}」")
        if final:
            m = SAMPLE.search(allt)
            if m:
                problems.append(f"{page} 雛形の架空の社名・注記が残っている：「{m.group(0)}」")
        words = [w for w in AI_WORDS if w in allt]
        if words:
            warns.append(f"{page} ありがちな言い回し：{'・'.join(words)}（具体的な言葉に言い換えると伝わる）")
        for h in t["heads"]:
            if len(h) > 60:
                warns.append(f"{page} 見出しが長い（{len(h)}字）。60字までに")
            m = COUNT.search(h)
            if m:
                n = KANJI_NUM.get(m.group(1)) or int(m.group(1).translate(str.maketrans("２３４５６７８９", "23456789")))
                if n not in t["counts"]:
                    warns.append(f"{page} 見出しは「{m.group(0)}」だが、同じ形で並ぶ要素が{n}個ない")
        ends.append(re.sub(r"[。、！？!?」』）)]+$", "", t["heads"][-1])[-2:] if t["heads"] else None)
    for i in range(len(ends) - 2):
        if ends[i] and ends[i] == ends[i + 1] == ends[i + 2]:
            warns.append(f"{i + 1}〜{i + 3}枚目 見出しの終わりが3枚続けて「{ends[i]}」")
    heads = [h for t in texts for h in t["heads"]]
    if len(heads) >= 4 and sum(bool(DESU.search(h)) for h in heads) * 2 > len(heads):
        warns.append("見出しの半分以上が です・ます で終わる。言い切りにすると締まる")
    return problems, warns


def run(html, out=None, morph=False, final=False):
    """1本を確かめて {"n", "problems", "warns", "infos", "out"} を返す"""
    f = Path(html).resolve()
    out = Path(out) if out else f.parent / "check" / f.stem
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.png"):
        old.unlink()
    P, Wn, I = [], [], []
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
        page.add_script_tag(content=CHECKS_JS)
        page.wait_for_timeout(1500)
        C = lambda name, *a: page.evaluate(f"(a) => UGK_CHECK.{name}(...a)", list(a))
        n = C("count")
        if not n:
            raise SystemExit("スライド（.deck > .slide）が見つかりません")
        texts, still = [], []
        for i in range(n):
            pg = f"{i + 1}枚目"
            # 開いた直後。#番号で開くと → で出す部分が全部出るので、前のページから → で入る
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
                        if t == 250:
                            gone = C("offscreen")
                            if gone:
                                Wn.append(f"{i}→{i + 1}枚目 変形の途中で画面の外へ出る：{'・'.join(gone)}")
            page.wait_for_timeout(1100)
            steps = C("steps", i)
            if steps:
                page.screenshot(path=str(out / f"{i + 1:02d}-0.png"))
                for _ in range(steps):
                    page.keyboard.press("ArrowRight")
                    page.wait_for_timeout(150)
                page.wait_for_timeout(300)
            C("settle")
            page.screenshot(path=str(out / f"{i + 1:02d}.png"))
            # 全部出した状態で測る
            P += [f"{pg} はみ出し {o['px']}px「{o['text']}」→ {fix_hint(o['px'])}" for o in C("overflow", i)]
            Wn += [f"{pg} 文字が重なる：{o}" for o in C("overlap", i)]
            P += [f"{pg} 文字が背景に沈む「{o['text']}」{o['ratio']}:1（{o['need']}:1 以上に）"
                  for o in contrast(out / f"{i + 1:02d}.png", C("inks", i))]
            lay = C("layout", i)
            if i and lay["gap"] > 240:  # 下の3分の1が空いている
                Wn.append(f"{pg} 下が {lay['gap']}px 空いている（中身は画面の {round(lay['fill'] * 100)}%）")
            sizes = C("fonts", i)
            if len(sizes) > 8:
                Wn.append(f"{pg} 文字の大きさが {len(sizes)} 種類（{'・'.join(map(str, sizes))}px）。近い大きさをまとめると揃って見える")
            ops = C("ops", i)
            if len(ops["kinds"]) > 1:
                Wn.append(f"{pg} 操作が {'・'.join(ops['kinds'])} の {len(ops['kinds'])} つ。1ページ1つにすると伝わりやすい")
            still.append(not ops["moves"])
            texts.append(C("text", i))
        # 根拠を全部開いた状態・表を貼り替えた状態
        for i in range(n):
            pg = f"{i + 1}枚目"
            page.evaluate(f"location.hash = '#{i + 1}'")
            page.wait_for_timeout(900)
            nwhy = C("openWhy", i, -1)
            for k in range(nwhy):  # 発表では1つずつ開くので、1つずつ開いて測る
                C("openWhy", i, k)
                page.wait_for_timeout(600)
                page.screenshot(path=str(out / (f"{i + 1:02d}-why.png" if nwhy == 1 else f"{i + 1:02d}-why{k + 1}.png")))
                P += [f"{pg} 根拠{k + 1}を開くとはみ出す {o['px']}px「{o['text']}」→ {fix_hint(o['px'])}" for o in C("overflow", i)]
                Wn += [f"{pg} 根拠{k + 1}を開くと文字が重なる：{o}" for o in C("overlap", i)]
            if nwhy:
                C("openWhy", i, -1)
            if C("hasSheet", i):
                P += [f"{pg} {b}" for b in C("sheet", i)]
                page.wait_for_timeout(900)
                page.screenshot(path=str(out / f"{i + 1:02d}-sheet.png"))
                P += [f"{pg} 表を貼り替えるとはみ出す {o['px']}px「{o['text']}」" for o in C("overflow", i)]
        P += C("calc")
        # 書体の読み込みなど、通信の失敗はスライドの不具合ではないので数えない
        P += ["エラー: " + e for e in errors if "fonts.g" not in e and "Failed to load resource" not in e]
        cr = C("carry")
        browser.close()
    p2, w2 = lint_text(texts, final)
    P += p2
    Wn += w2
    if sum(still) * 2 > n:
        Wn.append(f"動きのないページが {sum(still)} / {n} 枚。根拠・順に出す・スライダーのどれかを足すと「動くスライド」らしくなる")
    if cr["morph"]:
        joins = cr["joins"]
        bare = [f"{j + 1}→{j + 2}" for j, ok in enumerate(joins) if not ok]
        I.append(f"つながり {sum(joins)}/{len(joins)}" + (f"（{'・'.join(bare)} はつながらない）" if bare else "（全部の境目がつながる）"))
    return {"n": n, "problems": P, "warns": Wn, "infos": I, "out": out}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    r = run(args[0], morph="--morph" in sys.argv, final="--final" in sys.argv)
    name = Path(args[0]).name
    print(f"{name}（{r['n']}枚）: " + (f"問題 {len(r['problems'])} 件" if r["problems"] else "問題なし") +
          (f"・要確認 {len(r['warns'])} 件" if r["warns"] else ""))
    for x in r["problems"]:
        print("  問題　" + x)
    for x in r["warns"]:
        print("  要確認 " + x)
    for x in r["infos"]:
        print("  情報　" + x)
    print(f"画像: {r['out']}/（「問題なし」でも画像は必ず見る）")
    sys.exit(1 if r["problems"] else 0)


if __name__ == "__main__":
    main()
