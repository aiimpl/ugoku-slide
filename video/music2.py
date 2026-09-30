"""第2弾の紹介動画の BGM（26.5秒・120BPM）。音の部品は music.py と同じものを使う。

場面の切り替わりはすべて拍の上（0.5秒刻み）にそろえてある。
  0.0–2.5  冒頭の比べっこ：静かな和音。1.0 で左は「カチッ」と切り替わり、右は「すっ」と変形する音
  2.5–9.5  ビート（丸が形を変えていく）。2.9 / 5.8 / 7.9 のページ送りに「すっ」
  9.5–15.5 ハイハットを細かく（立体・表を貼る）
  15.5–20.5 ビート。18.0 で小さな一撃（62本の壁）
  20.5–23.5 キックを抜いて、打鍵の音（スキルに頼む）
  23.5– 締め、最後の1秒で消える
"""
import wave

import numpy as np

import music
from music import BEAT, SR, add, bass, clap, click, env, hat, impact, kick, lowpass, noise, pad, riser

LEN = 26.5
rng = np.random.default_rng(20261002)
ROOTS = [55.0, 43.65, 65.41, 49.0]
CHORDS = [[220, 261.6, 329.6], [174.6, 220, 261.6], [196, 261.6, 329.6], [196, 246.9, 293.7]]


def swoosh(dur=0.45):
    """変形に合わせた、明るくなって消えるノイズ"""
    n = int(dur * SR)
    k = np.linspace(0, 1, n)
    x = lowpass(noise(n), 0.08) * np.sin(np.pi * k) ** 2
    return x * env(n, 0.05, dur)


def build():
    L = np.zeros(int(LEN * SR))
    R = np.zeros(int(LEN * SR))
    both = lambda t, x, g=1.0, pan=0.0: (add(L, t, x, g * (1 - pan)), add(R, t, x, g * (1 + pan)))

    both(0, pad([110, 164.8, 220], 2.5, 0.02), 0.3)
    for b in range(5):
        both(b * BEAT, hat(0.015), 0.45)
    both(1.0, click(), 1.2, -0.5)       # 左：パッと切り替わる
    both(1.0, swoosh(0.6), 0.6, 0.4)    # 右：変形する
    both(2.0, riser(0.5), 0.35)
    both(2.5, impact(), 0.6)
    for t in (2.9, 5.8, 7.9):
        both(t, swoosh(), 0.55, 0.2 if t > 5 else -0.2)

    def groove(t0, t1, fine=False, drums=True):
        b = t0
        while b < t1 - 1e-6:
            k = int(round(b / BEAT))
            bar = (k // 4) % 4
            if drums:
                both(b, kick(), 0.95)
                if k % 2 == 1:
                    both(b, clap(), 0.5)
            step = BEAT / 4 if fine else BEAT / 2
            for j in range(int(BEAT / step)):
                both(b + j * step, hat(0.02 if j % 2 else 0.035), 0.55, 0.3 if j % 2 else -0.3)
            for j in range(2):
                both(b + j * BEAT / 2, bass(ROOTS[bar], BEAT / 2 * 0.9), 0.42)
            if k % 4 == 0:
                both(b, pad(CHORDS[bar], BEAT * 4, 0.05), 0.16)
            b += BEAT

    groove(2.5, 9.5)
    both(8.5, riser(1.0), 0.3)
    both(9.5, impact(), 0.5)
    groove(9.5, 15.5, fine=True)
    groove(15.5, 20.5)
    both(17.5, riser(0.5), 0.3)
    both(18.0, impact(), 0.45)
    groove(20.5, 23.5, drums=False)
    for t in np.sort(20.9 + rng.uniform(0, 1.5, 34)):
        both(float(t), click(), 0.6, float(rng.uniform(-0.3, 0.3)))
    both(22.6, clap(), 0.4)
    both(23.0, riser(0.5), 0.35)
    both(23.5, impact(), 0.9)
    groove(23.5, 26.0)
    both(26.0, pad(CHORDS[0], 0.5, 0.05), 0.2)

    st = np.stack([L, R], 1)
    fade = np.ones(len(st))
    n = int(1.0 * SR)
    fade[-n:] = np.linspace(1, 0, n)
    st *= fade[:, None]
    st = np.tanh(st * 1.1)
    return st / np.abs(st).max() * 0.7


def write(path):
    st = build()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype("<i2").tobytes())


assert music.BPM == 120  # 拍の長さは music.py と同じ

if __name__ == "__main__":
    import sys
    write(sys.argv[1] if len(sys.argv) > 1 else "music2.wav")
