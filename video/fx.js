// 撮影用の演出（テロップ・カーソル・クリック）。ページに差し込んで使う。
// 時間は performance.now（撮影中はゆっくり進む）で測るので、コマ撮りでもなめらかに動く。
(() => {
  const V = (window.V = {});
  const ease = k => 1 - Math.pow(1 - k, 3);
  const tween = (dur, fn) => new Promise(done => {
    const t0 = performance.now();
    const tick = () => {
      const k = Math.min(1, (performance.now() - t0) / (dur * 1000));
      fn(ease(k), k);
      if (k < 1) requestAnimationFrame(tick); else done();
    };
    requestAnimationFrame(tick);
  });
  const root = () => {
    let r = document.getElementById("vfx");
    if (!r) {
      r = document.createElement("div");
      r.id = "vfx";
      r.innerHTML = '<div id="vcur"><svg viewBox="0 0 24 24" width="44" height="44"><path d="M4 2 L4 19 L8.6 14.8 L11.6 21.4 L14.6 20 L11.7 13.6 L18 13.6 Z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg></div>';
      document.body.appendChild(r);
    }
    return r;
  };
  let cx = 2000, cy = 1200;
  const cur = () => root().querySelector("#vcur");
  const place = () => { cur().style.transform = `translate(${cx}px,${cy}px)`; };
  const center = sel => {
    const el = typeof sel === "string" ? document.querySelector(sel) : sel;
    const r = el.getBoundingClientRect();
    return [r.left + r.width / 2, r.top + r.height / 2, el];
  };

  V.cap = (html, cls = "") => {
    root().querySelectorAll(".cap").forEach(c => c.classList.add("out"));
    const c = document.createElement("div");
    c.className = "cap " + cls;
    c.innerHTML = html;
    root().appendChild(c);
  };
  V.chip = html => {
    const c = document.createElement("div");
    c.className = "chip";
    c.innerHTML = html;
    root().appendChild(c);
  };
  V.show = on => { cur().style.opacity = on ? 1 : 0; };
  V.from = (x, y) => { cx = x; cy = y; place(); V.show(true); };
  V.move = async (sel, dur = 0.4) => {
    const [x, y] = Array.isArray(sel) ? sel : center(sel);
    const x0 = cx, y0 = cy;
    V.show(true);
    await tween(dur, e => { cx = x0 + (x - x0) * e; cy = y0 + (y - y0) * e; place(); });
  };
  V.click = async sel => {
    const [x, y, el] = center(sel);
    cx = x; cy = y; place();
    const r = document.createElement("i");
    r.className = "ring";
    r.style.left = x + "px"; r.style.top = y + "px";
    root().appendChild(r);
    cur().classList.add("down");
    setTimeout(() => cur().classList.remove("down"), 0);
    el.click();
  };
  // スライダーのつまみをつかんで value まで動かす
  V.drag = async (sel, to, dur = 1) => {
    const el = document.querySelector(sel);
    const r = el.getBoundingClientRect(), min = +el.min, max = +el.max, step = +el.step || 1;
    const xAt = v => r.left + 10 + (v - min) / (max - min) * (r.width - 20);
    const from = +el.value;
    await V.move([xAt(from), r.top + r.height / 2], 0.25);
    await tween(dur, e => {
      const v = Math.round((from + (to - from) * e) / step) * step;
      if (+el.value !== v) { el.value = v; el.dispatchEvent(new Event("input", { bubbles: true })); }
      cx = xAt(from + (to - from) * e); place();
    });
  };
  V.key = k => document.dispatchEvent(new KeyboardEvent("keydown", { key: k, bubbles: true }));
  V.type = async (sel, text, dur) => {
    const el = document.querySelector(sel);
    await tween(dur, (e, k) => { el.textContent = text.slice(0, Math.round(text.length * k)); });
  };
  root();
})();
