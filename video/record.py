"""ページの時間をゆっくり進めながら1コマずつ撮る。

CSS のアニメーションは DevTools の Animation.setPlaybackRate で、JavaScript の動き（数字のカウントなど）は
performance.now の置き換えで、同じ割合だけ遅くする。撮れたコマを 30fps の時刻に割り当てれば、
撮影に時間がかかっても、なめらかで正しい速さの動画になる。
"""
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FX_JS = (HERE / "fx.js").read_text()
FX_CSS = (HERE / "fx.css").read_text()
FONT = "https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@500;700;900&family=Inter:wght@600;800;900&display=swap"
W, H, FPS = 1920, 1080, 30

# performance.now を「割合 rate で進む時計」に置き換える（ページのスクリプトより先に入れる）
CLOCK_JS = """(() => {
  const real = performance.now.bind(performance);
  let last = real(), virt = last, rate = 1;
  performance.now = () => { const r = real(); virt += (r - last) * rate; last = r; return virt; };
  window.__setRate = x => { performance.now(); rate = x; };
})();"""


def open_page(browser):
    page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
    page.set_default_timeout(90000)
    page.add_init_script(CLOCK_JS)
    return page


def prepare(page, url, settle=1.5, chip=True):
    """ページを開き、フォントと演出の部品を入れて、表示が落ち着くまで待つ"""
    page.goto(url, wait_until="domcontentloaded")
    page.add_style_tag(url=FONT)
    page.add_style_tag(content=FX_CSS)
    page.add_script_tag(content=FX_JS)
    page.evaluate("document.fonts.ready")
    if chip:
        page.evaluate("V.chip('<i></i>動くスライド 50選<b>無料</b>')")
    page.wait_for_timeout(int(settle * 1000))


def shoot(page, out_dir, duration, actions=(), rate=0.12):
    """duration 秒ぶんを撮って、30fps のコマを out_dir/00000.png… に書き出す。

    actions は [(秒, "JavaScript"), ...]。その時刻になったらページで実行する。
    返り値は書き出したコマ数。
    """
    out_dir = Path(out_dir)
    raw = out_dir / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    for p in [*raw.glob("*.png"), *out_dir.glob("[0-9]*.png")]:  # 前回のコマを残さない
        p.unlink()
    cdp = page.context.new_cdp_session(page)
    cdp.send("Animation.enable")
    acts = sorted(actions, key=lambda a: a[0])
    # 「0秒」の状態を先に作ってから時計を遅くする
    def run(js):  # 演出の終わりを待たない
        page.evaluate("() => { " + js + "; }")
    while acts and acts[0][0] <= 0:
        run(acts.pop(0)[1])
    cdp.send("Animation.setPlaybackRate", {"playbackRate": rate})
    page.evaluate(f"window.__setRate({rate})")
    shots = []
    t0 = time.perf_counter()
    while True:
        vt = (time.perf_counter() - t0) * rate
        while acts and acts[0][0] <= vt:
            run(acts.pop(0)[1])
        if vt > duration:
            break
        path = raw / f"{len(shots):05d}.png"
        page.screenshot(path=str(path))
        shots.append((vt, path))
    cdp.send("Animation.setPlaybackRate", {"playbackRate": 1})
    page.evaluate("window.__setRate(1)")
    # 30fps の各時刻に、その時刻までに撮れた最後のコマを割り当てる
    n = int(round(duration * FPS))
    j = 0
    for k in range(n):
        t = k / FPS
        while j + 1 < len(shots) and shots[j + 1][0] <= t:
            j += 1
        dst = out_dir / f"{k:05d}.png"
        if dst.exists():
            dst.unlink()
        dst.hardlink_to(shots[j][1])
    return n
