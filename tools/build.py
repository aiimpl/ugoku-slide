"""src/decks/*.html を、1ファイルで完結したスライドにして docs/ に書き出す。

  python3 tools/build.py          書き出す
  python3 tools/build.py --check  書き出し済みの docs/ が src と一致しているかだけ確かめる
  python3 tools/build.py --only 05 12  名前の先頭が一致するスライドだけ書き出す（一覧と zip は作らない）
"""
import html
import io
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "decks"
OUT = ROOT / "docs"
SITE = "https://aiimpl.github.io/ugoku-slide/"

META_RE = re.compile(r"<!--meta\s*(\{.*?\})\s*-->", re.S)
STYLE_RE = re.compile(r"<style>.*?</style>", re.S)
MAIN_RE = re.compile(r"<main class=\"deck\".*?</main>", re.S)
SCRIPT_RE = re.compile(r"<script>.*?</script>", re.S)
FEATURES = {
    "calc": r"\bdata-calc\b", "why": r'class="[^"]*\bwhy\b', "tabs": r"\bdata-tabs\b", "rank": r"\bdata-rank\b",
    "quiz": r'class="[^"]*\bquiz\b', "code": r'class="[^"]*\bcode\b', "count": r"\bdata-count=", "chart": r'class="[^"]*\bchart\b',
}
LABELS = {
    "calc": "数字で再計算", "why": "クリックで根拠", "tabs": "切り替え", "rank": "重みで順位",
    "quiz": "クイズ", "code": "コード強調", "count": "カウントアップ", "chart": "グラフ",
}


def read_engine():
    e = ROOT / "engine"
    return (e / "engine.css").read_text(), (e / "engine.js").read_text(), (e / "guide.txt").read_text()


def parse(path):
    text = path.read_text()
    m = META_RE.search(text)
    if not m:
        raise SystemExit(f"{path.name}: 先頭に <!--meta {{...}} --> がありません")
    meta = json.loads(m.group(1))
    for k in ("title", "style", "use", "aim", "desc"):
        if not meta.get(k):
            raise SystemExit(f"{path.name}: meta に {k} がありません")
    main = MAIN_RE.search(text)
    if not main:
        raise SystemExit(f'{path.name}: <main class="deck"> がありません')
    body = main.group(0)
    meta["id"] = path.stem
    meta["file"] = f"slides/{path.stem}.html"
    meta["slides"] = len(re.findall(r'<section class="slide', body))
    meta["features"] = [k for k, pat in FEATURES.items() if re.search(pat, body)]
    return meta, STYLE_RE.findall(text), body, SCRIPT_RE.findall(text[main.end():])


def assemble(meta, styles, body, scripts, engine):
    css, js, guide = engine
    fonts = meta.get("fonts")
    font_tags = ""
    if fonts:
        font_tags = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
                     '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
                     f'<link rel="stylesheet" href="{html.escape(fonts)}">\n')
    return (
        "<!doctype html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        f"<title>{html.escape(meta['title'])}</title>\n"
        f"<meta name=\"description\" content=\"{html.escape(meta['desc'])}\">\n"
        f"{font_tags}"
        f"<!--\n{guide}\n  このスライド：{meta['style']} / {meta['use']}\n-->\n"
        "<style>\n/* ==== ugoku-slide engine:css BEGIN ==== */\n" + css +
        "/* ==== ugoku-slide engine:css END ==== */\n</style>\n"
        "<!-- ==== ここから下の <style> が、このスライドの見た目（色・文字・飾り） ==== -->\n"
        + "\n".join(styles) + "\n</head>\n<body>\n" + body + "\n"
        "<script>\n/* ==== ugoku-slide engine:js BEGIN ==== */\n" + js +
        "/* ==== ugoku-slide engine:js END ==== */\n</script>\n" + "\n".join(scripts) +
        "\n</body>\n</html>\n"
    )


