"""紹介動画（1920×1080・30fps・26秒・音つき）を作る。

  python3 video/make_video.py            全部作って build/video/ugoku-slide_26s.mp4 に
  python3 video/make_video.py s2 s5a     指定した場面だけ撮り直して、つなぎ直す

先に make build で docs/ を書き出しておくこと。要 playwright・Pillow・NumPy・ffmpeg。
"""
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import music  # noqa: E402
import stages  # noqa: E402
from record import open_page, prepare, shoot  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs" / "slides"
OUT = ROOT / "build" / "video"
COV = OUT / "covers"
MP4 = OUT / "ugoku-slide_26s.mp4"

MONTAGE = ["04-keynote", "05-neobrutal", "18-wa-modern", "13-cyber", "25-y2k", "32-botanical", "22-bauhaus", "34-oversized",
           "12-synthwave", "42-chalkboard", "24-artdeco", "38-dashboard", "19-dentou", "21-riso", "40-magazine", "27-vapor"]


def deck(name, slide):
    return (DOCS / f"{name}.html").resolve().as_uri() + f"?embed#{slide}"


def covers(browser):
    """50本の表紙を撮る（全画面の PNG と、壁用の小さい JPEG）"""
    COV.mkdir(parents=True, exist_ok=True)
    page = open_page(browser)
    for f in sorted(DOCS.glob("*.html")):
        png = COV / f"{f.stem}.png"
        if not png.exists():
            page.goto(f.resolve().as_uri() + "?embed#1", wait_until="domcontentloaded")
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(1800)
            page.screenshot(path=str(png))
        jpg = COV / f"{f.stem}.jpg"
        if not jpg.exists():
            Image.open(png).convert("RGB").resize((480, 270), Image.LANCZOS).save(jpg, quality=92)
    page.close()
    return sorted(p.stem for p in COV.glob("*.png"))


def stage_page(browser, name, html):
    path = OUT / f"{name}.html"
    path.write_text(html)
    page = open_page(browser)
    page.goto(path.as_uri(), wait_until="domcontentloaded")
    page.add_style_tag(url="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@500;700;900&family=Inter:wght@600;800;900&display=swap")
    page.evaluate("document.fonts.ready")
    page.evaluate("document.getAnimations().forEach(a => { a.pause(); a.currentTime = 0; })")
    return page


# 撮り始めの瞬間に、場面の動きを頭から始める
RESET = "document.getAnimations().forEach(a => { a.currentTime = 0; a.play(); }); window.T0 = performance.now()"


