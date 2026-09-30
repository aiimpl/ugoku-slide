(() => {
  "use strict";
  const W = 1280, H = 720;
  const deck = document.querySelector(".deck");
  if (!deck) return;
  const slides = [...deck.querySelectorAll(":scope > .slide")];
  const params = new URLSearchParams(location.search);
  const embed = params.has("embed");
  const still = params.has("static"); // ?static：動きを止め、全部を出す
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const body = document.body;
  if (embed) body.classList.add("embed");
  if (still) body.classList.add("static");

  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

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
    pad2: v => String(Math.round(v)).padStart(2, "0"),
    year: v => String(Math.round(v)),
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
      const k = el.dataset.sign === "rev" ? -1 : 1; // data-sign="rev"：マイナスを緑にする
      el.classList.toggle("neg", to * k < 0);
      el.classList.toggle("pos", to * k > 0);
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
  // data-calc="global" の値は、ほかのページ（data-global-out）でも使える
  const G = {};
  const globalOuts = [...deck.querySelectorAll("[data-global-out]")].map(el => [el, compile(el.dataset.globalOut)]);
  const updateGlobal = () => globalOuts.forEach(([el, f]) => {
    let x; try { x = f(G); } catch (e) { x = NaN; }
    if (typeof x === "string") el.textContent = x; else tween(el, Number(x));
  });
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
      inputs.forEach(i => {
        if (i.type === "radio") { if (i.checked) v[i.name] = Number(i.value); else if (!(i.name in v)) v[i.name] = NaN; return; }
        v[i.name] = i.type === "checkbox" ? (i.checked ? 1 : 0) : Number(i.value);
      });
      lets.forEach(([k, f]) => { try { v[k] = f(v); } catch (e) { v[k] = NaN; } });
      const run = f => { try { return Number(f(v)); } catch (e) { return NaN; } };
      outs.forEach(([el, f]) => {
        let x; try { x = f(v); } catch (e) { x = NaN; }
        if (typeof x === "string") el.textContent = x; else tween(el, Number(x)); // 文字を返す式なら文字を出す
      });
      bars.forEach(([el, f, m]) => {
        const r = Math.max(0, Math.min(1, run(f) / run(m)));
        const fill = el.querySelector("i") || el;
        fill.style.width = (isFinite(r) ? r * 100 : 0) + "%";
      });
      shows.forEach(el => { el.textContent = format(el, v[el.dataset.show]); });
      // 値は CSS 変数 --名前 にも入る（図形を動かせる）
      Object.keys(v).forEach(k => { if (isFinite(v[k])) box.style.setProperty("--" + k, v[k]); });
      if (box.dataset.calc === "global") {
        Object.assign(G, v);
        Object.keys(v).forEach(k => { if (isFinite(v[k])) deck.style.setProperty("--" + k, v[k]); });
        updateGlobal();
      }
    };
    box.addEventListener("input", update);
    box.addEventListener("change", update);
    update();
  });
  deck.addEventListener("change", e => { if (e.target.matches("select")) e.target.blur(); });
  // 入力を触ったあとも、矢印キーでページを送れるようにする
  deck.addEventListener("pointerup", e => {
    if (e.target.matches("input[type=range],input[type=checkbox],input[type=radio]")) setTimeout(() => e.target.blur(), 0);
    else if (e.target.closest("label") && e.target.closest("label").querySelector("input[type=checkbox],input[type=radio]")) setTimeout(() => document.activeElement && document.activeElement.blur && document.activeElement.blur(), 0);
  });

  /* ---------- data-count：ページを開いたときにカウントアップ ---------- */
  const counters = [...deck.querySelectorAll("[data-count]")];
  counters.forEach(el => { el._v = Number(el.dataset.count); el.textContent = format(el, el._v); });
  const countUp = (slide, skip) => {
    slide.querySelectorAll("[data-count]").forEach(el => {
      if (skip && skip.has(el)) return;
      el._v = 0; tween(el, Number(el.dataset.count));
    });
    // ほかのページで決まった数字（data-global-out）も、開いたときに数え上がる
    let any = false;
    globalOuts.forEach(([el]) => { if (slide.contains(el) && !(skip && skip.has(el))) { el._v = 0; any = true; } });
    if (any) updateGlobal();
  };

  /* ---------- .draw：SVG の線が、表示されたときに描かれていく ---------- */
  deck.querySelectorAll(".draw").forEach(p => { if (p instanceof SVGGeometryElement) p.setAttribute("pathLength", "1"); });

  /* ---------- data-orbit：ドラッグで回せる立体（CSS の 3D） ---------- */
  const orbits = [];
  deck.querySelectorAll("[data-orbit]").forEach(box => {
    const rx0 = Number(box.dataset.rx || -22), ry0 = Number(box.dataset.ry || 32);
    const o = { box, rx: rx0, ry: ry0, spin: box.hasAttribute("data-spin") && !reduce };
    const set = () => { box.style.setProperty("--rx", o.rx.toFixed(2)); box.style.setProperty("--ry", o.ry.toFixed(2)); };
    let drag = null;
    box.addEventListener("pointerdown", e => {
      if (e.target.closest("input,button,summary,select,a")) return;
      drag = { x: e.clientX, y: e.clientY, rx: o.rx, ry: o.ry };
      o.spin = false;
      try { box.setPointerCapture(e.pointerId); } catch (err) { /* 合成した操作など */ }
      box.classList.add("grabbing");
    });
    box.addEventListener("pointermove", e => {
      if (!drag) return;
      const k = Number(deck.style.getPropertyValue("--scale")) || 1;
      o.ry = drag.ry + (e.clientX - drag.x) / k * 0.45;
      o.rx = Math.max(-85, Math.min(85, drag.rx - (e.clientY - drag.y) / k * 0.45));
      set();
    });
    const end = () => { drag = null; box.classList.remove("grabbing"); };
    box.addEventListener("pointerup", end);
    box.addEventListener("pointercancel", end);
    box.addEventListener("dblclick", () => { o.rx = rx0; o.ry = ry0; set(); });
    o.set = set;
    set();
    orbits.push(o);
  });
  if (orbits.some(o => o.spin)) {
    let last = performance.now();
    const loop = now => {
      const dt = Math.min(64, now - last); last = now;
      orbits.forEach(o => {
        if (o.spin && o.box.closest(".slide.active")) { o.ry += dt * 0.012; o.set(); }
      });
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }

  /* ---------- data-sheet：表を直す・貼ると、グラフと集計を作り直す ---------- */
  // 「1,200」「▲300」「1.2億」を数にする（単位は読み飛ばす）
  const parseNum = s => {
    const t = String(s).trim().replace(/[−－―]/g, "-").replace(/^[▲△]/, "-").replace(/[,，¥￥\s]/g, "")
      .replace(/[０-９．]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFEE0));
    const m = t.match(/^[-+]?(\d+\.?\d*|\.\d+)(e[-+]?\d+)?/i);
    return m ? Number(m[0]) : NaN;
  };
  // 目盛りは 1・2・2.5・5 の区切りで、3〜5本
  const niceScale = (m, lo = 0) => {
    if (!(m > lo)) m = lo + 1;
    const raw = (m - lo) / 4, p = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / p;
    const step = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * p;
    const a = Math.floor(lo / step + 1e-9) * step, b = Math.max(a + 2 * step, Math.ceil(m / step - 1e-9) * step);
    const n = Math.round((b - a) / step);
    return { min: a, max: b, ticks: Array.from({ length: n + 1 }, (_, i) => i / n) };
  };
  const sheets = [];
  deck.querySelectorAll("[data-sheet]").forEach(fig => {
    const table = fig.querySelector("table");
    if (!table) return;
    const initial = table.innerHTML;
    const kind = fig.dataset.chart || "bar";
    let chart = fig.querySelector(".sheet-chart");
    if (!chart) { chart = document.createElement("div"); chart.className = "sheet-chart"; fig.appendChild(chart); }
    const axisFmt = { dataset: { format: fig.dataset.format || "int", unit: "" } };
    const read = () => {
      const head = [...table.querySelectorAll("thead th")].slice(1).map(th => th.textContent.trim());
      const rows = [...table.querySelectorAll("tbody tr")].map(tr => {
        const c = [...tr.children];
        return { label: c[0] ? c[0].textContent.trim() : "", vals: c.slice(1).map(td => parseNum(td.textContent)) };
      });
      const n = Math.max(head.length, ...rows.map(r => r.vals.length), 0);
      while (head.length < n) head.push("系列" + (head.length + 1));
      return { head, rows };
    };
    const prep = () => {
      table.querySelectorAll("tbody td").forEach((td, i) => {
        if (td.cellIndex === 0) return;
        try { td.contentEditable = "plaintext-only"; } catch (e) { /* 古いブラウザ */ }
        if (td.contentEditable !== "plaintext-only") td.contentEditable = "true";
        td.classList.add("n");
        td.spellcheck = false;
      });
    };
    const outs = [...fig.querySelectorAll("[data-sheet-out]")].map(el => [el, (() => {
      try { return new Function("h", "with(Math){with(h){return (" + el.dataset.sheetOut + ");}}"); }
      catch (e) { console.warn("式が読めません:", el.dataset.sheetOut); return () => NaN; }
    })()]);
    let prevVals = null, shape = "";
    const render = () => {
    if (body.classList.contains("marking")) setTimeout(() => drawMarks());
      const d = read();
      const S = d.head.length, R = d.rows.length;
      const val = (r, s) => { const x = d.rows[r].vals[s]; return isFinite(x) ? x : 0; };
      let max = 0, min = 0;
      for (let r = 0; r < R; r++) {
        if (kind === "stack") { let t = 0; for (let s = 0; s < S; s++) t += Math.max(0, val(r, s)); max = Math.max(max, t); }
        else for (let s = 0; s < S; s++) { max = Math.max(max, val(r, s)); min = Math.min(min, val(r, s)); }
      }
      // data-min：目盛りの下限
      if (kind !== "stack" && fig.dataset.min !== undefined && isFinite(Number(fig.dataset.min))) min = Math.min(Number(fig.dataset.min), ...d.rows.flatMap(r => r.vals.filter(isFinite)));
      const sc = niceScale(max * 1.02, min);
      max = sc.max; const lo = sc.min, span = max - lo, base = Math.max(lo, Math.min(0, max));
      const yOf = v => (v - lo) / span;
      const sh = kind + R + "x" + S + "/" + sc.ticks.length + d.rows.map(r => r.label).join("|") + d.head.join("|");
      if (sh !== shape) {
        shape = sh;
        const grid = sc.ticks.map(k => `<div class="sc-gl" style="bottom:${k * 100}%"><span></span></div>`).join("") +
          (lo < 0 ? `<div class="sc-zero" style="bottom:${yOf(0) * 100}%"></div>` : "");
        const legend = S > 1 ? `<div class="sc-legend">${d.head.map((h, s) => `<span style="--c:var(--s${s + 1})"><i></i>${esc(h)}</span>`).join("")}</div>` : "";
        let plot = "";
        if (kind === "line") {
          plot = `<svg class="sc-lines" viewBox="0 0 1000 1000" preserveAspectRatio="none">${d.head.map((_, s) => `<polyline style="--c:var(--s${s + 1})" vector-effect="non-scaling-stroke"/>`).join("")}</svg>` +
            d.head.map((_, s) => d.rows.map(() => `<b class="sc-dot" style="--c:var(--s${s + 1})"></b>`).join("")).join("");
        }
        const groups = d.rows.map(r => `<div class="sc-g">${kind === "line" ? "" : `<div class="sc-bars">${d.head.map((_, s) => `<i style="--c:var(--s${s + 1})"><em></em></i>`).join("")}</div>`}<span class="sc-l">${esc(r.label)}</span></div>`).join("");
        chart.className = "sheet-chart sc-" + kind + (S > 1 ? " multi" : "");
        chart.innerHTML = `${legend}<div class="sc-plot">${grid}<div class="sc-groups">${groups}</div>${plot}</div>`;
        prevVals = null;
      }
      chart.querySelectorAll(".sc-gl span").forEach((sp, i) => { sp.textContent = format(axisFmt, lo + span * sc.ticks[i]); });
      if (kind === "line") {
        const from = prevVals, to = d.rows.map((_, r) => d.head.map((_, s) => val(r, s)));
        prevVals = to;
        const draw = k => {
          const pl = chart.querySelectorAll(".sc-lines polyline"), dots = chart.querySelectorAll(".sc-dot");
          d.head.forEach((_, s) => {
            const pts = to.map((row, r) => {
              const v = from ? from[r][s] + (row[s] - from[r][s]) * k : row[s];
              const x = R > 1 ? (r + .5) / R : .5, y = 1 - yOf(v);
              const dot = dots[s * R + r];
              if (dot) { dot.style.left = x * 100 + "%"; dot.style.top = y * 100 + "%"; dot.title = format(axisFmt, row[s]); }
              return (x * 1000).toFixed(1) + "," + (y * 1000).toFixed(1);
            });
            if (pl[s]) pl[s].setAttribute("points", pts.join(" "));
          });
        };
        if (!from || reduce) draw(1);
        else { const t0 = performance.now(); const tick = now => { const k = Math.min(1, (now - t0) / 500); draw(1 - Math.pow(1 - k, 3)); if (k < 1) requestAnimationFrame(tick); }; requestAnimationFrame(tick); }
      } else {
        chart.querySelectorAll(".sc-g").forEach((g, r) => {
          let acc = 0;
          g.querySelectorAll(".sc-bars > i").forEach((b, s) => {
            const raw = val(r, s);
            let from, to;
            if (kind === "stack") { const v = Math.max(0, raw); from = acc; to = acc + v; acc = to; }
            else { from = Math.min(raw, base); to = Math.max(raw, base); }
            b.style.setProperty("--b", (yOf(from) * 100).toFixed(3));
            b.style.setProperty("--h", ((to - from) / span * 100).toFixed(3));
            b.style.setProperty("--x", kind === "stack" ? 0 : (s / S * 100).toFixed(3));
            b.style.setProperty("--w", kind === "stack" ? 100 : (100 / S).toFixed(3));
            b.classList.toggle("neg", kind !== "stack" && raw < base);
            b.querySelector("em").textContent = format(axisFmt, raw);
          });
        });
      }
      const col = name => { const s = typeof name === "number" ? name : d.head.indexOf(name); return s < 0 ? [] : d.rows.map(r => r.vals[s]).filter(isFinite); };
      const h = {
        col, n: R,
        sum: c => col(c).reduce((a, b) => a + b, 0),
        avg: c => { const a = col(c); return a.length ? a.reduce((x, y) => x + y, 0) / a.length : NaN; },
        first: c => col(c)[0], last: c => { const a = col(c); return a[a.length - 1]; },
        max: c => Math.max(...col(c)), min: c => Math.min(...col(c)),
        growth: c => { const a = col(c); return a.length > 1 && a[0] ? (a[a.length - 1] / a[0] - 1) * 100 : NaN; },
        total: () => d.rows.reduce((a, r) => a + r.vals.filter(isFinite).reduce((x, y) => x + y, 0), 0),
        label: i => (d.rows[i < 0 ? R + i : i] || {}).label || "",
      };
      outs.forEach(([el, f]) => {
        let x; try { x = f(h); } catch (e) { x = NaN; }
        if (typeof x === "string") el.textContent = x; else tween(el, Number(x));
      });
    };
    const fromText = text => {
      const lines = text.replace(/\r/g, "").split("\n").filter(l => l.trim() !== "");
      if (!lines.length) return false;
      const sep = lines.some(l => l.includes("\t")) ? "\t" : ",";
      const cells = lines.map(l => l.split(sep).map(c => c.trim().replace(/^"(.*)"$/, "$1")));
      if (cells[0].length < 2) return false;
      const hasHead = cells[0].slice(1).some(c => !isFinite(parseNum(c)));
      const head = hasHead ? cells.shift() : ["", ...read().head];
      if (!cells.length) return false;
      const cols = Math.max(...cells.map(r => r.length));
      table.innerHTML = `<thead><tr>${Array.from({ length: cols }, (_, i) => `<th>${esc(head[i] || (i ? "系列" + i : ""))}</th>`).join("")}</tr></thead>` +
        `<tbody>${cells.map(r => `<tr>${Array.from({ length: cols }, (_, i) => {
          const x = parseNum(r[i] || "");
          return `<td>${i && isFinite(x) ? x.toLocaleString("ja-JP") : esc(r[i] || "")}</td>`;
        }).join("")}</tr>`).join("")}</tbody>`;
      prep(); render();
      return true;
    };
    let tm;
    table.addEventListener("input", () => { clearTimeout(tm); tm = setTimeout(render, 120); });
    table.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); e.target.blur(); } });
    const onPaste = e => {
      const text = (e.clipboardData || window.clipboardData).getData("text");
      if (!/[\t,\n]/.test(text.trim())) return; // 数字1つだけならそのセルに貼る
      e.preventDefault();
      if (fromText(text)) say("貼った表で、グラフと集計を作り直しました");
      else say("表として読めませんでした（1列目に項目名、2列目から数字）");
    };
    fig.addEventListener("paste", onPaste);
    const pad = document.createElement("textarea");
    pad.className = "sheet-pad"; pad.setAttribute("aria-label", "ここに表を貼る");
    fig.appendChild(pad);
    fig.querySelectorAll("[data-sheet-paste]").forEach(b => b.addEventListener("click", () => { pad.value = ""; pad.focus(); say("Excel やスプレッドシートでコピーした表を ⌘V / Ctrl+V で貼ってください"); }));
    pad.addEventListener("blur", () => { pad.value = ""; });
    fig.querySelectorAll("[data-sheet-reset]").forEach(b => b.addEventListener("click", () => { table.innerHTML = initial; prep(); render(); }));
    prep(); render();
    sheets.push({ fig, onPaste });
  });
  // どこにもフォーカスがないときの貼り付けは、表示中のスライドの表へ
  document.addEventListener("paste", e => {
    const t = e.target;
    if (t.closest && t.closest("[data-sheet],input,textarea,[contenteditable]")) return;
    const s = sheets.find(x => x.fig.closest(".slide.active"));
    if (s) s.onPaste(e);
  });

  /* ---------- details.why.float：下にはみ出すなら上へ開く ---------- */
  deck.querySelectorAll("details.why.float").forEach(d => d.addEventListener("toggle", () => {
    if (!d.open) return;
    d.classList.remove("up");
    const s = d.closest(".slide"), b = d.querySelector(".body");
    if (!s || !b) return;
    const k = s.getBoundingClientRect().height / H || 1;
    if ((b.getBoundingClientRect().bottom - s.getBoundingClientRect().top) / k > H - 12) d.classList.add("up");
  }));

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
    <button data-a="demo" title="自動で見せる (D)">デモ</button><button data-a="mark" title="囲んで直す指示を作る (E)">直す</button>
    <button data-a="presenter" title="発表者画面 (P)">発表者</button><button data-a="full" title="全画面 (F)">⛶</button><button data-a="help" title="操作一覧 (?)">?</button>`);
  const notesBox = el("div", "ugk-notes");
  const help = el("div", "ugk-help", `<div>
    <div><kbd>→</kbd>次へ（Space / Enter でも）</div><div><kbd>←</kbd>戻る</div>
    <div><kbd>F</kbd>全画面</div><div><kbd>O</kbd>一覧（Esc で戻る）</div><div><kbd>N</kbd>発表者メモ</div>
    <div><kbd>P</kbd>発表者画面（別ウィンドウ）</div><div><kbd>B</kbd>暗転</div>
    <div><kbd>D</kbd>自動で見せる（何か押すと止まる）</div><div><kbd>E</kbd>囲んで直す指示を作る</div>
    <div><kbd>3</kbd><kbd>↵</kbd>数字でそのページへ</div>
    <div><kbd>⌘P</kbd>PDF に保存（1ページ1枚）</div><div><kbd>?</kbd>この一覧</div></div>`);
  const toast = el("div", "ugk-toast");
  body.append(hud, notesBox, help, toast);
  const say = msg => { toast.textContent = msg; toast.classList.add("on"); clearTimeout(say.t); say.t = setTimeout(() => toast.classList.remove("on"), 1800); };

  /* ---------- 表示 ---------- */
  let cur = -1, overview = false, presenter = null;
  const titleOf = s => s ? (s.dataset.title || (s.querySelector("h1,h2,.big") || {}).textContent || "").trim() : "";
  const render = () => {
    if (body.classList.contains("marking")) setTimeout(() => drawMarks());
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
  /* ---------- data-morph：前後のページで同じ名前の要素を変形させてつなぐ ---------- */
  const morphMode = deck.dataset.transition === "morph";
  const MORPH_MS = 900, MORPH_EASE = "cubic-bezier(.65,0,.25,1)";
  const shownIn = (el, slide) => { for (let e = el; e && e !== slide; e = e.parentElement) if (e.classList.contains("step") && !e.classList.contains("shown")) return false; return true; };
  // 見えている位置（アニメーション中なら途中の位置）
  const seenRect = (el, slide) => {
    const r = el.getBoundingClientRect(), s = slide.getBoundingClientRect(), k = s.width / W || 1;
    return { x: (r.left - s.left) / k, y: (r.top - s.top) / k, w: r.width / k, h: r.height / k };
  };
  // 置かれた場所（transform を無視。まだ出ていないページ用）
  const layoutRect = (el, slide) => {
    let x = 0, y = 0, e = el;
    while (e && e !== slide) { x += e.offsetLeft; y += e.offsetTop; const p = e.offsetParent; if (p && p !== slide && !slide.contains(p)) break; e = p; }
    return { x, y, w: el.offsetWidth, h: el.offsetHeight };
  };
  // 見えているままの写し（計算済みの見た目を書き込む）
  const snapshot = (el, a) => {
    const c = el.cloneNode(true);
    const copy = (src, dst) => {
      if (!(src instanceof Element)) return;
      const cs = getComputedStyle(src);
      for (let i = 0; i < cs.length; i++) dst.style.setProperty(cs[i], cs.getPropertyValue(cs[i]));
      dst.style.animation = "none"; dst.style.transition = "none";
      ["data-morph", "data-count", "data-out", "data-show", "id", "data-morph-enter"].forEach(k => dst.removeAttribute && dst.removeAttribute(k));
      for (let i = 0; i < src.children.length; i++) copy(src.children[i], dst.children[i]);
    };
    copy(el, c);
    Object.assign(c.style, { position: "absolute", margin: "0", right: "auto", bottom: "auto", width: a.w + "px", height: a.h + "px",
      transform: "none", transformOrigin: "50% 50%", pointerEvents: "none", zIndex: "0", visibility: "visible", opacity: "1" });
    c.classList.add("ugk-ghost");
    c.setAttribute("aria-hidden", "true");
    return c;
  };
  const LOOK = ["backgroundColor", "color", "borderTopLeftRadius", "borderTopRightRadius", "borderBottomLeftRadius", "borderBottomRightRadius", "opacity", "borderColor"];
  const measureMorph = (from, to) => {
    const pairs = [];
    const olds = new Map();
    from.querySelectorAll("[data-morph]").forEach(el => {
      if (!shownIn(el, from) || !el.offsetWidth) return;
      if (parseFloat(getComputedStyle(el).opacity) < .05) return;
      olds.set(el.dataset.morph, el);
    });
    to.querySelectorAll("[data-morph]").forEach(el => {
      const o = olds.get(el.dataset.morph);
      if (!o || !(el instanceof HTMLElement) || !el.offsetWidth) return;
      const cs = getComputedStyle(o);
      const a = seenRect(o, from);
      const counting = o.hasAttribute("data-count") && el.hasAttribute("data-count");
      // 数え直す数字は写しを作らない（二重に見えるため）
      const same = counting || (o.innerHTML === el.innerHTML && cs.backgroundImage === getComputedStyle(el).backgroundImage);
      pairs.push({ o, n: el, a, look: LOOK.reduce((m, k) => (m[k] = cs[k], m), {}), same,
        ghost: same ? null : snapshot(o, a), count: counting ? o._v : null });
    });
    return pairs;
  };
  const runMorph = (pairs, to) => {
    const skip = new Set();
    pairs.forEach(p => {
      if (!shownIn(p.n, to)) return;
      const b = layoutRect(p.n, to), a = p.a;
      if (!b.w || !b.h) return;
      const leaf = !p.n.firstElementChild && p.n.textContent.trim() !== "";
      let sx = a.w / b.w, sy = a.h / b.h;
      if (leaf) sx = sy = a.h / b.h; // 文字は縦横比を保って拡大縮小する
      const dx = (a.x + a.w / 2) - (b.x + b.w / 2), dy = (a.y + a.h / 2) - (b.y + b.h / 2);
      const cs = getComputedStyle(p.n);
      const own = cs.transform === "none" ? "" : " " + cs.transform;
      const start = { transform: `translate(${dx}px,${dy}px) scale(${sx},${sy})${own}` }, end = { transform: own.trim() || "none" };
      LOOK.forEach(k => { if (k !== "opacity" && p.look[k] !== cs[k]) { start[k] = p.look[k]; end[k] = cs[k]; } });
      if (/Radius/.test(Object.keys(start).join())) ["borderTopLeftRadius", "borderTopRightRadius", "borderBottomLeftRadius", "borderBottomRightRadius"].forEach(k => {
        if (start[k] === undefined) { start[k] = p.look[k]; end[k] = cs[k]; }
      });
      const delay = Number(p.n.dataset.morphDelay || 0);
      p.n.style.visibility = ""; // すばやく戻ったときの隠れっぱなしを防ぐ
      p.n.getAnimations().forEach(x => x.id === "ugk-morph" && x.cancel());
      // 後片付けはアニメーションの終わりで（ゆっくり再生でも崩れない）
      const after = (anim, fn) => anim.finished.then(fn, fn);
      if (p.same) {
        const an = p.n.animate([start, end], { duration: MORPH_MS, delay, easing: MORPH_EASE, fill: "backwards" });
        an.id = "ugk-morph";
        p.o.style.visibility = "hidden";
        after(an, () => { p.o.style.visibility = ""; });
      } else {
        // 中身がちがう：前の形の写しを下に敷き、新しい方が出てから消す
        const g = p.ghost;
        g.style.left = a.x + "px"; g.style.top = a.y + "px";
        to.insertBefore(g, to.firstChild);
        const gsy = b.h / a.h, gsx = leaf ? gsy : b.w / a.w;
        const toB = `translate(${-dx}px,${-dy}px) scale(${gsx},${gsy})`;
        after(g.animate([{ transform: "none", opacity: 1 }, { opacity: 1, offset: .4 }, { transform: toB, opacity: 0 }], { duration: MORPH_MS, delay, easing: MORPH_EASE, fill: "both" }), () => g.remove());
        const an = p.n.animate([{ ...start, opacity: 0 }, { opacity: 1, offset: .45 }, end], { duration: MORPH_MS, delay, easing: MORPH_EASE, fill: "backwards" });
        an.id = "ugk-morph";
        p.o.style.visibility = "hidden";
        after(an, () => { p.o.style.visibility = ""; });
      }
      if (p.count !== null && isFinite(p.count)) { p.n._v = p.count; tween(p.n, Number(p.n.dataset.count)); skip.add(p.n); }
    });
    return skip;
  };

  const go = (i, atEnd) => {
    i = Math.max(0, Math.min(slides.length - 1, i));
    if (i === cur) return;
    const prev = cur;
    const canMorph = morphMode && prev !== -1 && !reduce && !overview && !still;
    const pairs = canMorph ? measureMorph(slides[prev], slides[i]) : [];
    cur = i;
    setSteps(i, atEnd || still ? plans[i].length : 0);
    const skip = pairs.length && !still ? runMorph(pairs, slides[i]) : null;
    render();
    if (prev !== -1) countUp(slides[i], skip);
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


  /* ---------- 数字でページへ（3 → 3枚目、12 → 12枚目。Enter ですぐ） ---------- */
  let digits = "", digitT;
  const jump = () => { const n = parseInt(digits, 10); digits = ""; if (n) go(n - 1); };
  const typeDigit = d => {
    digits += d; say(`${digits} 枚目へ`);
    clearTimeout(digitT); digitT = setTimeout(jump, 700);
  };

  /* ---------- 自動デモ（D）：各ページで操作を1つ見せ、最後は一覧 ---------- */
  // 見せる操作：data-demo の番号順。無ければ スライダー→タブ→クイズ→立体→根拠 から1つ
  const cursor = el("div", "ugk-cursor", `<svg viewBox="0 0 24 24" width="30" height="30"><path d="M4 2v17l4.6-4.2 3 6.6 3-1.4-2.9-6.4H18z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>`);
  deck.appendChild(cursor);
  let demoOn = false;
  // 待つ時間はページの時計で測る（裏のタブでは止まる。撮影でゆっくり再生しても合う）
  const sleep = ms => new Promise(r => { const end = performance.now() + ms; const f = () => performance.now() >= end ? r() : requestAnimationFrame(f); f(); });
  const place = (x, y) => { cursor.style.transform = `translate(${x}px,${y}px)`; };
  const aim = async target => { // 要素の真ん中へカーソルを動かす
    const r = target.getBoundingClientRect(), d = deck.getBoundingClientRect(), k = d.width / W;
    place((r.left + r.width / 2 - d.left) / k, (r.top + r.height / 2 - d.top) / k);
    await sleep(520);
  };
  const tap = async target => { await aim(target); cursor.classList.add("tap"); await sleep(160); cursor.classList.remove("tap"); target.click(); };
  const sweep = async (inp, to, ms) => { // スライダーを to まで動かす
    const from = Number(inp.value), t0 = performance.now();
    await aim(inp);
    while (demoOn) {
      const k = Math.min(1, (performance.now() - t0) / ms);
      const v = from + (to - from) * (1 - Math.pow(1 - k, 3)), step = Number(inp.step) || 1;
      inp.value = Math.round(v / step) * step;
      inp.dispatchEvent(new Event("input", { bubbles: true }));
      if (k >= 1) break;
      await sleep(16);
    }
  };
  const demoPick = s => {
    const marked = [...s.querySelectorAll("[data-demo]")].sort((a, b) => a.dataset.demo - b.dataset.demo);
    if (marked.length) return marked;
    const q = sel => s.querySelector(sel);
    return [q("[data-calc] input[type=range], .rank input[type=range]") || q("[data-tabs] [data-tab]:nth-of-type(2)") ||
      q(".quiz .choices > button[data-correct]") || q("[data-orbit]") || q("details.why > summary")].filter(Boolean);
  };
  const demoAct = async t => {
    if (t.matches("input[type=range]")) {
      const v0 = Number(t.value), hi = Number(t.max), lo = Number(t.min);
      await sweep(t, v0 + (hi - v0) * 0.8, 1100); await sleep(500);
      await sweep(t, v0 - (v0 - lo) * 0.5, 900); await sleep(400); await sweep(t, v0, 600);
    } else if (t.matches("[data-orbit]")) {
      await aim(t);
      const o = orbits.find(x => x.box === t), ry = o.ry;
      for (let k = 0; k <= 60 && demoOn; k++) { o.ry = ry + 90 * Math.sin(k / 60 * Math.PI); o.set(); await sleep(22); }
    } else if (t.matches("summary")) {
      await tap(t); await sleep(1600); if (demoOn) t.click();
    } else { await tap(t); }
    await sleep(900);
  };
  const demo = async () => {
    if (demoOn) return stopDemo();
    demoOn = true; body.classList.add("demo"); toggleOverview(false);
    place(W - 80, H - 60); go(0);
    for (let i = 0; i < slides.length && demoOn; i++) {
      if (i) { go(i); }
      await sleep(1300);
      while (demoOn && done[cur] < plans[cur].length) { next(); await sleep(750); }
      for (const t of demoPick(slides[cur])) { if (!demoOn) break; await demoAct(t); }
    }
    if (demoOn) toggleOverview(true);
    stopDemo();
  };
  const stopDemo = () => { demoOn = false; body.classList.remove("demo"); };
  ["keydown", "pointerdown", "wheel"].forEach(ev => addEventListener(ev, e => {
    if (demoOn && e.isTrusted && !(ev === "keydown" && e.key.toLowerCase() === "d")) stopDemo();
  }, true));

  /* ---------- 囲んで直す（E）：スライドの上を囲むと、Claude に渡す直しの指示が作れる ---------- */
  const markLayer = el("div", "ugk-mark");
  const markPanel = el("div", "ugk-markpanel", `<b>直したい所をドラッグで囲む</b><ol></ol>
    <form class="ask" hidden><input placeholder="どう直す？（例：文字を大きく）" aria-label="どう直すか"><button>追加</button></form>
    <div class="row"><button data-m="copy">指示をコピー</button><button data-m="clear">全部消す</button><button data-m="close">閉じる</button></div>`);
  const askForm = markPanel.querySelector(".ask"), askInput = askForm.querySelector("input");
  let pending = null; // 囲んだけれど、まだ指示を書いていない範囲
  deck.appendChild(markLayer); body.appendChild(markPanel);
  const marks = [];
  const slideXY = e => { const d = deck.getBoundingClientRect(), k = d.width / W; return [(e.clientX - d.left) / k, (e.clientY - d.top) / k]; };
  const textsIn = (s, r) => { // 囲んだ中にある文字（先頭2つ）
    const d = deck.getBoundingClientRect(), k = d.width / W, out = [];
    s.querySelectorAll("*").forEach(e => {
      if (out.length >= 2 || e.closest(".notes")) return;
      if (![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return;
      const b = e.getBoundingClientRect(), cx = (b.left + b.width / 2 - d.left) / k, cy = (b.top + b.height / 2 - d.top) / k;
      if (b.width && cx >= r.x && cx <= r.x + r.w && cy >= r.y && cy <= r.y + r.h) out.push(e.textContent.trim().replace(/\s+/g, " ").slice(0, 24));
    });
    return out;
  };
  const drawMarks = () => {
    markLayer.querySelectorAll(".box:not(.pending)").forEach(b => b.remove());
    if (!pending) markLayer.querySelectorAll(".box.pending").forEach(b => b.remove());
    marks.forEach((m, j) => {
      if (m.page !== cur) return;
      const b = el("div", "box", `<i>${j + 1}</i>`);
      Object.assign(b.style, { left: m.x + "px", top: m.y + "px", width: m.w + "px", height: m.h + "px" });
      markLayer.appendChild(b);
    });
    markPanel.querySelector("ol").innerHTML = marks.map(m => `<li><span>${m.page + 1}枚目</span>${esc(m.say || "（指示なし）")}</li>`).join("");
  };
  const markText = () => ["次の直しをお願いします（動くスライド。座標は 1280×720 のスライドの中の px）", ...marks.map((m, j) =>
    `${j + 1}. ${m.page + 1}枚目「${titleOf(slides[m.page]).slice(0, 30)}」の x=${m.x} y=${m.y} 幅${m.w} 高さ${m.h}` +
    (m.texts.length ? `（中の文字：「${m.texts.join("」「")}」）` : "") + `：${m.say || "（ここを直して）"}`)].join("\n");
  const copyText = async t => {
    try { await navigator.clipboard.writeText(t); }
    catch (err) { const a = document.createElement("textarea"); a.value = t; body.appendChild(a); a.select(); document.execCommand("copy"); a.remove(); }
    say("コピーしました。Claude に貼ってください");
  };
  const toggleMark = on => {
    const v = on === undefined ? !body.classList.contains("marking") : on;
    body.classList.toggle("marking", v);
    if (v) { toggleOverview(false); drawMarks(); say("直したい所をドラッグで囲んでください（Esc で終わる）"); }
  };
  let drag0 = null, live = null;
  markLayer.addEventListener("pointerdown", e => {
    drag0 = slideXY(e);
    live = el("div", "box live"); markLayer.appendChild(live);
    try { markLayer.setPointerCapture(e.pointerId); } catch (err) { /* 合成した操作など */ }
  });
  markLayer.addEventListener("pointermove", e => {
    if (!drag0) return;
    const [x, y] = slideXY(e);
    Object.assign(live.style, { left: Math.min(x, drag0[0]) + "px", top: Math.min(y, drag0[1]) + "px",
      width: Math.abs(x - drag0[0]) + "px", height: Math.abs(y - drag0[1]) + "px" });
  });
  markLayer.addEventListener("pointerup", e => {
    if (!drag0) return;
    const [x, y] = slideXY(e), r = { x: Math.round(Math.min(x, drag0[0])), y: Math.round(Math.min(y, drag0[1])), w: Math.round(Math.abs(x - drag0[0])), h: Math.round(Math.abs(y - drag0[1])) };
    drag0 = null;
    if (r.w < 8 || r.h < 8) { live.remove(); return; }
    live.classList.remove("live"); live.classList.add("pending");
    pending = { page: cur, ...r, texts: textsIn(slides[cur], r) };
    askForm.hidden = false; askInput.value = ""; askInput.focus();
  });
  askForm.addEventListener("submit", e => {
    e.preventDefault();
    if (!pending) return;
    marks.push({ ...pending, say: askInput.value.trim() });
    pending = null; askForm.hidden = true; askInput.blur();
    drawMarks();
  });
  markPanel.addEventListener("click", e => {
    const m = e.target.closest("button")?.dataset.m;
    if (m === "copy") copyText(markText());
    if (m === "clear") { marks.length = 0; drawMarks(); }
    if (m === "close") toggleMark(false);
  });

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
      d: demo, e: () => toggleMark(),
      Escape: () => {
        if (body.classList.contains("help")) body.classList.remove("help");
        else if (body.classList.contains("marking")) toggleMark(false);
        else toggleOverview(false);
      },
    }[k];
    if (/^[0-9]$/.test(k)) { e.preventDefault(); typeDigit(k); return; }
    if (k === "Enter" && digits) { e.preventDefault(); clearTimeout(digitT); jump(); return; }
    if (act) { e.preventDefault(); act(); }
  }
  document.addEventListener("keydown", onKey);
  hud.addEventListener("click", e => {
    const a = e.target.closest("button")?.dataset.a;
    ({ prev, next, overview: () => toggleOverview(), notes: () => body.classList.toggle("notes"),
       presenter: openPresenter, full, help: () => body.classList.toggle("help"), demo, mark: () => toggleMark() }[a] || (() => {}))();
  });
  help.addEventListener("click", () => body.classList.remove("help"));
  let tx = 0, ty = 0, tOk = false;
  deck.addEventListener("touchstart", e => {
    tOk = !e.target.closest("input,button,summary,select,a,[data-tab],[data-orbit],[data-sheet]");
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
