"""図面（DXF）を読んで、建物の寸法を spec.json に書く。読むのは線だけ（文字の寸法値は使わない）。

.venv/bin/python sekou/read_dxf.py drawing/sample.dxf [出力 spec.json]

  通り芯（通り芯レイヤーの線）     → 柱の位置 grid_x / grid_y（建物の中心を原点に）
  階の線（レベルレイヤーの線）     → 階数・1階の階高・基準階の階高
  東立面の外形（立面外形レイヤー） → 北側のセットバックの深さと、始まる階
  縮尺は表題欄の「S=1:200」から。工程（sched）と敷地（site）は今の spec.json のまま残す
"""
import json
import os
import re
import sys

import ezdxf

HERE = os.path.dirname(os.path.abspath(__file__))


def read(path):
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    scale = None
    for t in msp.query("TEXT"):
        m = re.search(r"S=1:(\d+)", t.dxf.text)
        if m:
            scale = int(m.group(1))
    k = 1000.0 / scale                      # 図面 mm / 実物 m
    xs, ys, zs = set(), set(), set()
    for ln in msp.query('LINE[layer=="通り芯"]'):
        a, b = ln.dxf.start, ln.dxf.end
        if abs(a.x - b.x) < 1e-6:
            xs.add(round(a.x, 3))
        elif abs(a.y - b.y) < 1e-6:
            ys.add(round(a.y, 3))
    for ln in msp.query('LINE[layer=="レベル"]'):
        zs.add(round(ln.dxf.start.y, 3))
    xs, ys, zs = sorted(xs), sorted(ys), sorted(zs)
    cx, cy = (xs[0] + xs[-1]) / 2, (ys[0] + ys[-1]) / 2
    grid_x = [round((x - cx) / k, 3) for x in xs]
    grid_y = [round((y - cy) / k, 3) for y in ys]
    lev = [round((z - zs[0]) / k, 3) for z in zs]
    floors = len(lev) - 1
    # 立面の外形：南の端 y0、上で一番北の点、段の高さ
    poly = list(msp.query('LWPOLYLINE[layer=="立面外形"]'))[0]
    pts = [(p[0], p[1]) for p in poly.get_points()]
    y_south = min(p[0] for p in pts)
    y_north = max(p[0] for p in pts)
    top = max(p[1] for p in pts)
    y_north_top = max(p[0] for p in pts if abs(p[1] - top) < 1e-6)
    depth = round((y_north - y_north_top) / k, 3)
    setback = {"from": floors + 1, "depth": 0.0}
    if depth > 0:
        z_step = max(p[1] for p in pts if abs(p[0] - y_north) < 1e-6)
        i = min(range(len(zs)), key=lambda n: abs(zs[n] - z_step))
        setback = {"from": i + 1, "depth": depth}
    assert abs((y_north - y_south) / k - (grid_y[-1] - grid_y[0])) < 1e-3, "立面と平面の奥行きが合わない"
    return {"grid_x": grid_x, "grid_y": grid_y, "floors": floors, "h1": lev[1], "htyp": round(lev[2] - lev[1], 3),
            "setback": setback}


def main():
    src = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else "drawing/sample.dxf")
    out = os.path.join(HERE, sys.argv[2] if len(sys.argv) > 2 else "spec.json")
    got = read(src)
    spec = json.load(open(os.path.join(HERE, "spec.json")))
    spec.update(got)
    json.dump(spec, open(out, "w"), ensure_ascii=False, indent=2)
    print(json.dumps(got, ensure_ascii=False))


if __name__ == "__main__":
    main()
