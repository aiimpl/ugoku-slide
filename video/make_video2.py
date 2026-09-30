"""第2弾の紹介動画（1920×1080・30fps・26.5秒・音つき）を作る。

  python3 video/make_video2.py            全部作って build/video/ugoku-slide-vol2_26s.mp4 に
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
from make_video import OUT, covers, deck, ffmpeg  # noqa: E402
from make_video import stage_page as _stage_page  # noqa: E402
from record import FPS, open_page, prepare, shoot  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MP4 = OUT / "ugoku-slide-vol2_26s.mp4"
HOOK = OUT / "hook"  # 冒頭の「いつものスライド」側の2枚（51 の1・2枚目の画像）
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


# 冒頭：左に「いつものスライド」（画像がパッと切り替わる）、右に本物のスライド（変形してつながる）
HOOK_CSS = """
body.embed{background:#0d0e11!important}
.deck{left:1410px!important;top:596px!important;transform:translate(-50%,-50%) scale(.65625)!important;border-radius:6px;
  box-shadow:0 0 0 3px #ff5a36,0 40px 90px -30px rgb(0 0 0 / .8)}
#hook{position:fixed;inset:0;z-index:5;pointer-events:none;font-family:"Noto Sans JP","Hiragino Sans",sans-serif;font-feature-settings:"palt" 1}
#hook .pane{position:absolute;left:90px;top:360px;width:840px;height:472.5px;border-radius:6px;overflow:hidden;box-shadow:0 0 0 1px rgb(255 255 255 / .12)}
#hook .pane img{position:absolute;inset:0;width:100%;height:100%;filter:saturate(.55) brightness(.8)}
#hook .pane .b{opacity:0;animation:cut .01s linear 1s forwards}
@keyframes cut{to{opacity:1}}
#hook h1{position:absolute;left:90px;top:64px;margin:0;color:#fff;font-weight:900;font-size:84px;letter-spacing:-.02em;line-height:1.2}
#hook h1 em{font-style:normal;color:#ff5a36}
#hook .lab{position:absolute;top:296px;font-weight:900;font-size:40px;color:#9a9ea7}
#hook .lab.r{left:990px;color:#ff5a36}
#hook .sub{position:absolute;top:862px;font-weight:700;font-size:34px;color:rgb(255 255 255 / .75);opacity:0;animation:up .4s cubic-bezier(.2,.9,.2,1) 1.35s forwards}
#hook .sub.r{left:990px;color:#fff}
@keyframes up{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
"""


# 1コマずつ時刻を決めて撮る（動きを止めたまま、アニメーションと時計をその時刻に合わせる）。
# 背景に画像が多い場面では、時計をゆっくり進める撮り方だと動きが止まることがあったため。
SEEK_JS = """(t) => {
  window.__setVirt(window.__v0 + t * 1000);
  document.getAnimations().forEach(a => {
    if (a.__t0 === undefined) { a.__t0 = t; a.pause(); }
    a.currentTime = (t - a.__t0) * 1000;
  });
}"""


def shoot_seek(page, out_dir, duration, actions=()):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in out_dir.rglob("*.png"):
        p.unlink()
    page.evaluate("window.__v0 = performance.now(); document.getAnimations().forEach(a => { a.pause(); a.__t0 = 0; })")
    acts = sorted(actions, key=lambda a: a[0])
    n = int(round(duration * FPS))
    for k in range(n):
        t = k / FPS
        while acts and acts[0][0] <= t + 1e-9:
            page.evaluate("() => { " + acts.pop(0)[1] + "; }")
        page.evaluate(SEEK_JS, t)
        page.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
        page.screenshot(path=str(out_dir / f"{k:05d}.png"))
    return n


def stage_page(browser, name, html):
    """場面の HTML を開き、画像の読み込みと文字の準備を待ってから、動きを頭で止めておく
    （読み込み中に撮り始めると、動きが遅れて始まったり止まったりする）"""
    p = _stage_page(browser, name, html)
    p.evaluate("Promise.all([...document.images].map(i => i.decode().catch(() => {})))")
    p.evaluate("document.fonts.ready")
    p.wait_for_timeout(500)
    p.evaluate("document.getAnimations().forEach(a => { a.pause(); a.currentTime = 0; })")
    return p


def hook_shots(browser):
    """冒頭の左側に使う、51 の1・2枚目の画像を撮る"""
    HOOK.mkdir(parents=True, exist_ok=True)
    p = browser.new_page(viewport={"width": 1280, "height": 720})
    p.goto(deck("51-onetake", 1), wait_until="domcontentloaded")
    p.evaluate("document.fonts.ready")
    p.wait_for_timeout(2500)
    p.screenshot(path=str(HOOK / "s1.png"))
    # 2枚目は右と同じく「めくった直後」（→ で出す行はまだ出ていない）
    p.keyboard.press("ArrowRight")
    p.wait_for_timeout(2500)
    p.screenshot(path=str(HOOK / "s2.png"))
    p.close()


def hook_page(browser):
    p = open_page(browser)
    prepare(p, deck("51-onetake", 1), chip=False)
    p.add_style_tag(content=HOOK_CSS)
    a, b = (HOOK / "s1.png").as_uri(), (HOOK / "s2.png").as_uri()
    p.evaluate(f"""() => {{ const h = document.createElement('div'); h.id = 'hook';
      h.innerHTML = `<h1>同じ2枚でも、<br>めくった瞬間が<em>ちがう。</em></h1>
        <div class="lab" style="left:90px">いつものスライド</div><div class="lab r">動くスライド</div>
        <div class="pane"><img src="{a}"><img class="b" src="{b}"></div>
        <div class="sub" style="left:90px">パッと切り替わるだけ</div><div class="sub r">丸が、次の図へつながる</div>`;
      document.body.appendChild(h); }}""")
    p.evaluate(CHIP)
    p.wait_for_timeout(800)
    return p


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

    def v0(b):  # 同じ2枚でも、めくった瞬間がちがう
        return hook_page(b), 2.5, [(0, "document.getAnimations().forEach(a => { a.currentTime = 0; a.play(); })"),
                                   (1.0, "V.key('ArrowRight')")]
    S["v0"] = v0

    def v1(b):  # めくっても、途切れない
        p = slide(b, "51-onetake", 2)
        return p, 3.0, [(0, "V.cap('めくっても、<em>途切れない。</em>')"), (0.4, "V.key('ArrowRight')"),
                        (1.4, "V.key('ArrowRight')"), (1.9, "V.key('ArrowRight')"), (2.4, "V.key('ArrowRight')")]
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


ORDER = ["v0", "v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8"]
SEEK = {"v6", "v7", "v8"}  # 画像を並べた場面は、1コマずつ時刻を決めて撮る


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1:] or ORDER
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = pw.chromium.launch(headless=True)
        ids = covers(browser)
        if "v0" in only:
            hook_shots(browser)
        for name, make in scenes([n for n in ORDER if n in only], ids):
            page, dur, acts = make(browser)
            if name in SEEK:
                acts = [x for x in acts if "getAnimations" not in x[1]]  # 頭出しは shoot_seek がする
                n = shoot_seek(page, OUT / "scenes" / name, dur, acts)
            else:
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