# 場面：名前 → (秒, 撮り方)
def scenes(names):
    rel = lambda n, ext="png": f"covers/{n}.{ext}"
    S = {}

    def s1(b):
        p = stage_page(b, "s1", stages.bland())
        return p, 2.5, [(0, RESET)]
    S["s1"] = s1

    def s2(b):
        p = open_page(b)
        prepare(p, deck("01-swiss", 4))
        return p, 4.5, [
            (0, "V.cap('動かすと、その場で<em>再計算</em>。')"), (0.05, "V.from(1800,980)"),
            (0.15, "V.drag('.slide.active input[name=growth]', 58, 0.9)"),
            (1.45, "V.drag('.slide.active input[name=growth]', 16, 0.8)"),
            (2.55, "V.cap('押すと、<em>根拠</em>が開く。')"),
            (2.6, "V.move('.slide.active details.why summary', 0.4)"),
            (3.1, "V.click('.slide.active details.why summary')"),
            (3.6, "V.move([1500, 900], 0.5)"),
        ]
    S["s2"] = s2

    def s3(b):
        return stage_page(b, "s3", stages.montage([rel(n) for n in MONTAGE])), 4.0, [(0, RESET)]
    S["s3"] = s3

    def s4(b):
        return stage_page(b, "s4", stages.wall([rel(n, "jpg") for n in ALL], rel(ALL[0]))), 3.0, [(0, RESET)]
    S["s4"] = s4

    def s5a(b):
        p = open_page(b)
        prepare(p, deck("08-aurora", 4))
        # 1位が入れ替わる動かし方（スライダー2本まで）を探しておく
        moves = p.evaluate("""() => {
          const s = document.querySelector('.slide.active');
          const top = () => s.querySelector('.rank .opt.top .name').textContent;
          const ins = [...s.querySelectorAll('.rank input')], t0 = top();
          const set = (i, v) => { ins[i].value = v; ins[i].dispatchEvent(new Event('input', {bubbles: true})); };
          const old = ins.map(x => x.value), back = () => ins.forEach((x, i) => set(i, old[i]));
          for (let i = 0; i < ins.length; i++) for (const v of [5, 0]) {
            set(i, v); const t = top(); back(); if (t !== t0) return [[i + 1, v]];
          }
          for (let i = 0; i < ins.length; i++) for (let j = 0; j < ins.length; j++) if (i !== j) {
            set(i, 5); set(j, 0); const t = top(); back(); if (t !== t0) return [[i + 1, 5], [j + 1, 0]];
          }
          return [[1, 0]]; }""")
        p.wait_for_timeout(900)
        sel = lambda k: f".slide.active .rank .field:nth-child({k}) input"
        acts = [(0, "V.cap('重みで、<em>順位が入れ替わる</em>。')"), (0.02, "V.from(1700,1000)")]
        for n, (k, v) in enumerate(moves):
            acts.append((0.08 + n * 0.45, f"V.drag('{sel(k)}', {v}, 0.35)"))
        return p, 1.4, acts
    S["s5a"] = s5a

    def s5b(b):
        p = open_page(b)
        prepare(p, deck("10-clay", 3))
        btn = "document.querySelector('.slide.active .quiz .choices > button[data-correct]')"
        return p, 1.2, [(0, "V.cap('答えると、<em>正解が開く</em>。')"), (0.02, "V.from(1750,1000)"),
                        (0.08, f"V.move({btn}, 0.4)"), (0.55, f"V.click({btn})")]
    S["s5b"] = s5b

    def s5c(b):
        p = open_page(b)
        prepare(p, deck("19-dentou", 5))
        tab = lambda i: f"document.querySelectorAll('.slide.active [data-tab]')[{i}]"
        return p, 1.2, [(0, "V.cap('押すと、<em>切り替わる</em>。')"), (0.02, "V.from(1500,1000)"),
                        (0.06, f"V.move({tab(1)}, 0.3)"), (0.4, f"V.click({tab(1)})"),
                        (0.5, f"V.move({tab(2)}, 0.25)"), (0.8, f"V.click({tab(2)})")]
    S["s5c"] = s5c

    def s5d(b):
        p = open_page(b)
        prepare(p, deck("14-terminal", 2), settle=0.3)
        # URL の #3 で開くと強調が最後まで進んだ状態になるので、前のページから → で入る
        p.keyboard.press("End"); p.keyboard.press("Home")
        p.evaluate("location.hash = '#2'"); p.wait_for_timeout(300); p.keyboard.press("ArrowRight")
        p.wait_for_timeout(1500)
        return p, 1.2, [(0, "V.cap('→ キーで、<em>1行ずつ</em>。')"),
                        (0.15, "V.key('ArrowRight')"), (0.55, "V.key('ArrowRight')"), (0.95, "V.key('ArrowRight')")]
    S["s5d"] = s5d

    def s6(b):
        p = stage_page(b, "s6", stages.ask([rel(n, "jpg") for n in ALL[:36]]))
        p.add_script_tag(content=(ROOT / "video" / "fx.js").read_text())
        p.add_style_tag(content=(ROOT / "video" / "fx.css").read_text())
        return p, 3.0, [(0, RESET),
                        (0.3, f"V.type('#txt', {stages.PROMPT!r}, 1.6)"), (0.05, "V.from(1700,1000)"),
                        (1.95, "V.move('#send', 0.3)"), (2.3, "V.click('#send'); document.getElementById('send').classList.add('go')")]
    S["s6"] = s6

    def s7(b):
        p = stage_page(b, "s7", stages.end([rel(n, "jpg") for n in ALL[:48]]))
        return p, 4.0, [(0, RESET)]
    S["s7"] = s7

    return [(n, S[n]) for n in names]


ORDER = ["s1", "s2", "s3", "s4", "s5a", "s5b", "s5c", "s5d", "s6", "s7"]
ALL = []


def ffmpeg(frames, wav, out):
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-i", str(frames / "%05d.png"), "-i", str(wav),
        "-vf", "scale=in_range=pc:out_range=tv,format=yuv420p", "-pix_fmt", "yuv420p", "-color_range", "tv",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "17",
        "-af", "alimiter=limit=0.7:level=false", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(out)], check=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1:] or ORDER
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = pw.chromium.launch(headless=True)
        ALL[:] = covers(browser)
        for name, make in scenes([n for n in ORDER if n in only]):
            page, dur, acts = make(browser)
            n = shoot(page, OUT / "scenes" / name, dur, acts)
            page.close()
            print(f"{name}: {dur}s・{n} コマ")
        browser.close()
    # つなぐ
    seq = OUT / "all"
    shutil.rmtree(seq, ignore_errors=True)
    seq.mkdir()
    k = 0
    for name in ORDER:
        for f in sorted((OUT / "scenes" / name).glob("[0-9]*.png")):
            (seq / f"{k:05d}.png").hardlink_to(f)
            k += 1
    print(f"合計 {k} コマ（{k / 30:.1f} 秒）")
    wav = OUT / "music.wav"
    music.write(wav)
    ffmpeg(seq, wav, MP4)
    print(f"書き出しました：{MP4.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
