// ブラウザの中で測る点検。check.py が読み込んで window.UGK_CHECK から呼ぶ。
// どれも「i 枚目（0 から）」の今の見た目を測る。座標は 1280×720 のスライド座標。
(() => {
  const W = 1280, H = 720;
  const slides = () => [...document.querySelectorAll(".deck > .slide")];
  const scaleOf = s => s.getBoundingClientRect().width / W || 1;
  const skipped = el => el.closest(".bg,.notes,details:not([open]) > .body,[hidden],[aria-hidden=true],.ugk-ghost,svg");

  // 親までたどった不透明度
  const alpha = (el, s) => { let a = 1; for (let e = el; e && e !== s.parentElement; e = e.parentElement) a *= parseFloat(getComputedStyle(e).opacity); return a; };
  const shown = (el, s) => (!el.checkVisibility || el.checkVisibility({ opacityProperty: true, visibilityProperty: true })) && alpha(el, s) >= 0.5;

  // 文字を直接持つ要素
  const textLeaves = s => [...s.querySelectorAll("*")].filter(el =>
    !skipped(el) && [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && shown(el, s));

  const box = (el, s) => {
    const r = el.getBoundingClientRect(), b = s.getBoundingClientRect(), k = scaleOf(s);
    return { l: (r.left - b.left) / k, t: (r.top - b.top) / k, r: (r.right - b.left) / k, b: (r.bottom - b.top) / k, w: r.width / k, h: r.height / k };
  };
  const snip = el => el.textContent.trim().replace(/\s+/g, " ").slice(0, 16);

  // 枠からはみ出した文字（px 付き）
  const overflow = i => {
    const s = slides()[i], out = [];
    textLeaves(s).forEach(el => {
      const r = box(el, s);
      if (!r.w || !r.h || getComputedStyle(el).position === "fixed") return;
      const px = Math.max(r.r - W, r.b - H, -r.l, -r.t);
      if (px > 4) out.push({ text: snip(el), px: Math.round(px) });
    });
    return out.slice(0, 5);
  };

  // 文字どうしの重なり（行ごとの箱を、文字の大きさの範囲に縮めて比べる）
  const overlap = i => {
    const s = slides()[i], k = scaleOf(s), boxes = [];
    textLeaves(s).forEach(el => {
      const fs = parseFloat(getComputedStyle(el).fontSize);
      const rg = document.createRange(); rg.selectNodeContents(el);
      [...rg.getClientRects()].forEach(b => {
        if (b.width < 2 || b.height < 2) return;
        const pad = Math.max(0, (b.height - fs * 0.78) / 2);
        boxes.push([el, { l: b.left, r: b.right, t: b.top + pad, b: b.bottom - pad, w: b.width, h: b.height - 2 * pad }]);
      });
    });
    const out = [];
    for (let a = 0; a < boxes.length; a++) for (let c = a + 1; c < boxes.length; c++) {
      const [e1, r1] = boxes[a], [e2, r2] = boxes[c];
      if (e1 === e2 || e1.contains(e2) || e2.contains(e1)) continue;
      const w = Math.min(r1.r, r2.r) - Math.max(r1.l, r2.l), h = Math.min(r1.b, r2.b) - Math.max(r1.t, r2.t);
      if (w / k > 6 && h / k > 4 && h > Math.min(r1.h, r2.h) * 0.35 && w > Math.min(r1.w, r2.w) * 0.2)
        out.push(`「${snip(e1)}」と「${snip(e2)}」`);
    }
    return [...new Set(out)].slice(0, 5);
  };

  // 中身が占める範囲と、下の空き（注記 .foot と背景は数えない）
  const layout = i => {
    const s = slides()[i], leaves = new Set(textLeaves(s));
    const els = [...s.querySelectorAll("*")].filter(el => {
      if (skipped(el) || el.closest(".foot") || !shown(el, s)) return false;
      if (leaves.has(el)) return true;
      if (/^(IMG|CANVAS|INPUT|SELECT|BUTTON|VIDEO)$/.test(el.tagName)) return true;
      const cs = getComputedStyle(el), r = box(el, s);
      const painted = cs.backgroundColor !== "rgba(0, 0, 0, 0)" || cs.backgroundImage !== "none" || parseFloat(cs.borderTopWidth) > 0;
      return painted && r.w * r.h < W * H * 0.8; // 全面の板は数えない
    });
    let top = H, bottom = 0;
    els.forEach(el => { const r = box(el, s); if (r.w && r.h) { top = Math.min(top, r.t); bottom = Math.max(bottom, r.b); } });
    if (bottom <= top) return { fill: 0, gap: H };
    return { fill: (Math.min(bottom, H) - Math.max(top, 0)) / H, gap: Math.round(H - Math.min(bottom, H)) };
  };

  // 見出しと本文の文字、数え上げの手がかり（同じ class の兄弟が並ぶ数）
  const text = i => {
    const s = slides()[i];
    const heads = [...s.querySelectorAll("h1,h2")].filter(h => !skipped(h) && shown(h, s)).map(h => h.textContent.replace(/\s+/g, "").trim());
    const body = textLeaves(s).map(el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join("")).join("\n");
    const counts = new Set();
    s.querySelectorAll("*").forEach(p => {
      if (skipped(p)) return;
      const kids = [...p.children].filter(c => !skipped(c) && c.tagName !== "ASIDE" && shown(c, s));
      const by = {};
      kids.forEach(c => { const key = c.tagName + "." + c.classList[0]; by[key] = (by[key] || 0) + 1; });
      Object.values(by).forEach(n => { if (n >= 2) counts.add(n); });
    });
    return { heads, body, counts: [...counts] };
  };

  // 文字の色と場所。背景の色は check.py が画像から拾って、コントラスト比を出す
  const rgba = c => { const m = c.match(/[\d.]+/g) || [0, 0, 0, 0]; return m.map(Number).concat(m.length < 4 ? [1] : []).slice(0, 4); };
  const inks = i => {
    const s = slides()[i], out = [];
    textLeaves(s).forEach(el => {
      const cs = getComputedStyle(el);
      if (cs.webkitBackgroundClip === "text" || cs.backgroundClip === "text") return; // 文字をグラデーションで塗る表現は測らない
      const fg = rgba(cs.webkitTextFillColor || cs.color);
      fg[3] *= alpha(el, s);
      if (fg[3] < 0.3) return;
      const r = box(el, s);
      if (r.w < 4 || r.h < 4 || r.r < 0 || r.l > W || r.b < 0 || r.t > H) return;
      const px = parseFloat(cs.fontSize);
      out.push({ text: snip(el), fg, box: [r.l, r.t, r.w, r.h], large: px >= 24 || (px >= 18.66 && Number(cs.fontWeight) >= 700) });
    });
    return out;
  };

  // 使っている文字の大きさ（px）
  const fonts = i => {
    const s = slides()[i];
    return [...new Set(textLeaves(s).map(el => Math.round(parseFloat(getComputedStyle(el).fontSize))))].sort((a, b) => a - b);
  };

  // そのページで見る人が触る操作の種類と、動きの有無
  const ops = i => {
    const s = slides()[i], has = q => !!s.querySelector(q) || s.matches(q);
    const kinds = [];
    if (has("[data-calc] input,[data-calc] select") || (s.matches("[data-calc]") && s.querySelector("input,select"))) kinds.push("スライダー");
    if (has("[data-tabs]")) kinds.push("タブ");
    if (has("[data-rank]")) kinds.push("重みで順位");
    if (has(".quiz")) kinds.push("クイズ");
    if (has("[data-sheet]")) kinds.push("表");
    if (has("[data-orbit]")) kinds.push("立体");
    const moves = kinds.length || has(".step,details.why,[data-count],[data-morph],.draw,.chart,pre.code[data-highlight]");
    return { kinds, moves: !!moves };
  };

  // ページの境目ごとに、同じ data-morph の名前でつながる要素があるか
  const carry = () => {
    const ss = slides(), names = s => new Set([...s.querySelectorAll("[data-morph]")].map(e => e.dataset.morph));
    const out = [];
    for (let j = 0; j + 1 < ss.length; j++) {
      const a = names(ss[j]), b = names(ss[j + 1]);
      out.push([...a].some(n => b.has(n)));
    }
    return { morph: document.querySelector(".deck").dataset.transition === "morph", joins: out };
  };

  // 変形の途中で、動いている要素が画面の外へ出ていないか
  const offscreen = () => {
    const s = document.querySelector(".slide.active");
    return [...s.querySelectorAll("[data-morph]")].filter(el => {
      const r = box(el, s);
      return r.w && (r.r < 0 || r.l > W || r.b < 0 || r.t > H);
    }).map(el => el.dataset.morph);
  };

  // → を押し切る回数（.step の数と、コードの強調の段数）
  const steps = i => {
    const s = slides()[i];
    return s.querySelectorAll(".step").length +
      [...s.querySelectorAll("pre.code[data-highlight]")].reduce((a, p) => a + p.dataset.highlight.split("|").length, 0);
  };

  // スライダーを両端まで動かして、数字が変わるか・計算できるか
  const calc = () => {
    const res = [];
    document.querySelectorAll("[data-calc]").forEach((b, bi) => {
      const outs = [...b.querySelectorAll("[data-out]")];
      b.querySelectorAll("input[type=range],input[type=checkbox]").forEach(inp => {
        const snap = () => outs.map(o => o.textContent);
        const set = v => {
          if (inp.type === "checkbox") inp.checked = v; else inp.value = v;
          outs.forEach(o => { o._v = NaN; });
          inp.dispatchEvent(new Event("input", { bubbles: true }));
          return snap();
        };
        const old = inp.type === "checkbox" ? inp.checked : inp.value, before = snap();
        const tries = inp.type === "checkbox" ? [set(!old)] : [set(inp.max), set(inp.min)];
        if (outs.length && tries.every(a => before.every((t, j) => t === a[j]))) res.push(`計算${bi + 1} ${inp.name} を動かしても数字が変わらない`);
        if (tries.some(a => a.some(t => /NaN|—/.test(t)))) res.push(`計算${bi + 1} ${inp.name} の端の値で計算できない式がある`);
        set(old);
      });
    });
    return res;
  };

  // 根拠を全部開く
  const openWhy = i => { const d = [...slides()[i].querySelectorAll("details.why")]; d.forEach(x => { x.open = true; x.dispatchEvent(new Event("toggle")); }); return d.length; };

  // 表（data-sheet）に 1.4 倍の数字で 3 行多い表を貼る。集計が「—」になる所を返す
  const sheet = i => {
    const bad = [];
    slides()[i].querySelectorAll("[data-sheet]").forEach((fig, k) => {
      const t = fig.querySelector("table");
      const head = [...t.querySelectorAll("thead th")].map(x => x.textContent.trim());
      const rows = [...t.querySelectorAll("tbody tr")].map(tr => [...tr.children].map(x => x.textContent.trim()));
      const num = v => parseFloat(String(v).replace(/[,，]/g, ""));
      const more = rows.concat(rows.slice(0, 3).map((r, j) => [r[0] + "（追加" + (j + 1) + "）", ...r.slice(1)]));
      const tsv = [head, ...more.map(r => [r[0], ...r.slice(1).map(v => isFinite(num(v)) ? String(Math.round(num(v) * 14) / 10) : v)])]
        .map(r => r.join("\t")).join("\n");
      const dt = new DataTransfer(); dt.setData("text/plain", tsv);
      fig.dispatchEvent(new ClipboardEvent("paste", { clipboardData: dt, bubbles: true, cancelable: true }));
      fig.querySelectorAll("[data-sheet-out]").forEach(o => { if (/NaN|—|undefined/.test(o.textContent)) bad.push(`表${k + 1} の集計「${o.dataset.sheetOut}」が計算できない`); });
    });
    return bad;
  };

  const count = () => slides().length;
  const hasSheet = i => !!slides()[i].querySelector("[data-sheet]");
  window.UGK_CHECK = { count, overflow, overlap, layout, text, inks, fonts, ops, carry, offscreen, steps, calc, openWhy, sheet, hasSheet };
})();
