"""新しい操作を見せる短い動画を作る（1920×1080・30fps・音つき）。

  python3 video/make_clips.py          2本とも作る
  python3 video/make_clips.py mark     「囲んで直す（E）」だけ
  python3 video/make_clips.py demo     「自動デモ（D）」だけ

書き出し先：build/video/clip_mark.mp4・clip_demo.mp4
撮り方は make_video2.py と同じ（スライドを少し小さくして、下の帯にテロップ）。
"""
import shutil
import sys
import wave
from pathlib import Path

import numpy as np
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import music  # noqa: E402
import stages2  # noqa: E402
from make_video import OUT, covers, ffmpeg  # noqa: E402
from make_video2 import shoot_seek, slide, stage_page  # noqa: E402
from record import shoot  # noqa: E402
from stages import CHIP_CSS, page  # noqa: E402

rel = lambda n: f"covers/{n}.jpg"


# ---------- 貼る場面：Claude の入力欄に、コピーした指示が入る ----------
MARK_TEXT = ("次の直しをお願いします（動くスライド。座標は 1280×720 のスライドの中の px）\n"
             "1. 4枚目「収益モデル」の x=846 y=196 幅360 高さ108（中の文字：「3年目の年間売上」「19.1億円」）：数字をもっと大きく")


def chat(bg):
    css = CHIP_CSS + """
body{background:#f6f5f1}
.bgw{position:absolute;inset:-40px;display:grid;grid-template-columns:repeat(6,1fr);gap:18px;opacity:.14;transform:rotate(-6deg) scale(1.15);filter:blur(1px)}
.bgw img{width:100%;border-radius:6px}
.box{position:absolute;left:230px;right:230px;top:300px;background:#fff;border-radius:28px;padding:34px 44px 30px;
  box-shadow:0 40px 90px -30px rgb(0 0 0 / .35),0 0 0 1px rgb(0 0 0 / .06);animation:rise .5s cubic-bezier(.2,.9,.2,1) both}
.txt{min-height:230px;font-size:32px;line-height:1.6;font-weight:700;color:#16171b;white-space:pre-wrap}
.txt::after{content:"";display:inline-block;width:4px;height:36px;background:#ff5a36;vertical-align:-6px;margin-left:4px}
.hint{font-size:22px;color:#8a8d94;font-weight:700;margin-top:10px}
.scap{top:120px;bottom:auto;left:50%;transform:translateX(-50%);white-space:nowrap;animation:rise2 .45s cubic-bezier(.2,.9,.2,1) .1s both}
@keyframes rise2{from{opacity:0;transform:translate(-50%,30px)}to{opacity:1;transform:translateX(-50%)}}
"""
    body = (f'<div class="bgw">{"".join(f"<img src={c!r}>" for c in bg)}</div>{stages2.CHIP}'
            '<div class="scap">コピーして、<em>Claude に貼るだけ。</em></div>'
            '<div class="box"><div class="txt" id="txt"></div><div class="hint">何枚目のどこか、中の文字まで伝わる</div></div>')
    return page(css, body)


