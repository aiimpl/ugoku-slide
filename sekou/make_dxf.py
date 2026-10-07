"""見本の図面（DXF・A2・1:200）を書く。平面図（通り芯・柱・外形・上階の外形）と東立面図（階の高さ・外形）。

.venv/bin/python sekou/make_dxf.py [階数]   → sekou/drawing/sample.dxf（階数を渡すと sample_<n>F.dxf）

設計者から受け取る図面の代わり。スライドの建物は、この図面を read_dxf.py で読んで作る。
"""
import json
import os
import sys

import ezdxf
from ezdxf.enums import TextEntityAlignment

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = json.load(open(os.path.join(HERE, "design.json")))
A2 = (594.0, 420.0)
K = 5.0                      # 1:200 → 1m = 5mm
PLAN_O = (80.0, 200.0)       # 平面図で x=X0, y=Y0 の位置
ELEV_O = (400.0, 90.0)       # 立面図で y=Y0, z=0 の位置


def build(floors):
    gx, gy = DESIGN["grid_x"], DESIGN["grid_y"]
    h1, ht, sb = DESIGN["h1"], DESIGN["htyp"], DESIGN["setback"]
    lev = [0.0] + [h1 + ht * i for i in range(floors)]
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4
    for name, color in (("枠", 7), ("表題", 7), ("通り芯", 1), ("柱", 7), ("外形", 7), ("上階外形", 3),
                        ("レベル", 2), ("立面外形", 7), ("文字", 7), ("寸法", 2)):
        doc.layers.add(name, color=color)
    msp = doc.modelspace()

    def txt(s, x, y, h=3.0, layer="文字", align=TextEntityAlignment.LEFT):
        msp.add_text(s, height=h, dxfattribs={"layer": layer}).set_placement((x, y), align=align)

    W, H = A2
    msp.add_lwpolyline([(10, 10), (W - 10, 10), (W - 10, H - 10), (10, H - 10)], close=True, dxfattribs={"layer": "枠"})
    # 表題欄
    tb = [(W - 190, 10), (W - 10, 10), (W - 10, 40), (W - 190, 40)]
    msp.add_lwpolyline(tb, close=True, dxfattribs={"layer": "表題"})
    txt("（仮称）サンプル町オフィス新築工事", W - 185, 28, 4.5, "表題")
    txt(f"平面図・東立面図　S=1:200　{floors}F", W - 185, 16, 3.5, "表題")

    # 平面図
    px, py = PLAN_O
    P = lambda x, y: (px + (x - gx[0]) * K, py + (y - gy[0]) * K)
    for i, x in enumerate(gx):
        a, b = P(x, gy[0] - 4), P(x, gy[-1] + 4)
        msp.add_line(a, b, dxfattribs={"layer": "通り芯"})
        txt(f"X{i + 1}", a[0], a[1] - 6, 3.0, "通り芯", TextEntityAlignment.CENTER)
    for j, y in enumerate(gy):
        a, b = P(gx[0] - 4, y), P(gx[-1] + 4, y)
        msp.add_line(a, b, dxfattribs={"layer": "通り芯"})
        txt(f"Y{j + 1}", a[0] - 6, a[1] - 1, 3.0, "通り芯", TextEntityAlignment.CENTER)
    for x in gx:
        for y in gy:
            c = P(x, y)
            s = 0.25 * K
            msp.add_lwpolyline([(c[0] - s, c[1] - s), (c[0] + s, c[1] - s), (c[0] + s, c[1] + s), (c[0] - s, c[1] + s)],
                               close=True, dxfattribs={"layer": "柱"})
    o = 0.6
    msp.add_lwpolyline([P(gx[0] - o, gy[0] - o), P(gx[-1] + o, gy[0] - o), P(gx[-1] + o, gy[-1] + o), P(gx[0] - o, gy[-1] + o)],
                       close=True, dxfattribs={"layer": "外形"})
    if floors >= sb["from"]:
        yn = gy[-1] - sb["depth"]
        msp.add_lwpolyline([P(gx[0] - o, yn + o), P(gx[-1] + o, yn + o)], dxfattribs={"layer": "上階外形"})
        txt(f"{sb['from']}F〜 外形", P(gx[-1] + 2, yn)[0], P(gx[-1] + 2, yn)[1], 2.5, "上階外形")
    txt("平面図", px, py - 44, 5.0)
    # 寸法（全長）
    a, b = P(gx[0], gy[0] - 8), P(gx[-1], gy[0] - 8)
    msp.add_line(a, b, dxfattribs={"layer": "寸法"})
    txt(f"{int((gx[-1] - gx[0]) * 1000):,}", (a[0] + b[0]) / 2, a[1] + 1.5, 2.5, "寸法", TextEntityAlignment.CENTER)

    # 東立面図（横が南→北、縦が高さ）
    ex, ey = ELEV_O
    E = lambda y, z: (ex + (y - gy[0]) * K, ey + z * K)
    for f, z in enumerate(lev):
        a, b = E(gy[0] - 3, z), E(gy[-1] + 3, z)
        msp.add_line(a, b, dxfattribs={"layer": "レベル"})
        name = "1FL" if f == 0 else ("RFL" if f == floors else f"{f + 1}FL")
        txt(f"{name} +{z:.1f}", b[0] + 2, b[1] - 1, 2.5, "レベル")
    top = lev[floors]
    yn_top = gy[-1] - (sb["depth"] if floors >= sb["from"] else 0)
    zs = lev[sb["from"] - 1] if floors >= sb["from"] else top
    pts = [E(gy[0], 0), E(gy[0], top), E(yn_top, top), E(yn_top, zs), E(gy[-1], zs), E(gy[-1], 0)]
    msp.add_lwpolyline(pts, dxfattribs={"layer": "立面外形"})
    txt("東立面図", ex, ey - 20, 5.0)
    return doc


def main():
    floors = int(sys.argv[1]) if len(sys.argv) > 1 else DESIGN["floors"]
    os.makedirs(os.path.join(HERE, "drawing"), exist_ok=True)
    name = "sample.dxf" if floors == DESIGN["floors"] else f"sample_{floors}F.dxf"
    path = os.path.join(HERE, "drawing", name)
    build(floors).saveas(path)
    print(path)


if __name__ == "__main__":
    main()
