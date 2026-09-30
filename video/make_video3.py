"""第3弾の紹介動画（1920×1080・30fps・25秒・音つき）を作る。囲んで直す・自動デモ・点検。

  python3 video/make_video3.py            全部作って build/video/ugoku-slide-vol3_25s.mp4 に
  python3 video/make_video3.py q e        指定した場面だけ撮り直して、つなぎ直す

撮り方は make_video2.py と同じ。BGM は make_clips.py の bgm（場面の頭で一撃）。
"""
import shutil
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stages3  # noqa: E402
from make_clips import MARK_TEXT, bgm, chat  # noqa: E402
from make_video import OUT, covers, ffmpeg  # noqa: E402
from make_video2 import shoot_seek, slide, stage_page  # noqa: E402
from record import shoot  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MP4 = OUT / "ugoku-slide-vol3_25s.mp4"
FX = [(ROOT / "video" / "fx.js").read_text(), (ROOT / "video" / "fx.css").read_text()]
rel = lambda n: f"covers/{n}.jpg"


def with_fx(p):
    p.add_script_tag(content=FX[0])
    p.add_style_tag(content=FX[1])
    return p


def scenes(names, ids):
    S = {}

    def h(b):  # 直す場所を、言葉で説明している
        p = with_fx(stage_page(b, "v3h", stages3.hook()))
        return p, 3.0, [(0.1, f"V.type('#txt', {stages3.HOOK_TEXT!r}, 1.8)")]
    S["h"] = h

    def m(b):  # E で囲んで、一言書いて、コピー
        p = slide(b, "51-onetake", 4, chip=stages3.CHIP_JS)
        # 指示の一覧は大きくし、直す数字を隠さないよう左下（つまみの下）に出す
        p.add_style_tag(content=".ugk-markpanel{top:auto;right:auto;left:170px;bottom:250px;width:420px;transform:scale(1.5);transform-origin:bottom left}")
        return p, 6.0, [(0, "V.cap('E で囲んで、<em>一言書くだけ。</em>')"), (0.05, "V.from(1700,1000)"),
                        (0.5, "V.key('e')"), (1.0, "V.box(846, 196, 1206, 304, 0.9)"),
                        (2.3, "V.fill('.ugk-markpanel input', '数字をもっと大きく', 1.1)"),
                        (3.6, "document.querySelector('.ugk-ask').requestSubmit()"),
                        (4.2, "V.move('.ugk-markpanel [data-m=copy]', 0.5)"), (4.8, "V.click('.ugk-markpanel [data-m=copy]')")]
    S["m"] = m

    def c(b):  # Claude に貼る
        html = chat([rel(n) for n in ids[:36]]).replace("コピーして、<em>Claude に貼るだけ。</em>", "Claude に貼れば、<em>場所まで伝わる。</em>")
        html = html.replace("動くスライド 第2弾", "動くスライド 第3弾")
        p = with_fx(stage_page(b, "v3c", html))
        return p, 3.0, [(0.2, f"V.type('#txt', {MARK_TEXT!r}, 2.0)")]
    S["c"] = c

    def d(b):  # D で自動デモ
        p = slide(b, "53-exploded", 1, chip=stages3.CHIP_JS)
        return p, 7.0, [(0, "V.cap('D を押すと、<em>勝手にプレゼン。</em>')"), (0.3, "V.key('d')")]
    S["d"] = d

    def q(b):  # 62本すべてに点検の印
        return stage_page(b, "v3q", stages3.checked([rel(n) for n in ids])), 3.0, []
    S["q"] = q

    def e(b):
        return stage_page(b, "v3e", stages3.end([rel(n) for n in ids[-48:]])), 3.0, []
    S["e"] = e
    return [(n, S[n]) for n in names]


ORDER = ["h", "m", "c", "d", "q", "e"]
SEEK = {"h", "c", "q", "e"}  # スライド以外の場面は1コマずつ時刻を決めて撮る


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
            p, dur, acts = make(browser)
            out = OUT / "scenes" / f"v3{name}"
            n = shoot_seek(p, out, dur, acts) if name in SEEK else shoot(p, out, dur, acts)
            p.close()
            print(f"{name}: {dur}s・{n} コマ")
        browser.close()
    seq = OUT / "all3"
    shutil.rmtree(seq, ignore_errors=True)
    seq.mkdir()
    k, t, hits = 0, 0.0, []
    for name in ORDER:
        hits.append(t)
        for f in sorted((OUT / "scenes" / f"v3{name}").glob("[0-9]*.png")):
            (seq / f"{k:05d}.png").hardlink_to(f)
            k += 1
        t = k / 30
    wav = OUT / "music3.wav"
    bgm(wav, t, hits[1:])
    ffmpeg(seq, wav, MP4)
    print(f"書き出しました：{MP4.relative_to(ROOT)}（{t:.1f}秒）")


if __name__ == "__main__":
    main()