def scenes(names, ids):
    S = {}

    def mark1(b):  # 囲んで、一言書いて、コピー
        p = slide(b, "51-onetake", 4)
        # 指示の一覧は、動画では読めるように大きく
        p.add_style_tag(content=".ugk-markpanel{top:40px;right:40px;width:420px;transform:scale(1.5);transform-origin:top right}")
        return p, 6.0, [(0, "V.cap('直したい所を、<em>囲むだけ。</em>')"), (0.05, "V.from(1700,1000)"),
                        (0.5, "V.key('e')"), (1.0, "V.box(846, 196, 1206, 304, 0.9)"),
                        (2.3, "V.fill('.ugk-markpanel input', '数字をもっと大きく', 1.1)"),
                        (3.6, "document.querySelector('.ugk-ask').requestSubmit()"),
                        (4.2, "V.move('.ugk-markpanel [data-m=copy]', 0.5)"), (4.8, "V.click('.ugk-markpanel [data-m=copy]')")]
    S["mark1"] = mark1

    def mark2(b):
        p = stage_page(b, "mark2", chat([rel(n) for n in ids[:36]]))
        p.add_script_tag(content=(OUT.parent.parent / "video" / "fx.js").read_text())
        p.add_style_tag(content=(OUT.parent.parent / "video" / "fx.css").read_text())
        return p, 4.0, [(0.3, f"V.type('#txt', {MARK_TEXT!r}, 2.4)")]
    S["mark2"] = mark2

    def mark3(b):  # 直った（数字が大きくなる）
        p = slide(b, "51-onetake", 4)
        p.add_style_tag(content=".model .readout .value{transition:font-size .6s cubic-bezier(.2,.8,.2,1)}.big-now .model .readout .value{font-size:104px}")
        return p, 4.0, [(0, "V.cap('場所が伝わるから、<em>直すのも早い。</em>')"), (0.9, "document.body.classList.add('big-now')")]
    S["mark3"] = mark3

    def demo1(b):  # D で自動デモ
        p = slide(b, "53-exploded", 1)
        return p, 15.0, [(0, "V.cap('D を押すと、<em>勝手にプレゼンする。</em>')"), (0.4, "V.key('d')"),
                         (7.0, "V.cap('つまみも立体も、<em>自分で動かして見せる。</em>')")]
    S["demo1"] = demo1

    def end(b):
        return stage_page(b, "clip_end", stages2.end([rel(n) for n in ids[-48:]])), 3.0, []
    S["end"] = end
    return [(n, S[n]) for n in names]


CLIPS = {"mark": ["mark1", "mark2", "mark3", "end"], "demo": ["demo1", "end"]}
SEEK = {"mark2", "end"}  # 画像を並べた場面は1コマずつ時刻を決めて撮る


def bgm(path, length, hits):
    """短い動画の BGM（120BPM のビート。hits の秒で一撃）"""
    L = np.zeros(int(length * music.SR))
    both = lambda t, x, g=1.0: music.add(L, t, x, g)
    b = 0.0
    while b < length - 1:
        k = int(round(b / music.BEAT))
        both(b, music.kick(), 0.9)
        if k % 2:
            both(b, music.clap(), 0.45)
        both(b, music.hat(0.03), 0.5)
        both(b + music.BEAT / 2, music.hat(0.02), 0.4)
        both(b, music.bass(music.ROOTS[(k // 4) % 4], music.BEAT * 0.9), 0.4)
        if k % 4 == 0:
            both(b, music.pad(music.CHORDS[(k // 4) % 4], music.BEAT * 4, 0.05), 0.15)
        b += music.BEAT
    for t in hits:
        both(t, music.impact(), 0.6)
    fade = np.ones(len(L))
    fade[-music.SR:] = np.linspace(1, 0, music.SR)
    st = np.tanh(np.stack([L, L], 1) * fade[:, None] * 1.1)
    st = st / np.abs(st).max() * 0.7
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(music.SR)
        w.writeframes((st * 32767).astype("<i2").tobytes())


def main():
    want = sys.argv[1:] or list(CLIPS)
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = pw.chromium.launch(headless=True)
        ids = covers(browser)
        names = [n for c in want for n in CLIPS[c]]
        for name, make in scenes(list(dict.fromkeys(names)), ids):
            p, dur, acts = make(browser)
            n = shoot_seek(p, OUT / "scenes" / name, dur, acts) if name in SEEK else shoot(p, OUT / "scenes" / name, dur, acts)
            p.close()
            print(f"{name}: {dur}s・{n} コマ")
        browser.close()
    for c in want:
        seq = OUT / f"all_{c}"
        shutil.rmtree(seq, ignore_errors=True)
        seq.mkdir()
        k, t, hits = 0, 0.0, []
        for name in CLIPS[c]:
            frames = sorted((OUT / "scenes" / name).glob("[0-9]*.png"))
            hits.append(t)
            for f in frames:
                (seq / f"{k:05d}.png").hardlink_to(f)
                k += 1
            t += len(frames) / 30
        wav = OUT / f"clip_{c}.wav"
        bgm(wav, t, hits[1:])
        mp4 = OUT / f"clip_{c}.mp4"
        ffmpeg(seq, wav, mp4)
        print(f"書き出しました：{mp4.relative_to(OUT.parent.parent)}（{t:.1f}秒）")


if __name__ == "__main__":
    main()
