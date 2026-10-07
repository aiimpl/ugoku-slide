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
 "fonts":"https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+JP:wght@400;500;700;900&display=swap"}}
-->
<style>
:root{{
  --bg:#ffffff; --surface:#f5f6f8; --ink:#1d2430; --muted:#5b6472; --line:#d7dbe2;
  --accent:#c2410c; --accent-ink:#ffffff; --accent-text:#b23c08; --navy:#1f3a5f; --frame:#e5e8ee;
  --font:"Noto Sans JP","Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif;
  --font-num:"Inter","Noto Sans JP","Hiragino Sans",sans-serif;
  --pad-y:56px; --pad-x:64px; --radius:4px;
}}
.deck{{background:#fff}}
.slide{{background:#fff}}
/* パワポの見慣れた枠：上の題名、左の色の帯、下のフッター */
.slide::before{{content:"";position:absolute;left:0;top:0;bottom:0;width:10px;background:var(--navy)}}
.hd{{position:absolute;left:64px;right:64px;top:40px}}
.hd .kicker{{font:600 14px/1 var(--font-num);letter-spacing:.18em;color:var(--accent-text);margin-bottom:12px;text-transform:uppercase}}
.hd h2{{font-size:30px;line-height:1.4;font-weight:700;color:var(--navy);margin:0;letter-spacing:.02em}}
.hd h2 em{{font-style:normal;color:var(--accent-text)}}
.hd::after{{content:"";display:block;margin-top:16px;height:2px;background:linear-gradient(90deg,var(--navy) 0 120px,var(--line) 120px)}}
.foot{{position:absolute;left:64px;right:40px;bottom:18px;display:flex;justify-content:space-between;font-size:13px;color:var(--muted)}}
.foot b{{font-weight:500;color:var(--navy)}}
.num{{font-family:var(--font-num);font-variant-numeric:tabular-nums}}

/* 建物の絵：同じ位置にコマを重ねて、数字に近いコマだけを見せる */
.bldg{{position:absolute;width:520px;height:600px}}
.bldg img{{position:absolute;inset:0;width:100%;height:100%;opacity:max(0, 1 - max(var(--f) - var(--n), var(--n) - var(--f)))}}
.bldg:not(.solid) img{{-webkit-mask-image:linear-gradient(90deg,transparent 0,#000 14%,#000 92%,transparent),linear-gradient(0deg,transparent 0,#000 12%);
  -webkit-mask-composite:source-in;mask-image:linear-gradient(90deg,transparent 0,#000 14%,#000 92%,transparent),linear-gradient(0deg,transparent 0,#000 12%);mask-composite:intersect}}
.bldg::after{{content:"";position:absolute;left:8%;right:8%;bottom:9%;height:1px;background:transparent}}

/* ---- 表紙 ---- */
.cover-t{{position:absolute;left:64px;top:150px;width:600px}}
.cover-t .co{{font:600 15px/1 var(--font-num);letter-spacing:.2em;color:var(--accent-text);margin-bottom:22px}}
.cover-t h1{{font-size:44px;line-height:1.35;font-weight:900;color:var(--navy);margin:0 0 26px;letter-spacing:.01em}}
.cover-t p{{font-size:19px;line-height:1.8;color:var(--muted);margin:0}}
.cover-t dl{{display:grid;grid-template-columns:auto 1fr;gap:10px 22px;margin:40px 0 0;font-size:17px}}
.cover-t dt{{color:var(--muted)}} .cover-t dd{{margin:0;font-weight:500}}
.s-cover .bldg{{right:40px;top:70px;--f:{WEEKS}}}

/* ---- 工程 ---- */
.gantt{{position:absolute;left:64px;top:150px;width:640px}}
.gantt .scale{{position:relative;height:26px;margin-left:170px;border-bottom:1px solid var(--line)}}
.gantt .scale span{{position:absolute;left:calc(var(--m) * 100% / 12);font:500 12px/1 var(--font-num);color:var(--muted);padding-left:4px;border-left:1px solid var(--line);height:22px}}
.row{{display:flex;align-items:center;height:56px;border-bottom:1px solid var(--frame)}}
.tn{{width:170px;font-size:16px;font-weight:500;line-height:1.3}}
.tn small{{display:block;font:500 12px/1.4 var(--font-num);color:var(--muted)}}
.lane{{position:relative;flex:1;height:100%}}
.bar{{position:absolute;top:17px;height:22px;left:calc(var(--a) / {WEEKS} * 100%);width:calc((var(--b) - var(--a)) / {WEEKS} * 100%);
  background:#dde3ec;border-radius:3px;overflow:hidden}}
.bar b{{position:absolute;left:0;top:0;bottom:0;width:calc(clamp(0, (var(--wk) - var(--a)) / (var(--b) - var(--a)), 1) * 100%);background:var(--navy)}}
.today{{position:absolute;top:150px;height:312px;left:calc(234px + var(--wk) / {WEEKS} * 470px);width:0;border-left:2.5px solid var(--accent);pointer-events:none;z-index:2}}
.today span{{position:absolute;top:-30px;left:0;transform:translateX(-50%);background:var(--accent-text);color:#fff;font:700 13px/1 var(--font);padding:6px 9px;border-radius:3px;white-space:nowrap}}
.today::after{{content:"";position:absolute;left:-9px;bottom:-9px;width:16px;height:16px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 4px rgb(232 89 12 / .2)}}
.slide input.drag{{position:absolute;left:224px;top:118px;width:490px;height:360px;opacity:0!important;cursor:ew-resize;z-index:3;margin:0}}
.kpis{{position:absolute;left:64px;top:500px;width:640px;display:grid;grid-template-columns:1.25fr 1fr 1fr;gap:0;border-top:2px solid var(--navy)}}
.kpis>div{{padding:14px 18px 0 0}}
.kpis .k{{font-size:14px;color:var(--muted);margin-bottom:6px}}
.kpis .v{{font:700 34px/1.1 var(--font-num);color:var(--navy)}}
.kpis .v small{{font:500 16px var(--font);color:var(--muted);margin-left:4px}}
.kpis .st{{font:700 22px/1.5 var(--font);color:var(--accent-text)}}
.s-plan .bldg{{left:716px;top:100px;--f:var(--wk)}}
.why{{position:absolute}}
.s-plan .why{{left:64px;bottom:44px}}

/* ---- 断面 ---- */
@property --cut{{syntax:"<number>";inherits:true;initial-value:0}}
.s-sec .bldg{{left:716px;top:100px;--f:var(--cut)}}
.slide.active.s-sec{{animation:cut 1.6s cubic-bezier(.45,0,.2,1) 1.3s both}}
@keyframes cut{{from{{--cut:0}}to{{--cut:23}}}}
.fl-l{{position:absolute;left:calc(716px + var(--x) * 520px);top:calc(100px + var(--y) * 600px);width:0;height:0;opacity:0}}
.fl-wrap{{position:absolute;inset:0;pointer-events:none}}
.slide.active .fl-wrap .fl-l{{animation:flin .4s ease-out calc(2.7s + var(--d) * 1s) both}}
@keyframes flin{{from{{opacity:0;transform:translateX(-12px)}}to{{opacity:1;transform:none}}}}
.fl-l i{{position:absolute;right:0;top:0;width:calc(var(--x) * 520px + 716px - 640px);border-top:1px solid var(--navy)}}
.fl-l i::after{{content:"";position:absolute;right:-4px;top:-4px;width:7px;height:7px;border-radius:50%;background:var(--navy)}}
.fl-l span{{position:absolute;right:calc(var(--x) * 520px + 716px - 640px + 12px);top:-12px;white-space:nowrap;font:700 18px/1 var(--font-num);color:var(--navy)}}
.fl-l span b{{font:500 15px var(--font);color:var(--muted);margin-left:10px}}
.sec-t{{position:absolute;left:64px;top:170px;width:400px;font-size:18px;line-height:1.85;color:var(--muted)}}
.sec-t strong{{color:var(--ink)}}
.sec-legend{{position:absolute;left:64px;bottom:60px;display:flex;gap:22px;font-size:14px;color:var(--muted)}}
.sec-legend i{{display:inline-block;width:14px;height:14px;margin-right:6px;vertical-align:-2px;border-radius:2px}}

/* ---- 日影 ---- */
.shade{{position:absolute;left:520px;top:126px;width:700px;height:520px;--f:calc((var(--t) - 8) * 4);border-radius:4px;overflow:hidden;box-shadow:0 0 0 1px var(--line)}}
.shade img{{position:absolute;inset:0;width:100%;height:100%;opacity:max(0, 1 - max(var(--f) - var(--n), var(--n) - var(--f)))}}
.shade .lb{{position:absolute;font:700 12px/1 var(--font);padding:4px 6px;border-radius:2px;background:rgb(255 255 255 / .85);white-space:nowrap;transform:translate(-50%,-140%)}}
.shctl{{position:absolute;left:64px;top:160px;width:410px}}
.shctl .time{{font:700 64px/1 var(--font-num);color:var(--navy)}}
.shctl .time small{{font:500 18px var(--font);color:var(--muted);margin-left:10px}}
.shctl input{{width:100%;margin:22px 0 8px;accent-color:var(--accent)}}
.shctl .ticks{{display:flex;justify-content:space-between;font:500 12px var(--font-num);color:var(--muted)}}
.shctl .res{{margin-top:30px;border-top:2px solid var(--navy);padding-top:14px;display:grid;grid-template-columns:1fr 1fr;gap:6px 18px}}
.shctl .res .k{{font-size:14px;color:var(--muted)}}
.shctl .res .v{{font:700 30px/1.15 var(--font-num);color:var(--navy)}}
.shctl .res .v.red{{color:#c42d14}}
.shctl .res .v small{{font:500 15px var(--font);color:var(--muted);margin-left:3px}}
.legend{{position:absolute;left:64px;bottom:96px;display:grid;gap:8px;font-size:14px;color:var(--muted)}}
.legend i{{display:inline-block;width:26px;margin-right:8px;vertical-align:4px}}
.s-shade .why{{left:64px;bottom:46px}}

/* ---- 外観 ---- */
@property --lit{{syntax:"<number>";inherits:true;initial-value:0}}
.s-dusk .bldg{{left:740px;top:140px;width:485px;height:560px;--f:var(--lit);overflow:hidden;border-radius:4px}}
.slide.active.s-dusk{{animation:lit 2.2s linear .2s both}}
@keyframes lit{{from{{--lit:0}}to{{--lit:11}}}}
.dusk-t{{position:absolute;left:64px;top:170px;width:560px}}
.dusk-t .list{{font-size:19px;line-height:1.7}}
.dusk-t .list li{{margin-bottom:14px}}
.dusk-t .list b{{color:var(--navy)}}

/* ---- 締め ---- */
.ask{{position:absolute;left:64px;top:160px;right:64px;display:grid;grid-template-columns:1fr 1fr;gap:28px}}
.ask .card{{border:1px solid var(--line);border-top:4px solid var(--navy);padding:24px 26px;border-radius:4px;background:#fff}}
.ask .card.pick{{border-top-color:var(--accent)}}
.ask h3{{font-size:22px;margin:0 0 12px;color:var(--navy)}}
.ask p{{font-size:17px;line-height:1.75;color:var(--muted);margin:0}}
.ask .big{{font:700 40px/1.1 var(--font-num);color:var(--ink);margin:14px 0 4px}}
.ask .big small{{font:500 16px var(--font);color:var(--muted);margin-left:4px}}
.next{{position:absolute;left:64px;right:64px;top:470px;display:flex;gap:16px}}
.next div{{flex:1;background:var(--surface);padding:16px 18px;border-radius:4px;font-size:16px;line-height:1.6}}
.next b{{display:block;font:700 13px var(--font-num);color:var(--accent-text);letter-spacing:.14em;margin-bottom:4px}}
@media (prefers-reduced-motion:reduce){{.slide.active.s-sec,.slide.active.s-dusk{{animation-duration:.01s}}}}
</style>

<main class="deck" data-transition="morph">
  <section class="slide s-cover" data-title="表紙">
    <div class="cover-t">
      <div class="co">CONSTRUCTION PLAN</div>
      <h1>（仮称）サンプル町オフィス<br>新築工事 施工計画</h1>
      <p>鉄骨造 地上8階・延床 約4,200㎡。<br>工程・断面・日影・完成の姿を、この資料の中で動かしてご説明します。</p>
      <dl><dt>工期</dt><dd class="num">{WEEKS}週（着工 4月 → 竣工 翌年3月）</dd><dt>発注者</dt><dd>サンプル不動産 株式会社</dd><dt>施工</dt><dd>サンプル建設 株式会社 工事部</dd></dl>
    </div>
    <div class="bldg" data-morph="bldg"><img src="assets/sekou/p{WEEKS:02d}.webp" style="--n:{WEEKS}" alt="完成した建物"></div>
    <div class="foot" data-morph="foot"><span><b>サンプル建設</b>　施工計画書 第1版</span><span>数字・会社名は架空のサンプルです</span></div>
    <aside class="notes">右の建物は Blender で描いた完成の姿。次のページから、工程に合わせて建ち上がります。</aside>
  </section>

  <section class="slide s-plan" data-title="工程" data-calc data-let="{LET}">
    <div class="hd"><div class="kicker">01 ｜ 工程</div><h2>鉄骨は第{S["鉄骨"][1]}週に上棟。外装を重ねて、<em>第{S["外装"][1]}週に完成</em></h2></div>
    <div class="gantt"><div class="scale">{months}</div>{"".join(rows)}</div>
    <div class="today"><span>第<b class="num" data-out="round(wk)" data-format="int"></b>週</span></div>
    <input class="drag" type="range" name="wk" min="0" max="{WEEKS}" step="0.05" value="30" aria-label="今日の週" data-demo="1">
    <div class="kpis">
      <div><div class="k">いまの作業</div><div class="st" data-out="{STAGE}"></div></div>
      <div><div class="k">進捗（金額ベース）</div><div class="v"><span data-out="done / {TOTAL} * 100" data-format="int"></span><small>%</small></div></div>
      <div><div class="k">出来高 / {TOTAL:.1f}億円</div><div class="v"><span data-out="done" data-format="dec1"></span><small>億円</small></div></div>
    </div>
    <div class="bldg" data-morph="bldg">{stack("p", WEEKS + 1, "f")}</div>
    <details class="why float"><summary>出来高の出し方</summary><div class="body">工種ごとの金額 × その工種の進み具合（週で按分）の合計。杭1.6・基礎2.2・鉄骨5.8・外装3.9・外構0.5億円。</div></details>
    <div class="foot" data-morph="foot"><span><b>サンプル建設</b>　施工計画書</span><span class="num">2</span></div>
    <aside class="notes">オレンジの「今日」の線を左右に動かすと、その週の現場の姿になります。鉄骨は1フロア3週。クレーンは建った階に合わせて継ぎ足していきます。</aside>
  </section>

  <section class="slide s-sec" data-title="断面">
    <div class="hd"><div class="kicker">02 ｜ 断面</div><h2>1階は天井高5mのロビー。<em>6階から上は北側を4m下げ</em>、住宅地への影を減らします</h2></div>
    <div class="sec-t"><p>柱は6mの格子。階高は1階 4.5m、2階から上は3.8m。</p><p>上の3層だけ北の面を下げることで、<strong>床面積を保ったまま</strong>、北の住宅地に落ちる影を短くしています。</p></div>
    <div class="bldg" data-morph="bldg">{stack("s", 24, "f")}</div>
    <div class="fl-wrap">{fl_labels}</div>
    <div class="sec-legend"><span><i style="background:#e8590c"></i>ロビー</span><span><i style="background:#f3d9b8"></i>事務所</span><span><i style="background:#b4542e"></i>鉄骨</span></div>
    <div class="foot" data-morph="foot"><span><b>サンプル建設</b>　施工計画書</span><span class="num">3</span></div>
    <aside class="notes">ページを開くと、建物が縦に切れて中が見えます。色はフロアの用途。</aside>
  </section>

  <section class="slide s-shade" data-title="日影" data-calc>
    <div class="hd"><div class="kicker">03 ｜ 日影（冬至）</div><h2>冬至の日影は、<em>北側の一部で規制の時間を超える</em>。上層をさらに下げる案と比べたい</h2></div>
    <div class="shctl">
      <div class="time num"><span data-out="round(t - 0.49)" data-format="int"></span>:<span data-out="round((t - round(t - 0.49)) * 60)" data-format="pad2"></span><small>真太陽時</small></div>
      <input type="range" name="t" min="8" max="16" step="0.25" value="8" aria-label="時刻" data-demo="1">
      <div class="ticks"><span>8:00</span><span>10:00</span><span>12:00</span><span>14:00</span><span>16:00</span></div>
      <div class="res">
        <div><div class="k">太陽の高さ</div><div class="v"><span data-out="{alt}" data-format="dec1"></span><small>°</small></div></div>
        <div><div class="k">規制を超えた範囲</div><div class="v red"><span data-out="{over}" data-format="int"></span><small>㎡</small></div></div>
      </div>
    </div>
    <div class="shade">{stack("h", len(fr), "f")}</div>
    <div class="legend">
      <span><i style="border-top:2px dashed #e8590c"></i>敷地から5m（ここから先は4時間まで）</span>
      <span><i style="border-top:2px dashed #b3261e"></i>敷地から10m（ここから先は2.5時間まで）</span>
      <span><i style="height:12px;background:#e03a1e;vertical-align:-1px"></i>8時からの日影の合計が、規制の時間を超えた所</span>
    </div>
    <details class="why float"><summary>計算の条件</summary><div class="body">東京（北緯35.68°）・冬至の8時〜16時、1分ごとに建物の影を計算して足し合わせた。測定面は地盤から4m。規制は第一種中高層住居専用地域（二）の例。16時までの合計で {FINAL_OVER:,}㎡ が超える。</div></details>
    <div class="foot" data-morph="foot"><span><b>サンプル建設</b>　施工計画書</span><span class="num">4</span></div>
    <aside class="notes">つまみで時刻を動かすと影が回り、合計の時間が規制を超えた所が赤くなります。</aside>
  </section>

  <section class="slide s-dusk" data-title="外観">
    <div class="hd"><div class="kicker">04 ｜ 完成の姿</div><h2>夕方、<em>通りから見上げた外観</em></h2></div>
    <div class="dusk-t"><ul class="list">
      <li class="step"><b>ガラスと白い方立</b>：1.5m ごとの縦の線で、重く見せない</li>
      <li class="step"><b>階ごとの白い帯</b>：床の位置をそろえ、夜は明かりの帯になる</li>
      <li class="step"><b>道路側の並木</b>：歩道に5本。ひさしの下がエントランス</li>
    </ul></div>
    <div class="bldg solid" data-morph="bldg">{stack("d", 12, "f")}</div>
    <div class="foot" data-morph="foot"><span><b>サンプル建設</b>　施工計画書</span><span class="num">5</span></div>
    <aside class="notes">日が沈んでから、フロアごとに明かりがついていきます。</aside>
  </section>

  <section class="slide s-end" data-title="決めていただきたいこと">
    <div class="hd"><div class="kicker">05 ｜ ご判断いただきたいこと</div><h2>日影の対策を、<em>次の定例までに2案から</em>お選びください</h2></div>
    <div class="ask">
      <div class="card pick"><h3>A　6階から上を、さらに北で4m下げる</h3><p>床面積は約3%減。外観の段がはっきり出ます。</p><div class="big num"><span data-count="120" data-format="int"></span><small>㎡ 減</small></div></div>
      <div class="card"><h3>B　8階をなくし、7階建てにする</h3><p>床面積は約12%減。工期は3週短くなります。</p><div class="big num"><span data-count="510" data-format="int"></span><small>㎡ 減</small></div></div>
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
'''
OUT.write_text(html)
print("wrote", OUT, len(html))
