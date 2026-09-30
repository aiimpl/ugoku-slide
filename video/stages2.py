"""第2弾の紹介動画で、実際のスライド以外の場面（62本の壁・スキルに頼む・締め）を HTML で組む。

どれも 1920×1080。書き方は stages.py と同じ（CSS アニメーションと performance.now で動く）。
"""
from stages import CHIP_CSS, page

CHIP = '<div class="chip"><i></i>動くスライド 第2弾<b>無料</b></div>'


# ---------- 62本の壁（上に第2弾の12本を大きく、下に第1弾の50本を小さく） ----------
def wall(cells, new_ids):
    W = 1640
    ox = (1920 - W) / 2
    gap_n, cols_n = 14, 6
    cw_n = (W - gap_n * (cols_n - 1)) / cols_n
    ch_n = cw_n * 9 / 16
    gap_o, cols_o = 8, 13
    cw_o = (W - gap_o * (cols_o - 1)) / cols_o
    ch_o = cw_o * 9 / 16
    top_n = 118
    top_o = top_n + 2 * ch_n + gap_n + 76
    css = CHIP_CSS + f"""
body{{background:#101114}}
.wall{{position:absolute;inset:0;transform-origin:50% 30%;animation:pull 2.5s cubic-bezier(.3,0,.2,1) both}}
@keyframes pull{{from{{transform:scale(1.12)}}to{{transform:none}}}}
.wall img{{position:absolute;border-radius:3px;opacity:.42;filter:saturate(.7);animation:fade .4s both}}
.wall img.new{{opacity:1;filter:none;border-radius:6px;box-shadow:0 0 0 3px #ff5a36,0 14px 30px rgb(0 0 0 / .55);animation:pop .45s cubic-bezier(.2,.9,.2,1) both}}
.lab{{position:absolute;left:{ox}px;font-weight:900;font-size:26px;letter-spacing:.04em;color:#fff;animation:fade .4s both}}
.lab em{{font-style:normal;color:#ff5a36}}
.lab.o{{color:rgb(255 255 255 / .55)}}
@keyframes pop{{from{{opacity:0;transform:scale(.85)}}to{{opacity:1;transform:none}}}}
@keyframes fade{{from{{opacity:0}}}}
.chip{{top:auto;bottom:70px;right:{ox}px}}
.scap{{left:{ox}px;bottom:52px;font-size:84px;padding:0;background:none;box-shadow:none;white-space:nowrap;animation:rise .5s cubic-bezier(.2,.9,.2,1) .5s both}}
@keyframes rise{{from{{opacity:0;transform:translateY(40px)}}to{{opacity:1;transform:none}}}}
"""
    news = [c for c in cells if c[0] in new_ids]
    olds = [c for c in cells if c[0] not in new_ids]
    imgs = []
    for k, (_, src) in enumerate(news):
        imgs.append(f'<img class="new" src="{src}" style="left:{ox + (k % cols_n) * (cw_n + gap_n)}px;top:{top_n + (k // cols_n) * (ch_n + gap_n)}px;'
                    f'width:{cw_n}px;height:{ch_n}px;animation-delay:{0.1 + k * 0.05:.2f}s">')
    for k, (_, src) in enumerate(olds):
        imgs.append(f'<img src="{src}" style="left:{ox + (k % cols_o) * (cw_o + gap_o)}px;top:{top_o + (k // cols_o) * (ch_o + gap_o)}px;'
                    f'width:{cw_o}px;height:{ch_o}px;animation-delay:{0.3 + k * 0.006:.3f}s">')
    labs = (f'<div class="lab" style="top:{top_n - 44}px">第2弾 <em>NEW 12</em></div>'
            f'<div class="lab o" style="top:{top_o - 44}px">第1弾 50（今回から変形の仕組み入り）</div>')
    body = f'<div class="wall">{labs}{"".join(imgs)}</div>{CHIP}<div class="scap">12種を足して、<em>全62種。</em></div>'
    return page(css, body)


# ---------- スキルを入れて、頼むだけ ----------
PROMPT = "動くスライドで、来期の出店計画を銀行の融資担当向けに作って。ページをめくっても図がつながるやつで。"


