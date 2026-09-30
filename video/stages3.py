"""第3弾の紹介動画で、スライド以外の場面（冒頭・点検した62本・締め）を HTML で組む。1920×1080。"""
from stages import CHIP_CSS, page

CHIP = '<div class="chip"><i></i>動くスライド 第3弾<b>無料</b></div>'
CHIP_JS = "V.chip('<i></i>動くスライド 第3弾<b>無料</b>')"

# 冒頭：直す場所を、言葉で説明している
HOOK_TEXT = "3枚目の、右上の…その下にある小さい数字を、もう少し大きく。いや、左の方の…"


def hook():
    css = CHIP_CSS + """
body{background:#f6f5f1}
.box{position:absolute;left:230px;right:230px;top:440px;background:#fff;border-radius:28px;padding:36px 46px;
  box-shadow:0 40px 90px -30px rgb(0 0 0 / .35),0 0 0 1px rgb(0 0 0 / .06)}
.txt{min-height:130px;font-size:44px;line-height:1.55;font-weight:700;color:#16171b}
.txt::after{content:"";display:inline-block;width:4px;height:48px;background:#ff5a36;vertical-align:-8px;margin-left:4px;animation:blink .5s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
.scap{top:250px;bottom:auto;left:50%;transform:translateX(-50%);white-space:nowrap;opacity:0;animation:rise2 .45s cubic-bezier(.2,.9,.2,1) 1.6s both}
@keyframes rise2{from{opacity:0;transform:translate(-50%,30px)}to{opacity:1;transform:translateX(-50%)}}
"""
    body = (f'{CHIP}<div class="scap">直す場所、<em>言葉で説明してない？</em></div>'
            '<div class="box"><div class="txt" id="txt"></div></div>')
    return page(css, body)


# 62本すべてに点検の印が付いていく
def checked(cells):
    cols, gap = 11, 10
    W = 1640
    cw = (W - gap * (cols - 1)) / cols
    ch = cw * 9 / 16
    ox, oy = (1920 - W) / 2, 110
    css = CHIP_CSS + f"""
body{{background:#101114}}
.wall img{{position:absolute;width:{cw}px;height:{ch}px;border-radius:3px}}
.ok{{position:absolute;width:30px;height:30px;border-radius:50%;background:#1f9d64;box-shadow:0 0 0 3px #101114;opacity:0;
  animation:pop .35s cubic-bezier(.2,.9,.2,1) both}}
.ok::after{{content:"";position:absolute;left:10px;top:6px;width:7px;height:13px;border:solid #fff;border-width:0 3px 3px 0;transform:rotate(45deg)}}
@keyframes pop{{from{{opacity:0;transform:scale(.4)}}to{{opacity:1;transform:none}}}}
.nums{{position:absolute;left:{ox}px;top:{oy + 6 * (ch + gap) + 40}px;display:flex;gap:56px;color:#fff;font-weight:900;opacity:0;animation:up .45s cubic-bezier(.2,.9,.2,1) 1.4s both}}
.nums b{{display:block;font:900 64px/1.05 "Inter",sans-serif;color:#3ed08d}}
.nums span{{font-size:24px;color:rgb(255 255 255 / .7)}}
@keyframes up{{from{{opacity:0;transform:translateY(20px)}}to{{opacity:1;transform:none}}}}
.chip{{top:auto;bottom:70px;right:{ox}px}}
.scap{{left:{ox}px;bottom:52px;font-size:76px;padding:0;background:none;box-shadow:none;white-space:nowrap}}
"""
    imgs, oks = [], []
    for i, src in enumerate(cells):
        x, y = ox + (i % cols) * (cw + gap), oy + (i // cols) * (ch + gap)
        imgs.append(f'<img src="{src}" style="left:{x}px;top:{y}px">')
        oks.append(f'<i class="ok" style="left:{x + cw - 36}px;top:{y + 6}px;animation-delay:{0.1 + i * 0.018:.3f}s"></i>')
    body = (f'<div class="wall">{"".join(imgs)}{"".join(oks)}</div>'
            '<div class="nums"><div><b>0</b><span>点検で見つかった問題（62本）</span></div>'
            '<div><b>4.5:1</b><span>文字と背景のコントラスト</span></div>'
            '<div><b>全部</b><span>変形の雛形は、どの境目もつながる</span></div></div>'
            f'{CHIP}<div class="scap">62本すべて、<em>点検して磨き直した。</em></div>')
    return page(css, body)


def end(covers):
    css = """
body{background:#16171b;color:#fff}
.bgw{position:absolute;left:-100px;right:-100px;top:-60px;display:grid;grid-template-columns:repeat(8,1fr);gap:16px;opacity:.14;animation:drift 3s linear both}
.bgw img{width:100%;border-radius:4px}
@keyframes drift{from{transform:translateY(0)}to{transform:translateY(-100px)}}
.a{position:absolute;left:0;right:0;top:170px;text-align:center;font-weight:900;font-size:140px;letter-spacing:-.03em;line-height:1.15}
.a span{display:block;opacity:0;animation:slam .5s cubic-bezier(.2,.9,.2,1) both}
.a span:nth-child(2){animation-delay:.4s}
.a em{font-style:normal;color:#ff5a36}
.chips{position:absolute;left:0;right:0;top:590px;display:flex;justify-content:center;gap:18px;animation:rise .45s cubic-bezier(.2,.9,.2,1) .8s both}
.chips span{padding:12px 28px;border-radius:999px;border:2px solid rgb(255 255 255 / .35);font-size:34px;font-weight:700}
.url{position:absolute;left:50%;top:720px;transform:translateX(-50%);padding:18px 44px;border-radius:18px;background:#ff5a36;
  font:800 58px "Inter",sans-serif;white-space:nowrap;animation:rise3 .45s cubic-bezier(.2,.9,.2,1) 1.1s both}
@keyframes rise3{from{opacity:0;transform:translate(-50%,30px)}to{opacity:1;transform:translateX(-50%)}}
.fol{position:absolute;left:0;right:0;top:880px;text-align:center;font-size:40px;font-weight:700;color:rgb(255 255 255 / .8);animation:rise .45s 1.4s both}
"""
    bg = "".join(f'<img src="{c}">' for c in covers)
    body = (f'<div class="bgw">{bg}</div><div class="a"><span>囲んで直す。</span><span>勝手に<em>プレゼンする。</em></span></div>'
            '<div class="chips"><span>E で囲んで直す</span><span>D で自動デモ</span><span>点検つきのスキル</span><span>62種・MIT</span></div>'
            '<div class="url">aiimpl.github.io/ugoku-slide</div><div class="fol">フォローすると、新作が届きます。</div>')
    return page(css, body)
