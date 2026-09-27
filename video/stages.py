"""実際のスライド以外の場面（冒頭・早送り・一覧の壁・頼み方・締め）を HTML で組む。

どれも 1920×1080。動きは CSS アニメーションと performance.now で書くので、
record.shoot のゆっくり撮影でそのままコマになる。
"""

BASE = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<style>
*{box-sizing:border-box}html,body{margin:0;width:1920px;height:1080px;overflow:hidden}
body{font-family:"Noto Sans JP","Hiragino Sans",sans-serif;-webkit-font-smoothing:antialiased;font-feature-settings:"palt" 1}
@keyframes slam{0%{opacity:0;transform:scale(1.35)}60%{opacity:1;transform:scale(.98)}100%{opacity:1;transform:none}}
@keyframes rise{from{opacity:0;transform:translateY(40px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
%CSS%
</style></head><body>%BODY%<script>%JS%</script></body></html>"""


def page(css, body, js=""):
    return BASE.replace("%CSS%", css).replace("%BODY%", body).replace("%JS%", js)


# ---------- 1. いつものスライド → もう、飽きた ----------
def bland():
    css = """
body{background:#fff}
.old{position:absolute;inset:0;background:#fff;font-family:"Hiragino Kaku Gothic ProN","Meiryo",sans-serif;color:#222}
.old .bar{position:absolute;left:0;right:0;top:0;height:170px;background:linear-gradient(#2d5ca8,#1f4789);color:#fff;font-size:64px;padding:48px 90px;font-weight:600}
.old ul{position:absolute;left:120px;top:250px;margin:0;padding:0;list-style:none;font-size:50px;line-height:2.1}
.old li::before{content:"■";color:#2d5ca8;margin-right:26px;font-size:36px;vertical-align:6px}
.old .pie{position:absolute;right:170px;top:300px;width:420px;height:420px;border-radius:50%;
  background:conic-gradient(#2d5ca8 0 38%,#c0504d 38% 63%,#9bbb59 63% 82%,#8064a2 82%);box-shadow:14px 18px 0 #b8b8b8}
.old .no{position:absolute;right:60px;bottom:40px;font-size:28px;color:#888}
.old .ft{position:absolute;left:90px;bottom:40px;font-size:26px;color:#999}
.old{animation:dull 1.4s linear both}
@keyframes dull{0%{filter:none;transform:none}100%{filter:grayscale(.85) brightness(.85);transform:scale(1.04)}}
.cap{position:absolute;left:96px;bottom:96px;padding:18px 34px 20px;background:#16171b;color:#fff;font-weight:900;font-size:72px;line-height:1.2;border-radius:14px;
  box-shadow:0 20px 50px -10px rgb(0 0 0 / .45);opacity:0}
.c1{animation:rise .45s cubic-bezier(.2,.9,.2,1) .1s both}
.c2{animation:rise .45s cubic-bezier(.2,.9,.2,1) .7s both}
.cap em{font-style:normal;color:#ff5a36}
.x{position:absolute;inset:0;background:#0d0d10;display:grid;place-items:center;opacity:0;animation:fade .01s 1.5s forwards}
.x p{margin:0;color:#fff;font-weight:900;font-size:190px;letter-spacing:-.03em;opacity:0;animation:slam .5s cubic-bezier(.2,.9,.2,1) 1.5s forwards}
.x p em{font-style:normal;color:#ff5a36}
"""
    body = """
<div class="old"><div class="bar">第3四半期　営業報告</div>
<ul><li>売上の状況について</li><li>今後の課題</li><li>対策（案）</li><li>その他</li></ul>
<div class="pie"></div><div class="ft">営業部</div><div class="no">3</div></div>
<div class="cap c1">いつものパワポ、</div>
<div class="cap c2" style="left:auto;right:96px;top:230px;bottom:auto">デザイン、<em>ダサいまま</em>？</div>
<div class="x"><p>もう、<em>飽きた。</em></p></div>"""
    return page(css, body)


CHIP_CSS = """
.chip{position:absolute;right:40px;top:36px;z-index:300;padding:10px 18px;border-radius:999px;background:rgb(22 23 27 / .86);color:#fff;font-weight:700;font-size:24px;display:flex;gap:10px;align-items:center}
.chip b{color:#ff5a36}
.chip i{width:26px;height:18px;border-radius:5px;background:#ff5a36;position:relative}
.chip i::after{content:"";position:absolute;left:10px;top:5px;border-left:7px solid #fff;border-top:4px solid transparent;border-bottom:4px solid transparent}
.scap{position:absolute;z-index:300;left:96px;bottom:88px;padding:18px 34px 20px;background:#16171b;color:#fff;font-weight:900;font-size:72px;line-height:1.2;border-radius:14px;
  box-shadow:0 20px 50px -10px rgb(0 0 0 / .45);animation:rise .45s cubic-bezier(.2,.9,.2,1) .1s both}
.scap em{font-style:normal;color:#ff5a36}
"""
CHIP = '<div class="chip"><i></i>動くスライド 50選<b>無料</b></div>'


# ---------- 3. 早送りで次々に（全部ちがうデザイン） ----------
def montage(covers, cut=0.25):
    n = len(covers)
    css = CHIP_CSS + """
body{background:#000}
img{position:absolute;inset:0;width:1920px;height:1080px}
@keyframes cut{0%{opacity:1;transform:scale(1.07)}99.9%{opacity:1;transform:none}100%{opacity:0}}
@keyframes last{from{transform:scale(1.07)}to{transform:none}}
.count{position:absolute;z-index:300;left:96px;top:70px;padding:6px 26px 10px;background:#ff5a36;color:#fff;border-radius:14px;
  font:900 110px/1 "Inter",sans-serif;letter-spacing:-.04em;font-variant-numeric:tabular-nums}
.count small{font-size:44px;opacity:.85;margin-left:6px}
"""
    imgs = "".join(
        f'<img src="{c}" style="z-index:{100 - i};animation:{"last" if i == n - 1 else "cut"} {cut}s linear {i * cut}s both">'
        for i, c in enumerate(covers))
    body = imgs + CHIP + '<div class="count"><span id="n">01</span><small>/ 50</small></div><div class="scap">デザインは、<em>全部ちがう。</em></div>'
    js = f"""const t0=performance.now();const el=document.getElementById('n');
(function f(){{const i=Math.min({n - 1},Math.floor((performance.now()-(window.T0||t0))/{cut * 1000}));
el.textContent=String(Math.round((i+1)*50/{n})).padStart(2,'0');requestAnimationFrame(f)}})();"""
    return page(css, body, js)


# ---------- 4. 50枚の壁へ引いていく ----------
def wall(cells, first_full):
    cols, rows, gap = 10, 5, 12
    cw = (1828 - gap * (cols - 1)) / cols
    ch = cw * 9 / 16
    gw, gh = 1828, rows * ch + (rows - 1) * gap
    ox, oy = (1920 - gw) / 2, 150
    s0 = 1920 / cw
    css = CHIP_CSS + f"""
body{{background:#101114}}
.wall{{position:absolute;left:{ox}px;top:{oy}px;width:{gw}px;height:{gh}px;transform-origin:0 0;
  animation:out 1.4s cubic-bezier(.75,0,.2,1) both}}
@keyframes out{{from{{transform:scale({s0})}}to{{transform:none}}}}
.wall img{{position:absolute;width:{cw}px;height:{ch}px;border-radius:3px;box-shadow:0 6px 16px rgb(0 0 0 / .4)}}
.wall img.full{{animation:fade .5s .6s reverse both}}
.scap{{left:50%;transform:translateX(-50%);bottom:70px;font-size:96px;padding:18px 44px 22px;animation:rise .5s cubic-bezier(.2,.9,.2,1) 1.25s both;white-space:nowrap}}
@keyframes rise{{from{{opacity:0;transform:translate(-50%,40px)}}to{{opacity:1;transform:translateX(-50%)}}}}
"""
    imgs = "".join(
        f'<img src="{c}" style="left:{(i % cols) * (cw + gap)}px;top:{(i // cols) * (ch + gap)}px">'
        for i, c in enumerate(cells))
    imgs += f'<img class="full" src="{first_full}" style="left:0;top:0">'
    body = f'<div class="wall">{imgs}</div>{CHIP}<div class="scap">50デザイン・<em>350枚</em>。</div>'
    return page(css, body)


# ---------- 6. ファイルを渡して、頼むだけ ----------
PROMPT = "この雛形を、来期の採用計画の資料に作り替えて。今の人数は38人、採用費は1人120万円。"


def ask(covers):
    css = CHIP_CSS + """
body{background:#f6f5f1}
.bgw{position:absolute;inset:-40px;display:grid;grid-template-columns:repeat(6,1fr);gap:18px;opacity:.16;transform:rotate(-6deg) scale(1.15);filter:blur(1px)}
.bgw img{width:100%;border-radius:6px}
.box{position:absolute;left:260px;right:260px;top:300px;background:#fff;border-radius:28px;padding:40px 48px 36px;box-shadow:0 40px 90px -30px rgb(0 0 0 / .35),0 0 0 1px rgb(0 0 0 / .06);
  animation:rise .5s cubic-bezier(.2,.9,.2,1) both}
.file{display:inline-flex;align-items:center;gap:16px;padding:14px 22px;border-radius:16px;background:#f3f1ec;font:700 30px "Inter","Noto Sans JP",sans-serif;color:#16171b}
.file i{width:46px;height:56px;border-radius:8px;background:#ff5a36;color:#fff;font:800 14px "Inter";display:grid;place-items:center;font-style:normal}
.txt{margin:30px 0 26px;min-height:120px;font-size:44px;line-height:1.5;font-weight:700;color:#16171b}
.txt::after{content:"";display:inline-block;width:4px;height:48px;background:#ff5a36;vertical-align:-8px;margin-left:4px;animation:blink .5s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
.row{display:flex;justify-content:flex-end}
.send{width:84px;height:84px;border-radius:50%;background:#16171b;display:grid;place-items:center}
.send.go{animation:pulse .5s ease-out}
@keyframes pulse{50%{transform:scale(1.18);background:#ff5a36}}
.send svg{width:40px;height:40px}
.scap{top:110px;bottom:auto;left:50%;transform:translateX(-50%);white-space:nowrap;animation:rise2 .45s cubic-bezier(.2,.9,.2,1) .1s both}
@keyframes rise2{from{opacity:0;transform:translate(-50%,30px)}to{opacity:1;transform:translateX(-50%)}}
"""
    bg = "".join(f'<img src="{c}">' for c in covers)
    body = (f'<div class="bgw">{bg}</div>{CHIP}<div class="scap">ファイルを渡して、<em>頼むだけ。</em></div>'
            '<div class="box"><div class="file"><i>HTML</i>36-mono-red.html</div><div class="txt" id="txt"></div>'
            '<div class="row"><div class="send" id="send"><svg viewBox="0 0 24 24"><path d="M12 19V5M5 12l7-7 7 7" stroke="#fff" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg></div></div></div>')
    return page(css, body)


# ---------- 7. 締め ----------
def end(covers):
    css = """
body{background:#16171b;color:#fff}
.bgw{position:absolute;left:-100px;right:-100px;top:-60px;display:grid;grid-template-columns:repeat(8,1fr);gap:16px;opacity:.14;animation:drift 4s linear both}
.bgw img{width:100%;border-radius:4px}
@keyframes drift{from{transform:translateY(0)}to{transform:translateY(-120px)}}
.a{position:absolute;left:0;right:0;top:170px;text-align:center;font-weight:900;font-size:150px;letter-spacing:-.03em;line-height:1.15}
.a span{display:block;opacity:0;animation:slam .5s cubic-bezier(.2,.9,.2,1) both}
.a span:nth-child(2){animation-delay:.45s}
.a em{font-style:normal;color:#ff5a36}
.chips{position:absolute;left:0;right:0;top:590px;display:flex;justify-content:center;gap:18px;animation:rise .45s cubic-bezier(.2,.9,.2,1) 1s both}
.chips span{padding:12px 28px;border-radius:999px;border:2px solid rgb(255 255 255 / .35);font-size:36px;font-weight:700}
.url{position:absolute;left:50%;top:720px;transform:translateX(-50%);padding:18px 44px;border-radius:18px;background:#ff5a36;
  font:800 58px "Inter",sans-serif;letter-spacing:-.01em;white-space:nowrap;animation:rise3 .45s cubic-bezier(.2,.9,.2,1) 1.4s both}
@keyframes rise3{from{opacity:0;transform:translate(-50%,30px)}to{opacity:1;transform:translateX(-50%)}}
.fol{position:absolute;left:0;right:0;top:880px;text-align:center;font-size:40px;font-weight:700;color:rgb(255 255 255 / .8);animation:rise .45s 1.8s both}
"""
    bg = "".join(f'<img src="{c}">' for c in covers)
    body = (f'<div class="bgw">{bg}</div><div class="a"><span>有料級。</span><span>でも、<em>全部無料。</em></span></div>'
            '<div class="chips"><span>50デザイン</span><span>350枚</span><span>1ファイルで完結</span><span>MIT</span></div>'
            '<div class="url">aiimpl.github.io/ugoku-slide</div><div class="fol">フォローすると、新作が届きます。</div>')
    return page(css, body)