def ask(covers):
    css = CHIP_CSS + """
body{background:#f6f5f1}
.bgw{position:absolute;inset:-40px;display:grid;grid-template-columns:repeat(6,1fr);gap:18px;opacity:.16;transform:rotate(-6deg) scale(1.15);filter:blur(1px)}
.bgw img{width:100%;border-radius:6px}
.box{position:absolute;left:250px;right:250px;top:320px;background:#fff;border-radius:28px;padding:36px 48px 34px;box-shadow:0 40px 90px -30px rgb(0 0 0 / .35),0 0 0 1px rgb(0 0 0 / .06);
  animation:rise .5s cubic-bezier(.2,.9,.2,1) both}
.skill{display:inline-flex;align-items:center;gap:14px;padding:12px 22px 12px 14px;border-radius:14px;background:#16171b;color:#fff;font:700 28px "Inter","Noto Sans JP",sans-serif}
.skill i{width:40px;height:40px;border-radius:10px;background:#ff5a36;display:grid;place-items:center;font-style:normal;font:800 15px "Inter"}
.skill small{font-weight:600;font-size:20px;color:rgb(255 255 255 / .6);margin-left:6px}
.txt{margin:28px 0 22px;min-height:132px;font-size:42px;line-height:1.55;font-weight:700;color:#16171b}
.txt::after{content:"";display:inline-block;width:4px;height:46px;background:#ff5a36;vertical-align:-8px;margin-left:4px;animation:blink .5s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
.row{display:flex;justify-content:space-between;align-items:center}
.row span{font-size:24px;color:#8a8d94;font-weight:700}
.send{width:84px;height:84px;border-radius:50%;background:#16171b;display:grid;place-items:center}
.send.go{animation:pulse .5s ease-out}
@keyframes pulse{50%{transform:scale(1.18);background:#ff5a36}}
.send svg{width:40px;height:40px}
.scap{top:110px;bottom:auto;left:50%;transform:translateX(-50%);white-space:nowrap;animation:rise2 .45s cubic-bezier(.2,.9,.2,1) .1s both}
@keyframes rise2{from{opacity:0;transform:translate(-50%,30px)}to{opacity:1;transform:translateX(-50%)}}
"""
    bg = "".join(f'<img src="{c}">' for c in covers)
    body = (f'<div class="bgw">{bg}</div>{CHIP}<div class="scap">スキルを入れて、<em>頼むだけ。</em></div>'
            '<div class="box"><div class="skill"><i>62</i>ugoku-slide<small>Claude のスキル</small></div><div class="txt" id="txt"></div>'
            '<div class="row"><span>62種から、場面に合う雛形を選んで作ります</span><div class="send" id="send"><svg viewBox="0 0 24 24"><path d="M12 19V5M5 12l7-7 7 7" stroke="#fff" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg></div></div></div>')
    return page(css, body)


# ---------- 締め ----------
def end(covers):
    css = """
body{background:#16171b;color:#fff}
.bgw{position:absolute;left:-100px;right:-100px;top:-60px;display:grid;grid-template-columns:repeat(8,1fr);gap:16px;opacity:.14;animation:drift 3s linear both}
.bgw img{width:100%;border-radius:4px}
@keyframes drift{from{transform:translateY(0)}to{transform:translateY(-100px)}}
.a{position:absolute;left:0;right:0;top:170px;text-align:center;font-weight:900;font-size:150px;letter-spacing:-.03em;line-height:1.15}
.a span{display:block;opacity:0;animation:slam .5s cubic-bezier(.2,.9,.2,1) both}
.a span:nth-child(2){animation-delay:.4s}
.a em{font-style:normal;color:#ff5a36}
.chips{position:absolute;left:0;right:0;top:590px;display:flex;justify-content:center;gap:18px;animation:rise .45s cubic-bezier(.2,.9,.2,1) .8s both}
.chips span{padding:12px 28px;border-radius:999px;border:2px solid rgb(255 255 255 / .35);font-size:36px;font-weight:700}
.url{position:absolute;left:50%;top:720px;transform:translateX(-50%);padding:18px 44px;border-radius:18px;background:#ff5a36;
  font:800 58px "Inter",sans-serif;letter-spacing:-.01em;white-space:nowrap;animation:rise3 .45s cubic-bezier(.2,.9,.2,1) 1.1s both}
@keyframes rise3{from{opacity:0;transform:translate(-50%,30px)}to{opacity:1;transform:translateX(-50%)}}
.fol{position:absolute;left:0;right:0;top:880px;text-align:center;font-size:40px;font-weight:700;color:rgb(255 255 255 / .8);animation:rise .45s 1.4s both}
"""
    bg = "".join(f'<img src="{c}">' for c in covers)
    body = (f'<div class="bgw">{bg}</div><div class="a"><span>有料級。</span><span>でも、<em>全部無料。</em></span></div>'
            '<div class="chips"><span>62デザイン</span><span>434枚</span><span>Claude用スキル</span><span>MIT</span></div>'
            '<div class="url">aiimpl.github.io/ugoku-slide</div><div class="fol">フォローすると、新作が届きます。</div>')
    return page(css, body)
