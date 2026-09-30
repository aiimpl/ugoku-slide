"""書き出した雛形を全部、ブラウザで開いて確かめる（要 playwright）。

  python3 tools/qa.py              全部
  python3 tools/qa.py 05 51        名前の先頭が一致するものだけ
  python3 tools/qa.py --warn 51    「要確認」も表示する

中身は skill/scripts/check.py と同じ点検（スキルで配っているもの）。
画像は build/qa/<名前>/、全ページを並べた一覧は sheet.png。
問題が1本でもあれば終了コード 1。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skill" / "scripts"))
from check import run  # noqa: E402

DOCS = ROOT / "docs" / "slides"
OUT = ROOT / "build" / "qa"


def sheet(out):
    """全ページを1枚に並べた sheet.png（Pillow があれば）"""
    try:
        from PIL import Image
    except ImportError:
        return
    shots = sorted(out.glob("[0-9][0-9].png"))
    ims = [Image.open(p).resize((640, 360)) for p in shots]
    board = Image.new("RGB", (1280, 360 * ((len(ims) + 1) // 2)), "white")
    for i, im in enumerate(ims):
        board.paste(im, ((i % 2) * 640, (i // 2) * 360))
    board.save(out / "sheet.png")


def main():
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print(__doc__)
        return
    show_warn = "--warn" in sys.argv
    pats = [a for a in sys.argv[1:] if not a.startswith("--")]
    files = [p for p in sorted(DOCS.glob("*.html")) if not pats or any(p.stem.startswith(x) for x in pats)]
    bad = warned = 0
    for f in files:
        r = run(f, out=OUT / f.stem)
        sheet(r["out"])
        tag = "NG" if r["problems"] else "OK"
        print(f"{tag} {f.stem}（{r['n']}枚）" + (f" 要確認 {len(r['warns'])}" if r["warns"] else "") +
              ("　" + "・".join(r["infos"]) if r["infos"] else ""))
        for x in r["problems"]:
            print("   問題　" + x)
        if show_warn:
            for x in r["warns"]:
                print("   要確認 " + x)
        bad += bool(r["problems"])
        warned += bool(r["warns"])
    print(f"\n{len(files)} 本中 問題 {bad} 本・要確認 {warned} 本。画像は {OUT.relative_to(ROOT)}/")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
