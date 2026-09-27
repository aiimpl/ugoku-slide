"""紹介動画の BGM（26秒・120BPM）を NumPy で1サンプルずつ作る。

場面の切り替わりはすべて拍の上（0.5秒刻み）にそろえてある。
  0.0–1.5  くすんだ和音（いつものスライド）
  1.5      「もう、飽きた。」で一撃 → 無音 → 2.0 から上がっていく音
  2.5–19   キック・手拍子・ハイハット・ベース（7–14 はハイハットを細かく）
  19–22    キックを抜いて、打鍵の音
  22–26    もう一度一撃から締め、最後の1秒で消える
"""
import wave

import numpy as np

SR = 44100
BPM = 120
BEAT = 60 / BPM
LEN = 26.0
rng = np.random.default_rng(20261001)


def env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def add(buf, t, x, gain=1.0):
    i = int(t * SR)
    x = x[: max(0, len(buf) - i)]
    buf[i:i + len(x)] += x * gain


def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t / 0.035)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.16)


def noise(n):
    return rng.standard_normal(n)


def hat(d=0.03):
    n = int(0.12 * SR)
    x = np.diff(noise(n + 1))  # 高い音だけ残す
    return x * env(n, 0.0005, d) * 0.35


def clap():
    n = int(0.3 * SR)
    x = np.diff(noise(n + 1)) * 0.5 + noise(n) * 0.3
    e = sum(env(n, 0.0008, 0.012) * (np.arange(n) >= int(k * SR)) for k in (0, 0.011, 0.022))
    return x * (e * 0.6 + env(n, 0.001, 0.09) * 0.5)


def lowpass(x, a):
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc)
        y[i] = acc
    return y


def saw(freq, dur, detune=0.0):
    t = np.arange(int(dur * SR)) / SR
    out = 0
    for dt in (-detune, 0, detune):
        ph = (t * freq * (1 + dt)) % 1
        out = out + (2 * ph - 1)
    return out / 3


def bass(freq, dur):
    x = saw(freq, dur, 0.004) + 0.6 * np.sin(2 * np.pi * freq * np.arange(int(dur * SR)) / SR)
    return lowpass(x, 0.06) * env(len(x), 0.004, dur * 0.8)


def pad(freqs, dur, bright=0.03):
    n = int(dur * SR)
    x = sum(saw(f, dur, 0.006) for f in freqs) / len(freqs)
    a = np.minimum(1, np.arange(n) / (0.25 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.3 * SR))
    return lowpass(x, bright) * a


def riser(dur):
    n = int(dur * SR)
    k = np.linspace(0, 1, n)
    x = noise(n)
    y = np.empty(n)
    acc = 0.0
    for i in range(n):  # だんだん明るくなるノイズ
        acc += (0.02 + 0.5 * k[i] ** 2) * (x[i] - acc)
        y[i] = acc
    return y * k ** 2


def impact():
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    f = 40 + 90 * np.exp(-t / 0.06)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.45)
    return boom + lowpass(noise(n), 0.2) * env(n, 0.001, 0.25) * 0.6


def click():
    n = int(0.03 * SR)
    return np.diff(noise(n + 1)) * env(n, 0.0003, 0.006) * 0.5


# A・F・C・G（1小節＝4拍ずつ）
ROOTS = [55.0, 43.65, 65.41, 49.0]
CHORDS = [[220, 261.6, 329.6], [174.6, 220, 261.6], [196, 261.6, 329.6], [196, 246.9, 293.7]]


def build():
    L = np.zeros(int(LEN * SR))
    R = np.zeros(int(LEN * SR))
    both = lambda t, x, g=1.0, pan=0.0: (add(L, t, x, g * (1 - pan)), add(R, t, x, g * (1 + pan)))

    # 0–1.5 くすんだ和音と、小さな時計の音
    both(0, pad([110, 130.8, 164.8], 1.55, 0.012), 0.35)
    for b in range(3):
        both(b * BEAT, hat(0.015), 0.5)
    # 1.5 一撃、2.0–2.5 上がっていく
    both(1.5, impact(), 0.9)
    both(2.0, riser(0.5), 0.35)

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

    groove(2.5, 7.0)
    both(6.0, riser(1.0), 0.3)
    both(7.0, impact(), 0.5)
    groove(7.0, 14.0, fine=True)
    groove(14.0, 19.0)
    # 19–22 キックを抜いて、打鍵
    groove(19.0, 22.0, drums=False)
    for t in np.sort(19.3 + rng.uniform(0, 1.6, 34)):
        both(float(t), click(), 0.6, float(rng.uniform(-0.3, 0.3)))
    both(21.1, clap(), 0.4)
    both(21.5, riser(0.5), 0.35)
    # 22– 締め
    both(22.0, impact(), 0.9)
    groove(22.0, 25.5)
    both(25.5, pad(CHORDS[0], 0.5, 0.05), 0.2)

    st = np.stack([L, R], 1)
    fade = np.ones(len(st))
    n = int(1.0 * SR)
    fade[-n:] = np.linspace(1, 0, n)
    st *= fade[:, None]
    st = np.tanh(st * 1.1)  # 軽く丸める
    return st / np.abs(st).max() * 0.7  # AAC にしても割れないよう -3dB 下げる


def write(path):
    st = build()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    import sys
    write(sys.argv[1] if len(sys.argv) > 1 else "music.wav")
