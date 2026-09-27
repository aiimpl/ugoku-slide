(() => {
  "use strict";
  const W = 1280, H = 720;
  const deck = document.querySelector(".deck");
  if (!deck) return;
  const slides = [...deck.querySelectorAll(":scope > .slide")];
  const params = new URLSearchParams(location.search);
  const embed = params.has("embed");
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const body = document.body;
  if (embed) body.classList.add("embed");

  /* ---------- 数字の見せ方 ---------- */
  const FORMAT = {
    int: v => Math.round(v).toLocaleString("ja-JP"),
    dec1: v => (Math.round(v * 10) / 10).toLocaleString("ja-JP", { minimumFractionDigits: 1, maximumFractionDigits: 1 }),
    yen: v => (v < 0 ? "-¥" : "¥") + Math.round(Math.abs(v)).toLocaleString("ja-JP"),
    man: v => {
      const a = Math.abs(v), s = v < 0 ? "-" : "";
      if (a >= 1e8) return s + (a / 1e8).toLocaleString("ja-JP", { maximumFractionDigits: a >= 1e10 ? 0 : a >= 1e9 ? 1 : 2 }) + "億円";
      return s + (a / 1e4).toLocaleString("ja-JP", { maximumFractionDigits: a >= 1e6 ? 0 : 1 }) + "万円";
    },
    pct: v => (Math.round(v * 10) / 10).toFixed(1) + "%",
    x: v => (Math.round(v * 10) / 10).toFixed(1) + "倍",
  };
  const format = (el, v) => {
    if (!isFinite(v)) return "—";
    const f = FORMAT[el.dataset.format] || FORMAT.int;
    return f(v) + (el.dataset.unit || "");
  };
  const tween = (el, to) => {
    const from = isFinite(el._v) ? el._v : to;
    el._v = to;
    if (el.hasAttribute("data-sign")) {
      el.classList.toggle("neg", to < 0);
      el.classList.toggle("pos", to > 0);
    }
    if (reduce || from === to || !isFinite(to)) { el.textContent = format(el, to); return; }
    const t0 = performance.now(), d = 450;
    cancelAnimationFrame(el._raf);
    const tick = now => {
      const k = Math.min(1, (now - t0) / d), e = 1 - Math.pow(1 - k, 3);
      el.textContent = format(el, from + (to - from) * e);
      if (k < 1) el._raf = requestAnimationFrame(tick);
    };
    el._raf = requestAnimationFrame(tick);
  };

  /* ---------- data-calc：入力を動かすと式を計算し直す ---------- */
  const compile = expr => {
    try { return new Function("v", "with(Math){with(v){return (" + expr + ");}}"); }
    catch (e) { console.warn("式が読めません:", expr, e); return () => NaN; }
  };
  deck.querySelectorAll("[data-calc]").forEach(box => {
    const inputs = [...box.querySelectorAll("input[name],select[name]")];
    const lets = (box.dataset.let || "").split(";").map(s => s.trim()).filter(Boolean).map(s => {
      const i = s.indexOf("=");
      return [s.slice(0, i).trim(), compile(s.slice(i + 1))];
    });
    const outs = [...box.querySelectorAll("[data-out]")].map(el => [el, compile(el.dataset.out)]);
    const bars = [...box.querySelectorAll("[data-bar]")].map(el => [el, compile(el.dataset.bar), compile(el.dataset.max || "100")]);
    const shows = [...box.querySelectorAll("[data-show]")];
    const update = () => {
      const v = {};
      inputs.forEach(i => { v[i.name] = i.type === "checkbox" ? (i.checked ? 1 : 0) : Number(i.value); });
      lets.forEach(([k, f]) => { try { v[k] = f(v); } catch (e) { v[k] = NaN; } });
      const run = f => { try { return Number(f(v)); } catch (e) { return NaN; } };
      outs.forEach(([el, f]) => tween(el, run(f)));
      bars.forEach(([el, f, m]) => {
        const r = Math.max(0, Math.min(1, run(f) / run(m)));
        const fill = el.querySelector("i") || el;
        fill.style.width = (isFinite(r) ? r * 100 : 0) + "%";
      });
      shows.forEach(el => { el.textContent = format(el, v[el.dataset.show]); });
    };
    box.addEventListener("input", update);
    box.addEventListener("change", update);
    update();
  });
  // スライダーをマウスで触ったあとは、矢印キーがページ送りに戻るようにする
  deck.addEventListener("pointerup", e => {
    if (e.target.matches("input[type=range]")) setTimeout(() => e.target.blur(), 0);
  });

  /* ---------- data-count：ページを開いたときにカウントアップ ---------- */
  const counters = [...deck.querySelectorAll("[data-count]")];
  counters.forEach(el => { el._v = Number(el.dataset.count); el.textContent = format(el, el._v); });
  const countUp = slide => slide.querySelectorAll("[data-count]").forEach(el => {
    el._v = 0; tween(el, Number(el.dataset.count));
  });

  /* ---------- data-tabs：切り替え ---------- */
  deck.querySelectorAll("[data-tabs]").forEach(g => {
    const btns = [...g.querySelectorAll("[data-tab]")];
    const panels = [...g.querySelectorAll("[data-panel]")];
    const pick = k => {
      btns.forEach(b => b.setAttribute("aria-selected", String(b.dataset.tab === k)));
      panels.forEach(p => { p.hidden = p.dataset.panel !== k; });
    };
    btns.forEach(b => b.addEventListener("click", () => pick(b.dataset.tab)));
    const first = btns.find(b => b.hasAttribute("data-default")) || btns[0];
    if (first) pick(first.dataset.tab);
  });

  /* ---------- .quiz：クイズ ---------- */
  deck.querySelectorAll(".quiz").forEach(q => {
    q.querySelectorAll(".choices > button").forEach(b => b.addEventListener("click", () => {
      if (q.classList.contains("answered")) return;
      b.classList.add("picked");
      q.classList.add("answered");
    }));
  });

  /* ---------- data-rank：重みを動かすと順位が入れ替わる ---------- */
  deck.querySelectorAll("[data-rank]").forEach(box => {
    let cfg;
    try { cfg = JSON.parse(box.querySelector("script[type='application/json']").textContent); }
    catch (e) { console.warn("data-rank の JSON が読めません", e); return; }
    const wrap = document.createElement("div");
    wrap.className = "rank";
    const left = document.createElement("div");
    const right = document.createElement("div");
    right.className = "opts";
    const max = cfg.max || 5;
    const sliders = cfg.criteria.map(c => {
      const f = document.createElement("div");
      f.className = "field";
      f.innerHTML = `<label><span></span><b></b></label><input type="range" min="0" max="5" step="1">`;
      f.querySelector("span").textContent = c.label;
      const inp = f.querySelector("input");
      inp.value = c.weight;
      left.appendChild(f);
      return { c, inp, out: f.querySelector("b") };
    });
    const cards = cfg.options.map(o => {
      const d = document.createElement("div");
      d.className = "opt";
      d.innerHTML = `<div class="name"></div><div class="score"></div><div class="meter"><i></i></div><div class="note"></div>`;
      d.querySelector(".name").textContent = o.name;
      d.querySelector(".note").textContent = o.note || "";
      right.appendChild(d);
      return { o, d };
    });
    const rowH = cfg.rowHeight || 124;
    right.style.height = rowH * cards.length + "px";
    const update = () => {
      let wsum = 0;
      sliders.forEach(s => { s.out.textContent = "重み " + s.inp.value; wsum += Number(s.inp.value); });
      cards.forEach(k => {
        const raw = sliders.reduce((a, s) => a + Number(s.inp.value) * (k.o.scores[s.c.key] || 0), 0);
        k.score = wsum ? raw / (wsum * max) * 100 : 0;
      });
      [...cards].sort((a, b) => b.score - a.score).forEach((k, i) => {
        k.d.style.transform = `translateY(${i * rowH}px)`;
        k.d.classList.toggle("top", i === 0 && wsum > 0);
        const s = k.d.querySelector(".score");
        s.dataset.format = "int"; s.dataset.unit = "点";
        tween(s, k.score);
        k.d.querySelector(".meter>i").style.width = k.score + "%";
      });
    };
    left.addEventListener("input", update);
    wrap.append(left, right);
    box.appendChild(wrap);
    update();
  });

  /* ---------- pre.code：色付けと、→ で行を順番に強調 ---------- */
  const esc = s => s.replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  const KW = "const|let|var|function|return|if|else|for|while|await|async|import|from|export|def|class|new|in|of|try|catch|throw|true|false|null|undefined|True|False|None|and|or|not|with|as|yield|lambda|SELECT|FROM|WHERE|GROUP|BY|ORDER|JOIN|ON|LIMIT";
  const paint = (line, py) => {
    const re = new RegExp((py ? "(#.*$)" : "(\\/\\/.*$)") +
      "|(\"(?:\\\\.|[^\"\\\\])*\"|'(?:\\\\.|[^'\\\\])*'|`(?:\\\\.|[^`\\\\])*`)|\\b(\\d+(?:\\.\\d+)?)\\b|\\b(" + KW + ")\\b", "g");
    let out = "", last = 0, m;
    while ((m = re.exec(line))) {
      out += esc(line.slice(last, m.index));
      const cls = m[1] ? "c" : m[2] ? "s" : m[3] ? "d" : "k";
      out += `<span class="${cls}">${esc(m[0])}</span>`;
      last = re.lastIndex;
    }
    return out + esc(line.slice(last));
  };
  deck.querySelectorAll("pre.code").forEach(pre => {
    const py = /^(py|python|sh|bash|yaml)$/.test(pre.dataset.lang || "");
    const lines = pre.textContent.replace(/^\n/, "").replace(/\s+$/, "").split("\n");
    pre.innerHTML = lines.map(l => `<span class="ln">${paint(l, py) || " "}</span>`).join("");
  });
  const setHl = (pre, stage) => {
    const groups = pre.dataset.highlight.split("|");
    const lines = pre.querySelectorAll(".ln");
    const on = new Set();
    if (stage > 0) groups[stage - 1].split(",").forEach(part => {
      const [a, b] = part.split("-").map(Number);
      for (let n = a; n <= (b || a); n++) on.add(n);
    });
    pre.classList.toggle("hl-on", stage > 0);
    lines.forEach((l, i) => l.classList.toggle("hl", on.has(i + 1)));
  };

  /* ---------- ページ送りの手順（.step と コード強調） ---------- */
  const plans = slides.map(s => {
    const acts = [];
    s.querySelectorAll(".step, pre.code[data-highlight]").forEach(el => {
      if (el.matches("pre")) {
        el.dataset.highlight.split("|").forEach((_, i) =>
          acts.push({ run: () => setHl(el, i + 1), undo: () => setHl(el, i) }));
      } else {
        acts.push({
          run: () => { s.querySelectorAll(".step.current").forEach(x => x.classList.remove("current")); el.classList.add("shown", "current"); },
          undo: () => el.classList.remove("shown", "current"),
        });
      }
    });
    return acts;
  });
  const done = slides.map(() => 0);
  const setSteps = (i, n) => {
    const p = plans[i];
    while (done[i] > n) p[--done[i]].undo();
    while (done[i] < n) p[done[i]++].run();
  };

  /* ---------- 画面の部品 ---------- */
  const el = (tag, cls, html) => { const e = document.createElement(tag); e.className = cls; if (html) e.innerHTML = html; return e; };
  const bar = el("div", "ugk-bar"); deck.appendChild(bar);
  const hud = el("div", "ugk-hud", `
    <button data-a="prev" title="前へ (←)">‹</button><button data-a="next" title="次へ (→)">›</button>
    <span class="count"></span><span class="sp"></span>
    <button data-a="overview" title="一覧 (O)">一覧</button><button data-a="notes" title="メモ (N)">メモ</button>
    <button data-a="presenter" title="発表者画面 (P)">発表者</button><button data-a="full" title="全画面 (F)">⛶</button><button data-a="help" title="操作一覧 (?)">?</button>`);
  const notesBox = el("div", "ugk-notes");
  const help = el("div", "ugk-help", `<div>
    <div><kbd>→</kbd>次へ（Space / Enter でも）</div><div><kbd>←</kbd>戻る</div>
    <div><kbd>F</kbd>全画面</div><div><kbd>O</kbd>一覧（Esc で戻る）</div><div><kbd>N</kbd>発表者メモ</div>
    <div><kbd>P</kbd>発表者画面（別ウィンドウ）</div><div><kbd>B</kbd>暗転</div>
    <div><kbd>⌘P</kbd>PDF に保存（1ページ1枚）</div><div><kbd>?</kbd>この一覧</div></div>`);
  const toast = el("div", "ugk-toast");
  body.append(hud, notesBox, help, toast);
  const say = msg => { toast.textContent = msg; toast.classList.add("on"); clearTimeout(say.t); say.t = setTimeout(() => toast.classList.remove("on"), 1800); };

  /* ---------- 表示 ---------- */
  let cur = -1, overview = false, presenter = null;
  const titleOf = s => s ? (s.dataset.title || (s.querySelector("h1,h2,.big") || {}).textContent || "").trim() : "";
  const render = () => {
    slides.forEach((s, i) => {
      s.classList.toggle("active", i === cur);
      s.classList.toggle("past", i < cur);
      s.setAttribute("aria-hidden", String(i !== cur));
    });
    bar.style.width = ((cur + 1) / slides.length * 100) + "%";
    hud.querySelector(".count").textContent = `${cur + 1} / ${slides.length}`;
    const n = slides[cur].querySelector(".notes");
    notesBox.innerHTML = n ? n.innerHTML : "<span style='opacity:.6'>このスライドにはメモがありません</span>";
    drawPresenter();
  };
  const go = (i, atEnd) => {
    i = Math.max(0, Math.min(slides.length - 1, i));
    if (i === cur) return;
    const prev = cur;
    cur = i;
    setSteps(i, atEnd ? plans[i].length : 0);
    render();
    if (prev !== -1) countUp(slides[i]);
    const h = "#" + (i + 1);
    if (location.hash !== h) history.replaceState(null, "", h);
  };
  const next = () => {
    if (done[cur] < plans[cur].length) { setSteps(cur, done[cur] + 1); drawPresenter(); }
    else go(cur + 1);
  };
  const prev = () => {
    if (done[cur] > 0) { setSteps(cur, done[cur] - 1); drawPresenter(); }
    else go(cur - 1, true);
  };

  /* ---------- 大きさ合わせ・一覧 ---------- */
  const fit = () => deck.style.setProperty("--scale", Math.min(innerWidth / W, innerHeight / H));
  const layoutOverview = () => {
    const n = slides.length, gap = 24;
    const cols = Math.ceil(Math.sqrt(n * 1.1)), rows = Math.ceil(n / cols);
    const s = Math.min((W - gap * (cols + 1)) / cols / W, (H - gap * (rows + 1)) / rows / H);
    const offX = (W - cols * W * s - (cols - 1) * gap) / 2, offY = (H - rows * H * s - (rows - 1) * gap) / 2;
    slides.forEach((sl, i) => {
      sl.style.setProperty("--os", s);
      sl.style.setProperty("--ox", offX + (i % cols) * (W * s + gap) + "px");
      sl.style.setProperty("--oy", offY + Math.floor(i / cols) * (H * s + gap) + "px");
    });
  };
  const toggleOverview = on => {
    overview = on === undefined ? !overview : on;
    if (overview) layoutOverview();
    deck.classList.toggle("overview", overview);
  };
  deck.addEventListener("click", e => {
    if (!overview) return;
    const s = e.target.closest(".slide");
    if (s) { toggleOverview(false); go(slides.indexOf(s)); }
  });

  /* ---------- 全画面 ---------- */
  const full = () => {
    const d = document;
    if (d.fullscreenElement || d.webkitFullscreenElement) (d.exitFullscreen || d.webkitExitFullscreen).call(d);
    else { const r = d.documentElement; (r.requestFullscreen || r.webkitRequestFullscreen || (() => say("全画面にできません"))).call(r); }
  };

  /* ---------- 発表者画面（P）：メモ・次のスライド・経過時間 ---------- */
  let started = 0;
  const openPresenter = () => {
    const w = window.open("", "ugk-presenter", "width=960,height=600");
    if (!w) { say("ポップアップを許可してください"); return; }
    presenter = w; started = Date.now();
    w.document.open();
    w.document.write(`<!doctype html><meta charset="utf-8"><title>発表者画面</title>
      <style>body{margin:0;padding:28px 34px;background:#111317;color:#eee;font:18px/1.7 system-ui,sans-serif}
      .top{display:flex;gap:28px;align-items:baseline;border-bottom:1px solid #333;padding-bottom:14px}
      .t{font-size:44px;font-weight:700;font-variant-numeric:tabular-nums}.c{color:#999}.n{font-size:22px}
      #notes{margin-top:18px;font-size:24px;line-height:1.8}#next{margin-top:24px;color:#9aa;font-size:17px}
      button{font:inherit;background:#2a2d34;color:#eee;border:0;border-radius:8px;padding:6px 16px;margin-right:6px;cursor:pointer}</style>
      <div class="top"><span class="t" id="timer">00:00</span><span class="c" id="clock"></span><span class="n" id="pos"></span>
      <span style="flex:1"></span><button id="b">‹ 戻る</button><button id="f">次へ ›</button><button id="r">時間リセット</button></div>
      <div id="title" style="margin-top:14px;font-size:20px;color:#bbb"></div><div id="notes"></div><div id="next"></div>`);
    w.document.close();
    w.document.addEventListener("keydown", onKey);
    w.document.getElementById("b").onclick = prev;
    w.document.getElementById("f").onclick = next;
    w.document.getElementById("r").onclick = () => { started = Date.now(); };
    drawPresenter();
    clearInterval(openPresenter.t);
    openPresenter.t = setInterval(() => {
      if (!presenter || presenter.closed) { clearInterval(openPresenter.t); presenter = null; return; }
      const s = Math.floor((Date.now() - started) / 1000);
      presenter.document.getElementById("timer").textContent = String(Math.floor(s / 60)).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0");
      presenter.document.getElementById("clock").textContent = new Date().toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" });
    }, 500);
  };
  function drawPresenter() {
    if (!presenter || presenter.closed) return;
    const d = presenter.document, s = slides[cur], n = s.querySelector(".notes");
    d.getElementById("pos").textContent = `${cur + 1} / ${slides.length}` + (plans[cur].length ? `（手順 ${done[cur]} / ${plans[cur].length}）` : "");
    d.getElementById("title").textContent = titleOf(s);
    d.getElementById("notes").innerHTML = n ? n.innerHTML : "（メモなし）";
    d.getElementById("next").textContent = slides[cur + 1] ? "次：" + titleOf(slides[cur + 1]) : "最後のスライドです";
  }

  /* ---------- キーボード・スワイプ・マウス ---------- */
  function onKey(e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const t = e.target, tag = (t.tagName || "").toLowerCase();
    if (tag === "input" || tag === "select" || tag === "textarea" || t.isContentEditable) {
      if (e.key === "Escape") t.blur();
      return;
    }
    if ((e.key === " " || e.key === "Enter") && (tag === "button" || tag === "summary" || tag === "a")) return;
    const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
    const act = {
      ArrowRight: next, ArrowDown: next, PageDown: next, " ": e.shiftKey ? prev : next, Enter: next,
      ArrowLeft: prev, ArrowUp: prev, PageUp: prev, Backspace: prev,
      Home: () => go(0), End: () => go(slides.length - 1, true),
      f: full, o: () => toggleOverview(), n: () => body.classList.toggle("notes"), p: openPresenter,
      b: () => body.classList.toggle("black"), "?": () => body.classList.toggle("help"),
      Escape: () => { if (body.classList.contains("help")) body.classList.remove("help"); else toggleOverview(false); },
    }[k];
    if (act) { e.preventDefault(); act(); }
  }
  document.addEventListener("keydown", onKey);
  hud.addEventListener("click", e => {
    const a = e.target.closest("button")?.dataset.a;
    ({ prev, next, overview: () => toggleOverview(), notes: () => body.classList.toggle("notes"),
       presenter: openPresenter, full, help: () => body.classList.toggle("help") }[a] || (() => {}))();
  });
  help.addEventListener("click", () => body.classList.remove("help"));
  let tx = 0, ty = 0, tOk = false;
  deck.addEventListener("touchstart", e => {
    tOk = !e.target.closest("input,button,summary,select,a,[data-tab]");
    tx = e.touches[0].clientX; ty = e.touches[0].clientY;
  }, { passive: true });
  deck.addEventListener("touchend", e => {
    if (!tOk) return;
    const dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.3) (dx < 0 ? next : prev)();
  }, { passive: true });
  let idle;
  const wake = () => { body.classList.add("ui"); clearTimeout(idle); idle = setTimeout(() => body.classList.remove("ui"), 2400); };
  addEventListener("mousemove", wake);
  addEventListener("touchstart", wake, { passive: true });

  /* ---------- 印刷：補足を全部開き、順番出しも全部見せる ---------- */
  let reopened = [];
  addEventListener("beforeprint", () => {
    reopened = [...deck.querySelectorAll("details.why:not([open])")];
    reopened.forEach(d => { d.open = true; });
  });
  addEventListener("afterprint", () => { reopened.forEach(d => { d.open = false; }); reopened = []; });

  /* ---------- 一覧ページの見本表示から操作する ---------- */
  addEventListener("message", e => {
    const m = e.data && e.data.ugk;
    if (m === "next") { if (cur >= slides.length - 1) go(0); else go(cur + 1, true); }
    else if (m === "first") go(0);
  });

  addEventListener("resize", () => { fit(); if (overview) layoutOverview(); });
  addEventListener("hashchange", () => { const n = parseInt(location.hash.slice(1), 10); if (n) go(n - 1, true); });
  fit();
  const start = parseInt(location.hash.slice(1), 10);
  go(start ? start - 1 : 0, !!start);
})();