def card(meta):
    chips = "".join(f"<span>{LABELS[f]}</span>" for f in meta["features"] if f in LABELS)
    e = html.escape
    return (
        f'<article class="tpl" data-id="{e(meta["id"])}" data-group="{e(meta.get("group", ""))}">'
        f'<a class="thumb" href="{e(meta["file"])}" target="_blank" rel="noopener" aria-label="{e(meta["title"])}を開く">'
        f'<iframe data-src="{e(meta["file"])}?embed" title="{e(meta["title"])}" tabindex="-1" loading="lazy"></iframe></a>'
        f'<div class="meta"><div class="no">{e(meta["id"][:2])}</div><div>'
        f'<h3>{e(meta["style"])}</h3><p class="use">{e(meta["use"])}｜{meta["slides"]}枚</p>'
        f'<p class="aim">{e(meta.get("aim", ""))}</p>'
        f'<p class="desc">{e(meta["desc"])}</p><div class="chips">{chips}</div></div></div>'
        f'<div class="acts"><a class="btn" href="{e(meta["file"])}" target="_blank" rel="noopener">開く</a>'
        f'<a class="btn primary" href="{e(meta["file"])}" download="{e(meta["id"])}.html">ダウンロード</a>'
        f'<button class="btn" data-copy="{e(meta["id"])}" type="button">Claude用の指示をコピー</button></div></article>'
    )


def build():
    engine = read_engine()
    decks = sorted(SRC.glob("*.html"))
    files, metas = {}, []
    for p in decks:
        meta, styles, body, scripts = parse(p)
        files[f"slides/{p.stem}.html"] = assemble(meta, styles, body, scripts, engine)
        metas.append(meta)
    tpl = (ROOT / "src" / "index.html").read_text()
    groups = {}
    for m in metas:
        groups.setdefault(m.get("group", "その他"), []).append(m)
    index = (tpl.replace("<!--CARDS-->", "\n".join(card(m) for m in metas))
                .replace("{{COUNT}}", str(len(metas)))
                .replace("{{SLIDES}}", str(sum(m["slides"] for m in metas)))
                .replace("{{GROUPS}}", "".join(
                    f'<button type="button" data-filter="{html.escape(g)}">{html.escape(g)}<small>{len(v)}</small></button>'
                    for g, v in groups.items()))
                .replace("{{MANIFEST}}", json.dumps(
                    [{k: m[k] for k in ("id", "title", "style", "use", "aim", "desc", "file")} for m in metas],
                    ensure_ascii=False)))
    files["index.html"] = index
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(k for k in files if k.startswith("slides/")):
            info = zipfile.ZipInfo("ugoku-slide/" + name.split("/", 1)[1], date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, files[name])
        info = zipfile.ZipInfo("ugoku-slide/LICENSE.txt", date_time=(2026, 1, 1, 0, 0, 0))
        info.external_attr = 0o644 << 16
        z.writestr(info, (ROOT / "LICENSE").read_text())
    return files, buf.getvalue(), metas


def main():
    if "--only" in sys.argv:
        pats = sys.argv[sys.argv.index("--only") + 1:]
        engine = read_engine()
        n = 0
        for p in sorted(SRC.glob("*.html")):
            if any(p.stem.startswith(x) for x in pats):
                out = OUT / "slides" / f"{p.stem}.html"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(assemble(*parse(p), engine))
                n += 1
        print(f"{n} 本を書き出しました")
        return
    files, zipped, metas = build()
    check = "--check" in sys.argv
    stale = []
    for name, text in files.items():
        path = OUT / name
        if check:
            if not path.exists() or path.read_text() != text:
                stale.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    zpath = OUT / "ugoku-slide-all.zip"
    if check:
        if not zpath.exists() or zpath.read_bytes() != zipped:
            stale.append(zpath.name)
        known = set(files) | {zpath.name, ".nojekyll", "og.png"}
        extra = [str(p.relative_to(OUT)) for p in OUT.rglob("*") if p.is_file() and str(p.relative_to(OUT)) not in known]
        if stale or extra:
            raise SystemExit("docs/ が古いです。make build してください：" + ", ".join(stale + extra))
        print(f"docs/ は最新です（{len(metas)} 本）")
    else:
        zpath.write_bytes(zipped)
        (OUT / ".nojekyll").write_text("")
        print(f"{len(metas)} 本・{sum(m['slides'] for m in metas)} 枚を docs/ に書き出しました")


if __name__ == "__main__":
    main()
