"""第4弾の2（図面1枚から・63-sekou）の紹介動画。日本語 29.5秒と英語 15秒（1920×1080・30fps・音つき）。

  python3 video/make_video5.py ja        日本語 → build/video/ugoku-slide-vol4b_ja.mp4
  python3 video/make_video5.py en        英語   → build/video/ugoku-slide-vol4b_en.mp4
  python3 video/make_video5.py ja g x    指定した場面だけ撮り直して、つなぎ直す

日本語：0–3 図面が入る／3–11 工程で建つ／11–14.5 回す／14.5–19.5 ばらす／19.5–23.5 日影／23.5–26.5 階数／26.5–29.5 締め
英語  ：0–4 回す／4–11 ばらす／11–15 工程の早回し
"""
import shutil
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_clips import bgm  # noqa: E402
from make_video import OUT, ffmpeg  # noqa: E402
from make_video2 import shoot_seek, slide, stage_page  # noqa: E402
from record import shoot  # noqa: E402
from stages import CHIP_CSS, page  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DECK = "63-sekou"
SEC = {"dwg": 2, "plan": 3, "exp": 5, "shade": 6, "vol": 7}
BG = (ROOT / "src" / "assets" / "sekou" / "x23.webp").resolve().as_uri()
CHIP = {"ja": "V.chip('<i></i>動くスライド 第4弾<b>建設業</b>')", "en": "V.chip('<i></i>ugoku-slide<b>free</b>')"}
# 図面が机の上からスライドへ入ってくる（動画のときだけ足す動き）
DWG_IN = (".slide.active .dwg{animation:dwgin 1.3s cubic-bezier(.2,.9,.2,1) .25s both}"
          "@keyframes dwgin{from{transform:translate(-380px,160px) rotate(-7deg) scale(.62);box-shadow:0 60px 90px -30px rgb(0 0 0 / .5)}}")


def setv(sel, v):
    return (f"(() => {{ const el = document.querySelector('.slide.active {sel}'); el.value = {v};"
            " el.dispatchEvent(new Event('input', { bubbles: true })); })()")


def prep(p, js):
    p.evaluate(js)
    p.wait_for_timeout(800)


def end_page():
    css = CHIP_CSS + """
body{background:#0f1216;color:#fff}
.bg{position:absolute;right:-40px;top:0;height:100%;opacity:.55;-webkit-mask-image:linear-gradient(90deg,transparent,#000 40%)}
.a{position:absolute;left:150px;top:250px;font-weight:900;font-size:140px;letter-spacing:-.03em;line-height:1.14}
.a span{display:block;opacity:0;animation:slam .5s cubic-bezier(.2,.9,.2,1) both}
.a span:nth-child(2){animation-delay:.35s}
.a em{font-style:normal;color:#ff7a2e}
.sub{position:absolute;left:156px;top:620px;font-size:40px;font-weight:700;color:rgb(255 255 255 / .82);animation:rise .45s cubic-bezier(.2,.9,.2,1) .8s both}
.url{position:absolute;left:150px;top:750px;padding:16px 40px;border-radius:16px;background:#e8590c;font:800 54px "Inter",sans-serif;animation:rise .45s cubic-bezier(.2,.9,.2,1) 1.1s both}
"""
    body = (f'<img class="bg" src="{BG}"><div class="a"><span>図面1枚で、</span><span><em>施工計画が動く。</em></span></div>'
            '<div class="sub">工程・回す・ばらす・日影・階数。全部スライドの中で。</div>'
            '<div class="url">aiimpl.github.io/ugoku-slide</div>')
    return page(css, body)


