"""第2弾の紹介動画（1920×1080・30fps・24秒・音つき）を作る。

  python3 video/make_video2.py            全部作って build/video/ugoku-slide-vol2_24s.mp4 に
  python3 video/make_video2.py v3 v4      指定した場面だけ撮り直して、つなぎ直す

先に make build で docs/ を書き出しておくこと。要 playwright・Pillow・NumPy・ffmpeg。
撮り方は make_video.py と同じ（record.py でページの時計を遅くして1コマずつ撮る）。
"""
import shutil
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import music2  # noqa: E402
import stages2  # noqa: E402
from make_video import OUT, covers, deck, ffmpeg, stage_page  # noqa: E402
from record import open_page, prepare, shoot  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MP4 = OUT / "ugoku-slide-vol2_24s.mp4"
CHIP = "V.chip('<i></i>動くスライド 第2弾<b>無料</b>')"
NEW = [f"{n}-" for n in range(51, 63)]

# 表を貼る場面で貼る表（Excel でコピーしたときと同じ、タブ区切り）
PASTE = "月\t売上\n" + "\n".join(f"{m}月\t{v}" for m, v in zip(
    [11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [310, 342, 360, 395, 420, 468, 455, 512, 560, 604, 648, 720]))


# スライドを少し小さくして上に寄せ、下の帯にテロップを置く（テロップがスライドの文字に重ならない）
STAGE_CSS = """
body.embed{background:radial-gradient(1500px 900px at 50% 38%,#1d1e23 0%,#0b0b0d 70%)!important}
.deck{top:calc(50% - 66px)!important;transform:translate(-50%,-50%) scale(calc(var(--scale) * .84))!important;border-radius:8px;
  box-shadow:0 40px 90px -30px rgb(0 0 0 / .8),0 0 0 1px rgb(255 255 255 / .07)}
#vfx .cap{left:154px;bottom:28px;top:auto;padding:0;background:none;box-shadow:none;font-size:62px;letter-spacing:-.01em}
#vfx .chip{top:auto;bottom:44px;right:154px}
"""


def slide(browser, name, n):
    p = open_page(browser)
    prepare(p, deck(name, n), chip=False)
    p.add_style_tag(content=STAGE_CSS)
    p.evaluate(CHIP)
    p.wait_for_timeout(300)
    return p


def scenes(names, all_ids):
    rel = lambda n, ext="png": f"covers/{n}.{ext}"
    S = {}

    def v1(b):  # めくっても、途切れない
        p = slide(b, "51-onetake", 1)
        return p, 3.0, [(0, "V.cap('めくっても、')"),
                        (0.9, "V.key('ArrowRight')"), (1.0, "V.cap('めくっても、<em>途切れない。</em>')"),
                        (2.0, "V.key('ArrowRight')")]
    S["v1"] = v1

    def v2(b):  # 同じ丸が、最後まで形を変える
        p = slide(b, "51-onetake", 3)
        m = "'.slide.active input[name=m]'"
        return p, 4.0, [(0, "V.cap('1つの丸が、<em>最後まで形を変える。</em>')"),
                        (0.3, "V.key('ArrowRight')"), (0.35, "V.from(1700,1010)"),
                        (1.25, f"V.drag({m}, 72000, 0.8)"),
                        (2.4, "V.show(false); V.key('ArrowRight')")]
    S["v2"] = v2

    def v3(b):  # 回して、分解できる
        p = slide(b, "53-exploded", 2)
        p.evaluate("(() => { const i = document.querySelector('.slide.active input[name=x]'); i.value = 0; i.dispatchEvent(new Event('input', {bubbles: true})); })()")
        p.wait_for_timeout(900)
        return p, 3.0, [(0, "V.cap('回して、<em>分解できる。</em>')"), (0.02, "V.from(1750,1000)"),
                        (0.15, "V.drag('.slide.active input[name=x]', 100, 0.9)"),
                        (1.45, "V.orbit('.slide.active [data-orbit]', 300, -60, 1.1)")]
    S["v3"] = v3

    def v4(b):  # Excel の表を、貼るだけ
        p = slide(b, "54-monthly", 3)
        btn = "document.querySelector('.slide.active [data-sheet-paste]')"
        paste = ("(() => { const dt = new DataTransfer(); dt.setData('text/plain', %r);"
                 " const t = document.activeElement && document.activeElement !== document.body ? document.activeElement : document.body;"
                 " t.dispatchEvent(new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true})); })()") % PASTE
        return p, 3.0, [(0, "V.cap('Excelの表を、<em>貼るだけ。</em>')"), (0.02, "V.from(1700,1000)"),
                        (0.1, f"V.move({btn}, 0.45)"), (0.6, f"V.click({btn})"),
                        (1.1, paste), (1.15, "V.move([1500, 950], 0.5)")]
    S["v4"] = v4

    def v5(b):  # つまみで、図そのものが動く
        p = slide(b, "59-breakeven", 4)
        return p, 2.5, [(0, "V.cap('つまみで、<em>図そのものが動く。</em>')"), (0.02, "V.from(1750,1000)"),
                        (0.1, "V.drag('.slide.active input[name=p]', 1750, 0.75)"),
                        (1.15, "V.drag('.slide.active input[name=v]', 1150, 0.75)")]
    S["v5"] = v5

    def v6(b):
        cells = [(i, rel(i, "jpg")) for i in all_ids]
        new = {i for i in all_ids if any(i.startswith(n) for n in NEW)}
        return stage_page(b, "v6", stages2.wall(cells, new)), 2.5, [(0, "document.getAnimations().forEach(a => { a.currentTime = 0; a.play(); })")]
    S["v6"] = v6

    def v7(b):
        p = stage_page(b, "v7", stages2.ask([rel(n, "jpg") for n in all_ids[-36:]]))
        p.add_script_tag(content=(ROOT / "video" / "fx.js").read_text())
        p.add_style_tag(content=(ROOT / "video" / "fx.css").read_text())
        return p, 3.0, [(0, "document.getAnimations().forEach(a => { a.currentTime = 0; a.play(); })"),
                        (0.3, f"V.type('#txt', {stages2.PROMPT!r}, 1.6)"), (0.05, "V.from(1700,1000)"),
                        (1.95, "V.move('#send', 0.3)"), (2.3, "V.click('#send'); document.getElementById('send').classList.add('go')")]
    S["v7"] = v7

    def v8(b):
        p = stage_page(b, "v8", stages2.end([rel(n, "jpg") for n in all_ids[-48:]]))
        return p, 3.0, [(0, "document.getAnimations().forEach(a => { a.currentTime = 0; a.play(); })")]
    S["v8"] = v8

    return [(n, S[n]) for n in names]


ORDER = ["v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1:] or ORDER
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = pw.chromium.launch(headless=True)
        ids = covers(browser)
        for name, make in scenes([n for n in ORDER if n in only], ids):
            page, dur, acts = make(browser)
            n = shoot(page, OUT / "scenes" / name, dur, acts)
            page.close()
            print(f"{name}: {dur}s・{n} コマ")
        browser.close()
    seq = OUT / "all2"
    shutil.rmtree(seq, ignore_errors=True)
    seq.mkdir()
    k = 0
    for name in ORDER:
        for f in sorted((OUT / "scenes" / name).glob("[0-9]*.png")):
            (seq / f"{k:05d}.png").hardlink_to(f)
            k += 1
    print(f"合計 {k} コマ（{k / 30:.1f} 秒）")
    wav = OUT / "music2.wav"
    music2.write(wav)
    ffmpeg(seq, wav, MP4)
    print(f"書き出しました：{MP4.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
