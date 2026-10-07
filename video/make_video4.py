"""第4弾（建設業・63-sekou）の紹介動画（1920×1080・30fps・28.5秒・音つき）。

  python3 video/make_video4.py            全部作って build/video/ugoku-slide-vol4_25s.mp4 に
  python3 video/make_video4.py s h        指定した場面だけ撮り直して、つなぎ直す

0–9 工程表の「今日」の線をつかんで動かすとビルが建つ／9–12.5 完成した建物をドラッグで回す／12.5–17.5 めくると断面／14–19 冬至の日影／19–22 夕景／22–25 締め
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
MP4 = OUT / "ugoku-slide-vol4_25s.mp4"
CHIP_JS = "V.chip('<i></i>動くスライド 第4弾<b>建設業</b>')"
DECK = "63-sekou"
BG = (ROOT / "src" / "assets" / "sekou" / "d11.webp").resolve().as_uri()


def setv(sel, v):
    return (f"(() => {{ const el = document.querySelector('.slide.active {sel}'); el.value = {v};"
            " el.dispatchEvent(new Event('input', { bubbles: true })); })()")


def end_page():
    css = CHIP_CSS + """
body{background:#0f1216;color:#fff}
.bg{position:absolute;right:0;top:0;height:100%;opacity:.5;-webkit-mask-image:linear-gradient(90deg,transparent,#000 45%)}
.a{position:absolute;left:150px;top:250px;font-weight:900;font-size:150px;letter-spacing:-.03em;line-height:1.12}
.a span{display:block;opacity:0;animation:slam .5s cubic-bezier(.2,.9,.2,1) both}
.a span:nth-child(2){animation-delay:.35s}
.a em{font-style:normal;color:#ff7a2e}
.sub{position:absolute;left:156px;top:640px;font-size:40px;font-weight:700;color:rgb(255 255 255 / .82);animation:rise .45s cubic-bezier(.2,.9,.2,1) .8s both}
.url{position:absolute;left:150px;top:770px;padding:16px 40px;border-radius:16px;background:#e8590c;font:800 54px "Inter",sans-serif;animation:rise .45s cubic-bezier(.2,.9,.2,1) 1.1s both}
"""
    body = (f'<img class="bg" src="{BG}"><div class="a"><span>パワポのまま、</span><span><em>建物が動く。</em></span></div>'
            '<div class="sub">工程・断面・日影・外観。Blender の建物を、スライドの中で。</div>'
            '<div class="url">aiimpl.github.io/ugoku-slide</div>')
    return page(css, body)


def scenes(names):
    S = {}

    def g(b):  # 工程表の線をつかんで動かすと、ビルが建つ
        p = slide(b, DECK, 3, chip=CHIP_JS)
        return p, 9.0, [(0, setv(".drag", 0)), (0, "V.cap('工程表の線を、<em>つかんで動かすと</em>')"), (0.02, "V.from(1500,980)"),
                        (0.7, "V.drag('.slide.active .drag', 52, 7.3, true)"),
                        (3.3, "V.cap('<em>ビルが、1階ずつ建つ。</em>')"),
                        (6.4, "V.cap('進捗も出来高も、<em>その場で計算。</em>')")]
    S["g"] = g

    def r(b):  # 完成したら、ドラッグで回せる
        p = slide(b, DECK, 3, chip=CHIP_JS)
        p.wait_for_function("window.__turnReady === true", timeout=60000)
        p.evaluate(setv(".drag", 52))
        p.wait_for_timeout(800)
        return p, 3.5, [(0, "V.cap('完成したら、<em>ぐるっと回せる。</em>')"),
                        (0.02, "V.from(1500,900)"), (0.3, "V.orbit('.slide.active .bldg', -432, 0, 2.9)")]
    S["r"] = r

    def s(b):  # めくると、そのまま断面に
        p = slide(b, DECK, 3, chip=CHIP_JS)
        return p, 5.0, [(0, setv(".drag", 52)), (0, "V.cap('めくると、<em>そのまま断面に。</em>')"),
                        (0.5, "V.key('ArrowRight')")]
    S["s"] = s

    def h(b):  # 冬至の日影
        p = slide(b, DECK, 6, chip=CHIP_JS)
        return p, 5.0, [(0, setv("input[name=t]", 8)), (0, "V.cap('冬至の日影も、<em>動かして確かめる。</em>')"),
                        (0.02, "V.from(700,980)"), (0.5, "V.drag('.slide.active input[name=t]', 16, 4.0, true)")]
    S["h"] = h

    def d(b):  # 夕景
        p = slide(b, DECK, 8, chip=CHIP_JS)
        return p, 3.0, [(0, "document.getAnimations().forEach(a => { a.currentTime = 0; })"),
                        (0, "V.cap('完成の姿は、<em>Blender で。</em>')")]
    S["d"] = d

    def e(b):
        return stage_page(b, "v4e", end_page()), 3.0, []
    S["e"] = e
    return [(n, S[n]) for n in names]


ORDER = ["g", "r", "s", "h", "d", "e"]
SEEK = {"e", "s"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1:] or ORDER
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = pw.chromium.launch(headless=True)
        for name, make in scenes([n for n in ORDER if n in only]):
            p, dur, acts = make(browser)
            p.evaluate("Promise.all([...document.images].map(i => i.decode().catch(() => {})))")
            out = OUT / "scenes" / f"v4{name}"
            n = shoot_seek(p, out, dur, acts) if name in SEEK else shoot(p, out, dur, acts)
            p.close()
            print(f"{name}: {dur}s・{n} コマ")
        browser.close()
    seq = OUT / "all4"
    shutil.rmtree(seq, ignore_errors=True)
    seq.mkdir()
    k, t, hits = 0, 0.0, []
    for name in ORDER:
        hits.append(t)
        for f in sorted((OUT / "scenes" / f"v4{name}").glob("[0-9]*.png")):
            (seq / f"{k:05d}.png").hardlink_to(f)
            k += 1
        t = k / 30
    wav = OUT / "music4.wav"
    bgm(wav, t, hits[1:])
    ffmpeg(seq, wav, MP4)
    print(f"書き出しました：{MP4.relative_to(ROOT)}（{t:.1f}秒）")


if __name__ == "__main__":
    main()
