"""DXF の線と文字を、スライドに載せる SVG にする（読むのは DXF だけ）。

.venv/bin/python sekou/dxf_svg.py drawing/sample.dxf ../src/assets/sekou/drawing.svg
"""
import os
import sys
from xml.sax.saxutils import escape

import ezdxf

HERE = os.path.dirname(os.path.abspath(__file__))
STYLE = {  # レイヤー → 線の色・太さ・線種
    "枠": ("#232427", 0.6, None), "表題": ("#232427", 0.5, None), "通り芯": ("#b9502b", 0.35, "6 2 1 2"),
    "柱": ("#232427", 0.5, None), "外形": ("#232427", 0.9, None), "上階外形": ("#b9502b", 0.6, "3 2"),
    "レベル": ("#7d7f84", 0.35, "4 2"), "立面外形": ("#232427", 0.9, None), "寸法": ("#7d7f84", 0.35, None),
}


def main():
    src, dst = sys.argv[1], sys.argv[2]
    doc = ezdxf.readfile(os.path.join(HERE, src))
    msp = doc.modelspace()
    W, H = 594, 420
    Y = lambda y: H - y
    out = []
    for e in msp:
        col, lw, dash = STYLE.get(e.dxf.layer, ("#232427", 0.4, None))
        da = f' stroke-dasharray="{dash}"' if dash else ""
        cls = f' class="l-{e.dxf.layer}"'
        if e.dxftype() == "LINE":
            a, b = e.dxf.start, e.dxf.end
            out.append(f'<line{cls} x1="{a.x:.2f}" y1="{Y(a.y):.2f}" x2="{b.x:.2f}" y2="{Y(b.y):.2f}" stroke="{col}" stroke-width="{lw}"{da}/>')
        elif e.dxftype() == "LWPOLYLINE":
            pts = " ".join(f"{p[0]:.2f},{Y(p[1]):.2f}" for p in e.get_points())
            tag = "polygon" if e.closed else "polyline"
            out.append(f'<{tag}{cls} points="{pts}" fill="none" stroke="{col}" stroke-width="{lw}"{da}/>')
        elif e.dxftype() == "TEXT":
            p = e.dxf.align_point if e.dxf.halign else e.dxf.insert
            anchor = "middle" if e.dxf.halign == 1 else "start"
            out.append(f'<text{cls} x="{p.x:.2f}" y="{Y(p.y):.2f}" font-size="{e.dxf.height * 1.25:.2f}" text-anchor="{anchor}" fill="{col}">{escape(e.dxf.text)}</text>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Jost, Noto Sans JP, sans-serif">'
           + "".join(out) + "</svg>")
    open(os.path.join(HERE, dst), "w").write(svg)
    print(dst, len(svg))


if __name__ == "__main__":
    main()