def scenes(lang, names):
    S = {}
    chip = CHIP[lang]
    ja = lang == "ja"

    def a(b):  # 図面が入る
        p = slide(b, DECK, SEC["dwg"], chip=chip)
        p.add_style_tag(content=DWG_IN)
        p.evaluate("document.querySelectorAll('.slide.active .dwg').forEach(d => { d.style.animation = 'none'; d.offsetHeight; d.style.animation = ''; })")
        return p, 3.0, [(0, "document.querySelectorAll('.slide.active .dwg').forEach(d => d.getAnimations().forEach(x => { x.currentTime = 0; x.play(); }))"),
                        (0, "V.cap('図面を1枚、<em>渡すだけ。</em>')"), (0.02, "V.from(560,900)"), (0.25, "V.move([1240,620], 1.3)")]
    S["a"] = a

    def g(b):  # 工程で建つ
        p = slide(b, DECK, SEC["plan"], chip=chip)
        prep(p, setv(".drag", 0))
        if ja:
            acts = [(0, "V.cap('工程表どおりに、<em>建っていく。</em>')"), (5.2, "V.cap('出来高も、<em>その場で計算。</em>')")]
            dur, d = 8.0, 7.2
        else:
            acts = [(0, "V.cap('Then build it again, <em>week by week.</em>')")]
            dur, d = 4.0, 3.5
        return p, dur, acts + [(0.02, "V.from(1500,980)"), (0.3, f"V.drag('.slide.active .drag', 52, {d}, true)")]
    S["g"] = g

    def r(b):  # 回す
        p = slide(b, DECK, SEC["plan"], chip=chip)
        p.wait_for_function("window.__turnReady === true", timeout=60000)
        prep(p, setv(".drag", 52))
        cap = "V.cap('ぐるっと<em>回せる。</em>')" if ja else "V.cap('A slide. <em>Drag to spin it.</em>')"
        dur = 3.5 if ja else 4.0
        return p, dur, [(0, cap), (0.02, "V.from(1500,900)"), (0.3, f"V.orbit('.slide.active .bldg', -432, 0, {dur - 0.6})")]
    S["r"] = r

    def x(b):  # ばらす
        p = slide(b, DECK, SEC["exp"], chip=chip)
        prep(p, setv("input[name=e]", 0))
        cap = "V.cap('部品ごとに、<em>ばらせる。</em>')" if ja else "V.cap('Then <em>pull it apart.</em>')"
        dur = 5.0 if ja else 7.0
        half = (dur - 0.8) / 2
        return p, dur, [(0, cap), (0.02, "V.from(700,980)"), (0.3, f"V.drag('.slide.active input[name=e]', 1, {half}, true)"),
                        (0.4 + half, f"V.drag('.slide.active input[name=e]', 0, {half - 0.2}, true)")]
    S["x"] = x

    def h(b):  # 冬至の日影
        p = slide(b, DECK, SEC["shade"], chip=chip)
        prep(p, setv("input[name=t]", 8))
        return p, 4.0, [(0, "V.cap('冬至の日影も、<em>動かして確かめる。</em>')"), (0.02, "V.from(700,980)"),
                        (0.3, "V.drag('.slide.active input[name=t]', 16, 3.3, true)")]
    S["h"] = h

    def v(b):  # 階数を変える
        p = slide(b, DECK, SEC["vol"], chip=chip)
        prep(p, setv("input[name=n]", 8))
        return p, 3.0, [(0, "V.cap('階数を変えると、<em>日影が変わる。</em>')"), (0.02, "V.from(700,980)"),
                        (0.3, "V.drag('.slide.active input[name=n]', 6, 2.3, true)")]
    S["v"] = v

    def e(b):
        return stage_page(b, "v5e", end_page()), 3.0, []
    S["e"] = e
    return [(n, S[n]) for n in names]


ORDER = {"ja": ["a", "g", "r", "x", "h", "v", "e"], "en": ["r", "x", "g"]}
SEEK = {"e"}


def main():
    lang = sys.argv[1] if len(sys.argv) > 1 else "ja"
    order = ORDER[lang]
    only = sys.argv[2:] or order
    mp4 = OUT / f"ugoku-slide-vol4b_{lang}.mp4"
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = pw.chromium.launch(headless=True)
        for name, make in scenes(lang, [n for n in order if n in only]):
            p, dur, acts = make(browser)
            p.evaluate("Promise.all([...document.images].map(i => i.decode().catch(() => {})))")
            out = OUT / "scenes" / f"v5{lang}{name}"
            n = shoot_seek(p, out, dur, acts) if name in SEEK else shoot(p, out, dur, acts)
            p.close()
            print(f"{name}: {dur}s・{n} コマ")
        browser.close()
    seq = OUT / f"all5{lang}"
    shutil.rmtree(seq, ignore_errors=True)
    seq.mkdir()
    k, t, hits = 0, 0.0, []
    for name in order:
        hits.append(t)
        for f in sorted((OUT / "scenes" / f"v5{lang}{name}").glob("[0-9]*.png")):
            (seq / f"{k:05d}.png").hardlink_to(f)
            k += 1
        t = k / 30
    wav = OUT / f"music5{lang}.wav"
    bgm(wav, t, hits[1:])
    ffmpeg(seq, wav, mp4)
    print(f"書き出しました：{mp4.relative_to(ROOT)}（{t:.1f}秒）")


if __name__ == "__main__":
    main()
