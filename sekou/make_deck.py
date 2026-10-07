"""Blender のコマと計算結果から、動くスライドの雛形 63-sekou.html を書き出す。

python3 make_deck.py   （先に frames/ を assets に変換しておく：make_assets.sh。計算結果は data/）
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = json.loads((HERE / "spec.json").read_text())
LAB = json.loads((HERE / "data" / "labels.json").read_text())
SH = json.loads((HERE / "data" / "shade.json").read_text())
OUT = HERE.parent / "src" / "decks" / "63-sekou.html"
WEEKS = SPEC["weeks"]
S = SPEC["sched"]

# 工種と金額（億円・架空）。工程はスライドの棒と Blender で同じ値
TASKS = [("杭", "杭工事", 1.6), ("基礎", "基礎・地下", 2.2), ("鉄骨", "鉄骨建方・床", 5.8),
         ("外装", "外装 カーテンウォール", 3.9), ("外構", "外構・植栽", 0.5)]
TOTAL = sum(t[2] for t in TASKS)


def stack(prefix, n, var, cls=""):
    return "".join(f'<img src="assets/sekou/{prefix}{i:02d}.webp" style="--n:{i}" alt="">' for i in range(n))


TURN = 48


def turn_layer(empty=False):
    """一周のコマ。表紙は同じ画像を二重に持たないよう空にしておき、開いたときに工程のページから写す"""
    imgs = "" if empty else "".join(f'<img src="assets/sekou/t{i % TURN:02d}.webp" style="--n:{i}" alt="">' for i in range(TURN + 1))
    return f'<div class="turn">{imgs}</div><span class="turn-hint">ドラッグで回せます</span>'


# 進捗・出来高の式
lets = []
for key, _, cost in TASKS:
    a, b = S[key]
    lets.append(f"p_{key} = min(max((wk - {a}) / {b - a}, 0), 1)")
lets.append("done = " + " + ".join(f"p_{k} * {c}" for k, _, c in TASKS))
lets.append(f"fl = min(max(round((wk - {S['鉄骨'][0]}) / {(S['鉄骨'][1] - S['鉄骨'][0]) / SPEC['floors']} + 0.5), 0), {SPEC['floors']})")
LET = "; ".join(lets)
STAGE = ("wk < 0.5 ? '着工前' : wk < {a1} ? '杭を打っています' : wk < {a2} ? '基礎をつくっています' : "
         "wk < {a3} ? '鉄骨を建てています' : wk < {a4} ? '外装を張っています' : wk < {a5} ? '外構・仕上げ' : '完成・引渡し'").format(
    a1=S["杭"][1], a2=S["基礎"][1], a3=S["鉄骨"][1], a4=S["外装"][1], a5=S["外構"][1])

# ガントの行
rows = []
for key, name, cost in TASKS:
    a, b = S[key]
    rows.append(f'<div class="row"><div class="tn">{name}<small>{cost:.1f}億</small></div>'
                f'<div class="lane"><i class="bar" style="--a:{a};--b:{b}"><b></b></i></div></div>')
months = "".join(f'<span style="--m:{m}">{(m + 3) % 12 + 1}月</span>' for m in range(12))

# 日影：時刻 → 規制を超えた面積（m²）。33コマの値をそのまま式に
fr = SH["frames"]
over = " : ".join(f"t < {f['t'] + 0.125:.3f} ? {round(f['over_m2'])}" for f in fr[:-1]) + f" : {round(fr[-1]['over_m2'])}"
alt = " : ".join(f"t < {f['t'] + 0.125:.3f} ? {f['alt']:.1f}" for f in fr[:-1]) + f" : {fr[-1]['alt']:.1f}"
FINAL_OVER = round(fr[-1]["over_m2"])

fl_labels = "".join(
    f'<div class="fl-l" style="--x:{p[0]};--y:{p[1]};--d:{0.08 * i:.2f}"><i></i><span>{f}F<b>{"エントランス・ロビー" if f == 1 else "事務所"}</b></span></div>'
    for i, (f, p) in enumerate(zip(range(1, SPEC["floors"] + 1), LAB["floors"])) if f in (1, 3, 5, 6, 8))

html = f'''<!--meta
{{"title":"（仮称）サンプル町オフィス 新築工事 施工計画｜サンプル建設","style":"施工計画 × 3D","use":"施工計画・工程説明",
 "group":"触れる・立体",
 "aim":"ゼネコンの工事担当が発注者との定例で、工程・断面・日影・完成の姿を、パワポのまま建物を動かして説明する。",
 "desc":"工程表の「今日」の線をドラッグすると、Blender で描いたビルが杭から1階ずつ建ち上がり、進捗と出来高が計算し直される。日影は冬至の8時〜16時を動かせる。",
 "fonts":"https://fonts.googleapis.com/css2?family=Jost:wght@300;400;500&family=Noto+Sans+JP:wght@300;400;500;700&display=swap"}}
-->
<style>
:root{{
  --bg:#edece8; --surface:#f7f6f3; --ink:#232427; --muted:#5a5c61; --line:#c9c7c1;
  --accent:#b9502b; --accent-ink:#ffffff; --accent-text:#a2431f; --frame:#d8d6d0;
  --font:"Noto Sans JP","Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif;
  --font-num:"Jost","Noto Sans JP","Hiragino Sans",sans-serif;
  --head-weight:500; --radius:0px; --shadow:none; --pad-y:56px; --pad-x:64px;
  --paper:#fbfaf7;
}}
.deck{{background:radial-gradient(1300px 820px at 62% 38%,#f5f4f1 0%,#ecebe7 58%,#e2e0db 100%)}}
.slide{{background:transparent}}
/* 見出し：字間をあけた小見出し＋線、結論の一文 */
.hd{{position:absolute;left:64px;right:64px;top:44px}}
.hd .kicker{{font:400 15px/1 var(--font-num);letter-spacing:.32em;color:var(--muted);margin-bottom:18px;display:flex;align-items:center;gap:14px}}
.hd .kicker b{{font-weight:500;color:var(--ink)}}
.hd .kicker::after{{content:"";flex:0 0 60px;height:1px;background:var(--ink)}}
.hd h2{{font-size:32px;line-height:1.5;font-weight:500;letter-spacing:.05em;color:var(--ink);margin:0}}
.hd h2 em{{font-style:normal;color:var(--accent-text);font-weight:500}}
.foot{{position:absolute;left:64px;right:40px;bottom:20px;display:flex;justify-content:space-between;font-size:14px;color:var(--muted)}}
.foot b{{font-weight:500;color:var(--ink)}}
.num{{font-family:var(--font-num);font-variant-numeric:tabular-nums}}
/* 図面の表題欄（右下） */
.tb{{position:absolute;right:36px;bottom:18px;display:flex;border:1px solid var(--ink);font:400 12px/1 var(--font-num);letter-spacing:.14em;color:var(--ink);background:var(--surface);z-index:2}}
.tb span{{padding:6px 10px}}
.tb span+span{{border-left:1px solid var(--ink)}}
.north{{position:absolute;width:40px;height:40px;border:1px solid var(--ink);border-radius:50%;font:400 12px/1 var(--font-num);letter-spacing:.1em;display:grid;place-items:center;background:var(--surface)}}
.north::before{{content:"";position:absolute;left:50%;top:-8px;margin-left:-5px;border:5px solid transparent;border-bottom:10px solid var(--ink);border-top:0}}
details.why{{border:0;border-top:1px solid var(--line);border-radius:0;background:transparent}}
details.why>summary{{color:var(--ink);font-weight:500;font-size:16px;padding:10px 0;letter-spacing:.04em}}
details.why>summary::before{{background:transparent;border:1px solid var(--ink);color:var(--ink);font-size:16px;width:20px;height:20px}}
details.why>.body{{padding:0 0 12px;font-size:16px}}
details.why.float[open]>.body{{background:var(--surface);border:1px solid var(--ink);border-radius:0;padding:14px 16px;box-shadow:0 18px 40px -16px rgb(60 52 42 / .35)}}

/* 建物の絵：同じ位置にコマを重ねて、数字に近いコマだけを見せる */
.bldg{{position:absolute;width:520px;height:600px}}
/* 下のコマ（n = 切り捨て）は不透明のまま、次のコマを端数の濃さで重ねる（半分ずつ重ねると透けて見える） */
.bldg img{{position:absolute;inset:0;width:100%;height:100%;opacity:calc(clamp(0, 1 - (var(--n) - var(--f)), 1) * clamp(0, (var(--n) - var(--f) + 1) * 1000, 1))}}
.bldg:not(.solid) img{{-webkit-mask-image:linear-gradient(90deg,transparent 0,#000 14%,#000 92%,transparent),linear-gradient(0deg,transparent 0,#000 12%);
  -webkit-mask-composite:source-in;mask-image:linear-gradient(90deg,transparent 0,#000 14%,#000 92%,transparent),linear-gradient(0deg,transparent 0,#000 12%);mask-composite:intersect}}

/* 完成した建物はドラッグで回る（Blender で一周48コマ）。回している間は .turning */
.bldg .turn{{position:absolute;inset:0;opacity:0;transition:opacity .2s}}
.bldg .turn img{{opacity:calc(clamp(0, 1 - (var(--n) - var(--t, 0)), 1) * clamp(0, (var(--n) - var(--t, 0) + 1) * 1000, 1))}}
.bldg.turning>img{{opacity:0!important}}
.bldg.turning .turn{{opacity:1}}
.bldg[data-turn].ready{{cursor:grab}}
.turn-hint{{position:absolute;right:18px;top:28px;font-size:15px;letter-spacing:.06em;color:var(--muted);opacity:0;transition:opacity .3s;pointer-events:none}}
.bldg.ready .turn-hint{{opacity:1}}
.bldg.turning .turn-hint{{opacity:0}}

/* ---- 表紙 ---- */
.cover-t{{position:absolute;left:64px;top:64px;width:560px}}
.cover-t .kicker{{font:400 15px/1 var(--font-num);letter-spacing:.32em;color:var(--muted);display:flex;align-items:center;gap:14px;margin-bottom:34px}}
.cover-t .kicker b{{font-weight:500;color:var(--ink)}}
.cover-t .kicker::after{{content:"";flex:0 0 60px;height:1px;background:var(--ink)}}
.cover-t h1{{font-size:54px;line-height:1.36;font-weight:500;letter-spacing:.06em;margin:0}}
.cover-t h1 em{{font-style:normal;color:var(--accent-text)}}
.cover-t .lead{{font-size:19px;line-height:1.9;color:var(--muted);margin-top:24px;max-width:460px}}
.cover-t .meta{{position:absolute;top:470px;width:470px;display:grid;gap:10px;font-size:16px;color:var(--muted)}}
.cover-t .meta div{{display:grid;grid-template-columns:120px 1fr;border-top:1px solid var(--line);padding-top:10px}}
.cover-t .meta b{{font:400 13px/1.6 var(--font-num);letter-spacing:.22em;color:var(--ink)}}
.s-cover .bldg{{left:660px;top:50px;--f:{WEEKS}}}

/* ---- 工程 ---- */
.gantt{{position:absolute;left:64px;top:182px;width:640px}}
.gantt .scale{{position:relative;height:26px;margin-left:170px;border-bottom:1px solid var(--ink)}}
.gantt .scale span{{position:absolute;left:calc(var(--m) * 100% / 12);font:400 13px/1 var(--font-num);letter-spacing:.06em;color:var(--muted);padding-left:4px;border-left:1px solid var(--line);height:22px}}
.row{{display:flex;align-items:center;height:52px;border-bottom:1px solid var(--line)}}
.tn{{width:170px;font-size:16px;font-weight:500;line-height:1.3}}
.tn small{{display:block;font:400 14px/1.4 var(--font-num);color:var(--muted);letter-spacing:.04em}}
.lane{{position:relative;flex:1;height:100%}}
.bar{{position:absolute;top:18px;height:16px;left:calc(var(--a) / {WEEKS} * 100%);width:calc((var(--b) - var(--a)) / {WEEKS} * 100%);
  background:repeating-linear-gradient(135deg,rgb(35 36 39 / .16) 0 1px,transparent 1px 6px),var(--paper);border:1px solid var(--ink);overflow:hidden}}
.bar b{{position:absolute;left:0;top:0;bottom:0;width:calc(clamp(0, (var(--wk) - var(--a)) / (var(--b) - var(--a)), 1) * 100%);background:var(--ink)}}
.today{{position:absolute;top:182px;height:290px;left:calc(234px + var(--wk) / {WEEKS} * 470px);width:0;border-left:1.5px solid var(--accent);pointer-events:none;z-index:2}}
.today span{{position:absolute;top:-30px;left:0;transform:translateX(-50%);background:var(--accent-text);color:#fff;font:500 13px/1 var(--font);letter-spacing:.06em;padding:6px 9px;white-space:nowrap}}
.today::after{{content:"";position:absolute;left:-7px;bottom:-7px;width:12px;height:12px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 4px rgb(185 80 43 / .18)}}
.slide input.drag{{position:absolute;left:224px;top:150px;width:490px;height:340px;opacity:0!important;cursor:ew-resize;z-index:3;margin:0}}
.kpis{{position:absolute;left:64px;top:500px;width:640px;display:grid;grid-template-columns:1.3fr 1fr 1fr;border-top:1px solid var(--ink)}}
.kpis>div{{padding:12px 18px 0 0}}
.kpis .k{{font-size:14px;color:var(--muted);margin-bottom:8px}}
.kpis .v{{font:300 46px/1 var(--font-num);color:var(--ink);letter-spacing:-.01em}}
.kpis .v small{{font:400 16px var(--font);color:var(--muted);margin-left:4px}}
.kpis .st{{font:500 20px/1.6 var(--font);color:var(--accent-text);letter-spacing:.04em}}
.s-plan .bldg{{left:716px;top:96px;--f:var(--wk)}}
.why{{position:absolute}}
.s-plan .why{{left:64px;bottom:52px;width:300px}}

/* ---- 断面 ---- */
@property --cut{{syntax:"<number>";inherits:true;initial-value:0}}
.s-sec .bldg{{left:716px;top:96px;--f:var(--cut)}}
.slide.active.s-sec{{animation:cut 1.6s cubic-bezier(.45,0,.2,1) 1.3s both}}
@keyframes cut{{from{{--cut:0}}to{{--cut:23}}}}
.fl-l{{position:absolute;left:calc(716px + var(--x) * 520px);top:calc(96px + var(--y) * 600px);width:0;height:0;opacity:0}}
.fl-wrap{{position:absolute;inset:0;pointer-events:none}}
.slide.active .fl-wrap .fl-l{{animation:flin .4s ease-out calc(2.7s + var(--d) * 1s) both}}
@keyframes flin{{from{{opacity:0;transform:translateX(-12px)}}to{{opacity:1;transform:none}}}}
.fl-l i{{position:absolute;right:0;top:0;width:calc(var(--x) * 520px + 716px - 640px);border-top:1px solid var(--ink)}}
.fl-l i::after{{content:"";position:absolute;right:-3px;top:-3px;width:5px;height:5px;border-radius:50%;background:var(--ink)}}
.fl-l span{{position:absolute;right:calc(var(--x) * 520px + 716px - 640px + 12px);top:-11px;white-space:nowrap;font:400 19px/1 var(--font-num);color:var(--ink);letter-spacing:.04em}}
.fl-l span b{{font:400 14px var(--font);color:var(--muted);margin-left:10px;letter-spacing:.08em}}
.sec-t{{position:absolute;left:64px;top:200px;width:380px;border-top:1px solid var(--ink)}}
.sec-t>div{{display:grid;grid-template-columns:1fr auto;align-items:baseline;padding:13px 0;border-bottom:1px solid var(--line)}}
.sec-t span{{font-size:17px}}
.sec-t b{{font:300 38px/1 var(--font-num)}}
.sec-t b small{{font:400 16px var(--font);margin-left:3px}}
.sec-t p{{font-size:16px;line-height:1.8;color:var(--muted);margin:16px 0 0}}
.sec-legend{{position:absolute;left:64px;bottom:64px;display:flex;gap:22px;font-size:14px;color:var(--muted);letter-spacing:.06em}}
.sec-legend i{{display:inline-block;width:14px;height:14px;margin-right:6px;vertical-align:-2px;border:1px solid var(--ink)}}

/* ---- 日影 ---- */
.shade{{position:absolute;left:540px;top:150px;width:680px;height:505px;--f:calc((var(--t) - 8) * 4);overflow:hidden;border:1px solid var(--ink);background:#f4f1ea;box-shadow:0 1px 0 rgb(0 0 0 / .06),0 22px 50px -18px rgb(60 52 42 / .28)}}
.shade img{{position:absolute;inset:0;width:100%;height:100%;opacity:calc(clamp(0, 1 - (var(--n) - var(--f)), 1) * clamp(0, (var(--n) - var(--f) + 1) * 1000, 1))}}
.s-shade .north{{left:1160px;top:170px}}
.shctl{{position:absolute;left:64px;top:186px;width:420px}}
.shctl .time{{font:300 76px/1 var(--font-num);color:var(--ink);letter-spacing:-.01em}}
.shctl .time small{{font:400 16px var(--font);color:var(--muted);margin-left:12px;letter-spacing:.1em}}
.shctl input{{width:100%;margin:22px 0 8px;accent-color:var(--accent)}}
.shctl .ticks{{display:flex;justify-content:space-between;font:400 12px var(--font-num);color:var(--muted);letter-spacing:.06em}}
.shctl .res{{margin-top:26px;border-top:1px solid var(--ink)}}
.shctl .res>div{{display:grid;grid-template-columns:1fr auto;align-items:baseline;padding:12px 0;border-bottom:1px solid var(--line)}}
.shctl .res .k{{font-size:17px}}
.shctl .res .v{{font:300 40px/1 var(--font-num);color:var(--ink)}}
.shctl .res .v.red{{color:var(--accent-text)}}
.shctl .res .v small{{font:400 16px var(--font);color:var(--muted);margin-left:3px}}
.legend{{position:absolute;left:64px;bottom:106px;display:grid;gap:8px;font-size:14px;color:var(--muted)}}
.legend i{{display:inline-block;width:26px;margin-right:8px;vertical-align:4px}}
.s-shade .why{{left:64px;bottom:52px;width:300px}}

/* ---- 外観 ---- */
@property --lit{{syntax:"<number>";inherits:true;initial-value:0}}
.s-dusk .bldg{{left:740px;top:96px;width:485px;height:560px;--f:var(--lit);overflow:hidden;border:1px solid var(--ink);box-shadow:0 22px 50px -18px rgb(60 52 42 / .35)}}
.slide.active.s-dusk{{animation:lit 2.2s linear .2s both}}
@keyframes lit{{from{{--lit:0}}to{{--lit:11}}}}
.chg{{position:absolute;left:64px;top:200px;width:560px;list-style:none;margin:0;padding:0;border-top:1px solid var(--ink)}}
.chg li{{display:grid;grid-template-columns:34px 1fr;gap:12px;padding:16px 0;border-bottom:1px solid var(--line)}}
.chg li i{{width:26px;height:26px;border-radius:50%;background:var(--ink);color:#fff;font:500 15px/26px var(--font-num);font-style:normal;text-align:center;margin-top:2px}}
.chg li b{{display:block;font-size:19px;font-weight:500;margin-bottom:3px}}
.chg li span{{font-size:16px;color:var(--muted);line-height:1.6}}

/* ---- 締め ---- */
.ask{{position:absolute;left:64px;top:200px;right:64px;display:grid;grid-template-columns:1fr 1fr;gap:40px}}
.ask .card{{border:0;border-top:1px solid var(--ink);padding:18px 0 0;background:transparent;border-radius:0}}
.ask .card .tag{{font:400 13px/1 var(--font-num);letter-spacing:.22em;color:var(--muted)}}
.ask .card.pick .tag{{color:var(--accent-text)}}
.ask h3{{font-size:22px;font-weight:500;margin:12px 0 10px;letter-spacing:.04em}}
.ask p{{font-size:17px;line-height:1.75;color:var(--muted);margin:0}}
.ask .big{{font:300 54px/1.1 var(--font-num);color:var(--ink);margin:18px 0 4px}}
.ask .card.pick .big{{color:var(--accent-text)}}
.ask .big small{{font:400 16px var(--font);color:var(--muted);margin-left:6px}}
.next{{position:absolute;left:64px;right:64px;top:500px;display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--ink)}}
.next div{{padding:14px 20px 0 0;font-size:16px;line-height:1.6}}
.next b{{display:block;font:400 13px var(--font-num);color:var(--ink);letter-spacing:.22em;margin-bottom:6px}}
@media (prefers-reduced-motion:reduce){{.slide.active.s-sec,.slide.active.s-dusk{{animation-duration:.01s}}}}
</style>

<main class="deck" data-transition="morph">
  <section class="slide s-cover" data-title="表紙">
    <div class="cover-t">
      <div class="kicker"><b>SAMPLE KENSETSU</b>施工計画書</div>
      <h1>サンプル町オフィス、<br><em>{WEEKS}週</em>で建てる。</h1>
      <p class="lead">鉄骨造 地上8階・延床 約4,200㎡。工程・断面・日影・完成の姿を、この資料の中で建物を動かしてご説明します。</p>
      <div class="meta"><div><b>PERIOD</b><span>着工 4月 → 竣工 翌年3月</span></div><div><b>CLIENT</b><span>サンプル不動産 株式会社</span></div><div><b>FROM</b><span>サンプル建設 株式会社 工事部</span></div></div>
    </div>
    <div class="bldg" data-morph="bldg" data-turn><img src="assets/sekou/p{WEEKS:02d}.webp" style="--n:{WEEKS}" alt="完成した建物">{turn_layer(empty=True)}</div>
    <div class="foot" data-morph="foot"><span><b>サンプル建設</b>　施工計画書 第1版</span><span>数字・会社名は架空のサンプルです</span></div>
    <aside class="notes">右の建物は Blender で描いた完成の姿。次のページから、工程に合わせて建ち上がります。</aside>
  </section>

  <section class="slide s-plan" data-title="工程" data-calc data-let="{LET}">
    <div class="hd"><div class="kicker"><b>01</b>工程</div><h2>鉄骨は第{S["鉄骨"][1]}週に上棟。外装を重ねて、<em>第{S["外装"][1]}週に完成</em></h2></div>
    <div class="gantt"><div class="scale">{months}</div>{"".join(rows)}</div>
    <div class="today"><span>第<b class="num" data-out="round(wk)" data-format="int"></b>週</span></div>
    <input class="drag" type="range" name="wk" min="0" max="{WEEKS}" step="0.05" value="30" aria-label="今日の週" data-demo="1">
    <div class="kpis">
      <div><div class="k">いまの作業</div><div class="st" data-out="{STAGE}"></div></div>
      <div><div class="k">進捗（金額ベース）</div><div class="v"><span data-out="done / {TOTAL} * 100" data-format="int"></span><small>%</small></div></div>
      <div><div class="k">出来高 / {TOTAL:.1f}億円</div><div class="v"><span data-out="done" data-format="dec1"></span><small>億円</small></div></div>
    </div>
    <div class="bldg" data-morph="bldg" data-turn>{stack("p", WEEKS + 1, "f")}{turn_layer()}</div>
    <details class="why float"><summary>出来高の出し方</summary><div class="body">工種ごとの金額 × その工種の進み具合（週で按分）の合計。杭1.6・基礎2.2・鉄骨5.8・外装3.9・外構0.5億円。</div></details>
    <div class="tb"><span>K-01</span><span>工程表</span><span>52週</span></div>
    <div class="foot" data-morph="foot"><span><b>サンプル建設</b>　施工計画書</span></div>
    <aside class="notes">オレンジの「今日」の線を左右に動かすと、その週の現場の姿になります。鉄骨は1フロア3週。クレーンは建った階に合わせて継ぎ足していきます。</aside>
  </section>

  <section class="slide s-sec" data-title="断面">
    <div class="hd"><div class="kicker"><b>02</b>断面</div><h2>6階から上は北側を<em>4m下げて</em>、住宅地への影を減らす</h2></div>
    <div class="sec-t">
      <div><span>柱の間隔</span><b>6<small>m 格子</small></b></div>
      <div><span>階高（1階 / 2階から上）</span><b>4.5 / 3.8<small>m</small></b></div>
      <div><span>北側のセットバック</span><b>4<small>m（6〜8階）</small></b></div>
      <p>上の3層だけ北の面を下げ、床面積を保ったまま北の住宅地に落ちる影を短くしています。</p>
    </div>
    <div class="bldg" data-morph="bldg">{stack("s", 24, "f")}</div>
    <div class="fl-wrap">{fl_labels}</div>
    <div class="sec-legend"><span><i style="background:#e8590c"></i>ロビー</span><span><i style="background:#f3d9b8"></i>事務所</span><span><i style="background:#b4542e"></i>鉄骨（H形鋼 700×300）</span></div>
    <div class="tb"><span>K-02</span><span>断面図</span><span>S=1:400</span></div>
    <div class="foot" data-morph="foot"><span><b>サンプル建設</b>　施工計画書</span></div>
    <aside class="notes">ページを開くと、建物が縦に切れて中が見えます。色はフロアの用途。</aside>
  </section>

  <section class="slide s-shade" data-title="日影" data-calc>
    <div class="hd"><div class="kicker"><b>03</b>日影（冬至）</div><h2>冬至の日影は、<em>北側の一部で規制の時間を超える</em></h2></div>
    <div class="shctl">
      <div class="time num"><span data-out="round(t - 0.49)" data-format="int"></span>:<span data-out="round((t - round(t - 0.49)) * 60)" data-format="pad2"></span><small>真太陽時</small></div>
      <input type="range" name="t" min="8" max="16" step="0.25" value="8" aria-label="時刻" data-demo="1">
      <div class="ticks"><span>8:00</span><span>10:00</span><span>12:00</span><span>14:00</span><span>16:00</span></div>
      <div class="res">
        <div><span class="k">太陽の高さ</span><span class="v"><span data-out="{alt}" data-format="dec1"></span><small>°</small></span></div>
        <div><span class="k">規制を超えた範囲</span><span class="v red"><span data-out="{over}" data-format="int"></span><small>㎡</small></span></div>
      </div>
    </div>
    <div class="shade">{stack("h", len(fr), "f")}</div>
    <div class="legend">
      <span><i style="border-top:2px dashed #e8590c"></i>敷地から5m（ここから先は4時間まで）</span>
      <span><i style="border-top:2px dashed #b3261e"></i>敷地から10m（ここから先は2.5時間まで）</span>
      <span><i style="height:12px;background:#e03a1e;vertical-align:-1px"></i>8時からの日影の合計が、規制の時間を超えた所</span>
    </div>
    <details class="why float"><summary>計算の条件</summary><div class="body">東京（北緯35.68°）・冬至の8時〜16時、1分ごとに建物の影を計算して足し合わせた。測定面は地盤から4m。規制は第一種中高層住居専用地域（二）の例。16時までの合計で {FINAL_OVER:,}㎡ が超える。</div></details>
    <div class="north">N</div>
    <div class="tb"><span>K-03</span><span>日影図</span><span>冬至 GL+4m</span></div>
    <div class="foot" data-morph="foot"><span><b>サンプル建設</b>　施工計画書</span></div>
    <aside class="notes">つまみで時刻を動かすと影が回り、合計の時間が規制を超えた所が赤くなります。</aside>
  </section>

  <section class="slide s-dusk" data-title="外観">
    <div class="hd"><div class="kicker"><b>04</b>完成の姿</div><h2>夕方、<em>通りから見上げた外観</em></h2></div>
    <ul class="chg">
      <li class="step"><i>1</i><div><b>ガラスと白い方立</b><span>1.5m ごとの縦の線と、パネルごとの色の揺らぎで、8階建てを重く見せない。</span></div></li>
      <li class="step"><i>2</i><div><b>階ごとの白い帯と暗いスパンドレル</b><span>床の位置をそろえ、夜は天井の照明が帯になって並ぶ。</span></div></li>
      <li class="step"><i>3</i><div><b>道路側の並木と植え込み</b><span>歩道に5本。ひさしの下がエントランス。</span></div></li>
    </ul>
    <div class="bldg solid" data-morph="bldg">{stack("d", 12, "f")}</div>
    <div class="tb"><span>K-04</span><span>外観パース</span><span>夕景</span></div>
    <div class="foot" data-morph="foot"><span><b>サンプル建設</b>　施工計画書</span></div>
    <aside class="notes">日が沈んでから、フロアごとに明かりがついていきます。</aside>
  </section>

  <section class="slide s-end" data-title="決めていただきたいこと">
    <div class="hd"><div class="kicker"><b>05</b>ご判断いただきたいこと</div><h2>日影の対策を、<em>次の定例までに2案から</em>お選びください</h2></div>
    <div class="ask">
      <div class="card pick"><div class="tag">PLAN A ｜ おすすめ</div><h3>6階から上を、さらに北で4m下げる</h3><p>床面積は約3%減。外観の段がはっきり出ます。</p><div class="big num"><span data-count="120" data-format="int"></span><small>㎡ 減</small></div></div>
      <div class="card"><div class="tag">PLAN B</div><h3>8階をなくし、7階建てにする</h3><p>床面積は約12%減。工期は3週短くなります。</p><div class="big num"><span data-count="510" data-format="int"></span><small>㎡ 減</small></div></div>
    </div>
    <div class="next">
      <div class="step"><b>STEP 1</b>2案の日影を同じ条件で計算し直す（1週間）</div>
      <div class="step"><b>STEP 2</b>近隣説明会の資料に、このページの日影を使う</div>
      <div class="step"><b>STEP 3</b>決まった案で、工程と出来高を引き直す</div>
    </div>
    <div class="foot" data-morph="foot"><span><b>サンプル建設</b>　工事部 工事課　内線 0000</span><span>数字・会社名は架空のサンプルです</span></div>
    <aside class="notes">面積の減り方は架空の概算です。</aside>
  </section>
</main>
<script>
// 完成した建物をドラッグで回す（表紙と、工程表を最後の週まで進めたとき）
(() => {{
  const N = {TURN};
  const src = document.querySelector(".turn img") && document.querySelector(".turn img").parentNode;
  document.querySelectorAll(".turn:empty").forEach(t => {{ if (src) src.querySelectorAll("img").forEach(i => t.appendChild(i.cloneNode())); }});
  document.querySelectorAll(".bldg[data-turn]").forEach(b => {{
    const plan = b.closest("[data-calc]");
    const done = () => !plan || +plan.querySelector("input[name=wk]").value >= {WEEKS} - 0.05;
    let t = 0, x0 = null, t0 = 0;
    const set = v => {{ t = ((v % N) + N) % N; b.style.setProperty("--t", t.toFixed(3)); }};
    const sync = () => {{ b.classList.toggle("ready", done()); if (!done()) {{ b.classList.remove("turning"); set(0); }} }};
    if (plan) plan.addEventListener("input", sync);
    sync();
    b.addEventListener("pointerdown", e => {{ if (!done()) return; x0 = e.clientX; t0 = t; b.classList.add("turning"); e.preventDefault(); }});
    const move = e => {{ if (x0 === null) return; set(t0 - (e.clientX - x0) / 9); }};
    b.addEventListener("pointermove", move);
    window.addEventListener("pointermove", move);
    const up = () => {{ x0 = null; }};
    b.addEventListener("pointerup", up);
    window.addEventListener("pointerup", up);
  }});
}})();
</script>
'''
OUT.write_text(html)
print("wrote", OUT, len(html))
