"""施工計画スライド用：8階建て鉄骨オフィスを Python で組み、工程・断面・日影・夕景のコマを書き出す。

blender -b --factory-startup -P scene.py -- progress|section|shade|dusk|test [first last]

寸法はすべて SPEC（1か所）から。工程（週）は SCHED で、スライドのガントチャートと同じ値を使う。
"""
import bpy
import math
import os
import sys
import json
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = json.load(open(os.path.join(HERE, "spec.json")))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["test"]
MODE = argv[0]

GX = SPEC["grid_x"]            # 柱の通り（東西）
GY = SPEC["grid_y"]            # 柱の通り（南北）
NF = SPEC["floors"]
H1, HT = SPEC["h1"], SPEC["htyp"]
LEV = [0.0] + [H1 + HT * i for i in range(NF)]  # 各階の床の高さ（LEV[NF] が屋上）
TOP = LEV[NF]
X0, X1, Y0, Y1 = GX[0], GX[-1], GY[0], GY[-1]
SITE = SPEC["site"]            # [xmin, ymin, xmax, ymax]
SCHED = SPEC["sched"]          # 名前 → [開始週, 終了週]
SB = SPEC["setback"]           # 北側セットバック（上層）

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
col_main = scn.collection


def clamp01(v):
    return max(0.0, min(1.0, v))


def prog(name, w):
    a, b = SCHED[name]
    return clamp01((w - a) / (b - a))


# ---------------------------------------------------------------- 材質
CUT = {"x": 1e9}  # 断面：x がこれより大きい所を消す


def mat(name, color, rough=0.6, metal=0.0, alpha=1.0, emit=None, transmission=0.0, cut=True):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Metallic"].default_value = metal
    if transmission:
        bs.inputs["Transmission Weight"].default_value = transmission
    if emit:
        bs.inputs["Emission Color"].default_value = (*emit[0], 1)
        bs.inputs["Emission Strength"].default_value = emit[1]
    shader = bs.outputs[0]
    if alpha < 1.0:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mx = nt.nodes.new("ShaderNodeMixShader")
        mx.inputs[0].default_value = alpha
        nt.links.new(tr.outputs[0], mx.inputs[1])
        nt.links.new(shader, mx.inputs[2])
        shader = mx.outputs[0]
    if cut:
        # 断面：ワールド座標の x が CUT より大きい所は透明
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        cmp = nt.nodes.new("ShaderNodeMath")
        cmp.operation = "GREATER_THAN"
        cmp.name = "cutval"
        cmp.inputs[1].default_value = CUT["x"]
        tr2 = nt.nodes.new("ShaderNodeBsdfTransparent")
        mx2 = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(geo.outputs["Position"], sep.inputs[0])
        nt.links.new(sep.outputs[0], cmp.inputs[0])
        nt.links.new(cmp.outputs[0], mx2.inputs[0])
        nt.links.new(shader, mx2.inputs[1])
        nt.links.new(tr2.outputs[0], mx2.inputs[2])
        shader = mx2.outputs[0]
    nt.links.new(shader, out.inputs[0])
    return m


def set_cut(x):
    CUT["x"] = x
    for m in bpy.data.materials:
        if m.node_tree and "cutval" in m.node_tree.nodes:
            m.node_tree.nodes["cutval"].inputs[1].default_value = x


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c)


M = dict(
    steel=mat("steel", srgb("#B4542E"), 0.55, 0.2),
    deck=mat("deck", srgb("#9DA3A8"), 0.45, 0.6),
    conc=mat("conc", srgb("#CFCBC3"), 0.85),
    found=mat("found", srgb("#B9B4AA"), 0.9),
    pile=mat("pile", srgb("#8C8780"), 0.8),
    glass=mat("glass", srgb("#3E5566"), 0.08, 0.0, transmission=0.0),
    mull=mat("mull", srgb("#D8DADC"), 0.35, 0.8),
    fence=mat("fence", srgb("#F2F1EC"), 0.7),
    crane=mat("crane", srgb("#F0B323"), 0.45, 0.1),
    dark=mat("dark", srgb("#2B2F33"), 0.6),
    house=mat("house", srgb("#F4F2EC"), 0.85, cut=False),
    roof=mat("roof", srgb("#8E959B"), 0.7, cut=False),
    tree=mat("tree", srgb("#7E9C6A"), 0.9, cut=False),
    trunk=mat("trunk", srgb("#6B5A48"), 0.9, cut=False),
    road=mat("road", srgb("#C4C4C0"), 0.95, cut=False),
    use_off=mat("use_off", srgb("#F3D9B8"), 0.9),
    use_lobby=mat("use_lobby", srgb("#E8590C"), 0.9),
    use_roof=mat("use_roof", srgb("#C7D3DD"), 0.9),
    span=mat("span", srgb("#2C363F"), 0.35, 0.3),
    pave=mat("pave", srgb("#D9D4CA"), 0.9, cut=False),
    curb=mat("curb", srgb("#BDB8AE"), 0.9, cut=False),
    plant=mat("plant", srgb("#6F8C5A"), 0.95, cut=False),
    unit=mat("unit", srgb("#C9CDD1"), 0.4, 0.5),
)


def panel_glass(m):
    """ガラス：1.5m × 階ごとのパネルで少しずつ色を変え、映り込みは残す"""
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    bs.inputs["Roughness"].default_value = 0.035
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sc = nt.nodes.new("ShaderNodeVectorMath")
    sc.operation = "MULTIPLY"
    sc.inputs[1].default_value = (1 / 1.5, 1 / 1.5, 1 / 3.8)
    fl = nt.nodes.new("ShaderNodeVectorMath")
    fl.operation = "FLOOR"
    wn = nt.nodes.new("ShaderNodeTexWhiteNoise")
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*srgb("#34495A"), 1)
    mix.inputs["B"].default_value = (*srgb("#4D6779"), 1)
    nt.links.new(tc.outputs["Object"], sc.inputs[0])
    nt.links.new(sc.outputs[0], fl.inputs[0])
    nt.links.new(fl.outputs[0], wn.inputs["Vector"])
    nt.links.new(wn.outputs["Value"], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], bs.inputs["Base Color"])


panel_glass(M["glass"])


def paving(m, size=0.6):
    """舗装：目地のあるタイル"""
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Color1"].default_value = (*srgb("#DCD7CD"), 1)
    br.inputs["Color2"].default_value = (*srgb("#D2CCC1"), 1)
    br.inputs["Mortar"].default_value = (*srgb("#B9B3A8"), 1)
    br.inputs["Scale"].default_value = 1 / size
    br.inputs["Mortar Size"].default_value = 0.012
    br.offset = 0.5
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], bs.inputs["Base Color"])


paving(M["pave"])


def box(name, x0, y0, z0, x1, y1, z1, m, coll=None):
    me = bpy.data.meshes.new(name)
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(v, [], f)
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    (coll or col_main).objects.link(ob)
    return ob


def cyl(name, x, y, z0, z1, r, m, n=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=r, depth=z1 - z0, location=(x, y, (z0 + z1) / 2))
    ob = bpy.context.object
    ob.name = name
    ob.data.materials.append(m)
    return ob


def merge(objs, name):
    """たくさんの箱を1つにまとめる（表示の切り替えを速くする）"""
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.object
    ob.name = name
    return ob


def bevel(ob, w=0.03):
    """角を少し丸めて、光が稜線に乗るようにする"""
    md = ob.modifiers.new("bevel", "BEVEL")
    md.width = w
    md.segments = 2
    md.limit_method = "ANGLE"
    return ob


def north_y(f):
    """f 階（1始まり）の北面の y。上層はセットバック"""
    return Y1 - (SB["depth"] if f >= SB["from"] else 0.0)


# ---------------------------------------------------------------- 建物（部材ごとに名前を付けて、週で出し入れ）
STAGE = []  # (object, 出す週, 種類)


def add(ob, week, kind="pop"):
    STAGE.append((ob, week, kind))
    return ob


# 杭（頭だけ見える）と基礎
pa, pb = SCHED["杭"]
piles = [(x, y) for x in GX for y in GY]
for i, (x, y) in enumerate(piles):
    add(cyl(f"pile{i}", x, y, -0.4, 0.25, 0.55, M["pile"]), pa + (pb - pa) * i / len(piles))
fa, fb = SCHED["基礎"]
add(box("found", X0 - 1.2, Y0 - 1.2, -0.2, X1 + 1.2, Y1 + 1.2, 0.6, M["found"]), fa, "rise")

# 鉄骨：階ごとに 柱 → 梁 → デッキ
sa, sb = SCHED["鉄骨"]
per = (sb - sa) / NF
for f in range(1, NF + 1):
    z0, z1 = LEV[f - 1] + (0.6 if f == 1 else 0), LEV[f]
    yN = north_y(f)
    ys = [y for y in GY if y <= yN + 1e-6] + ([yN] if yN not in GY else [])
    w0 = sa + per * (f - 1)
    cols = [box(f"c{f}_{x}_{y}", x - 0.25, y - 0.25, z0, x + 0.25, y + 0.25, z1, M["steel"]) for x in GX for y in ys]
    add(bevel(merge(cols, f"cols{f}"), 0.02), w0 + per * 0.05, "rise")
    bm = []
    zt, zb = z1 - 0.05, z1 - 0.75   # H 形鋼 700×300
    for y in ys:
        bm += [box(f"bxt{f}_{y}", X0, y - 0.15, zt - 0.04, X1, y + 0.15, zt, M["steel"]),
               box(f"bxb{f}_{y}", X0, y - 0.15, zb, X1, y + 0.15, zb + 0.04, M["steel"]),
               box(f"bxw{f}_{y}", X0, y - 0.018, zb, X1, y + 0.018, zt, M["steel"])]
    for x in GX:
        bm += [box(f"byt{f}_{x}", x - 0.15, Y0, zt - 0.04, x + 0.15, yN, zt, M["steel"]),
               box(f"byb{f}_{x}", x - 0.15, Y0, zb, x + 0.15, yN, zb + 0.04, M["steel"]),
               box(f"byw{f}_{x}", x - 0.018, Y0, zb, x + 0.018, yN, zt, M["steel"])]
    add(merge(bm, f"beams{f}"), w0 + per * 0.45)
    add(box(f"deck{f}", X0 - 0.3, Y0 - 0.3, z1 - 0.05, X1 + 0.3, yN + 0.3, z1 + 0.12, M["deck"]), w0 + per * 0.8)
    # 中の用途（断面で見える）
    um = M["use_lobby"] if f == 1 else M["use_off"]
    u = box(f"use{f}", X0 + 0.6, Y0 + 0.6, z0 + 0.05, X1 - 0.6, yN - 0.6, z1 - 0.9, um)
    u["use"] = 1
    add(u, SCHED["外装"][1])

# 屋上のパラペットと設備
pr = [box("parS", X0 - 0.3, Y0 - 0.3, TOP, X1 + 0.3, Y0, TOP + 1.1, M["conc"]),
      box("parN", X0 - 0.3, north_y(NF), TOP, X1 + 0.3, north_y(NF) + 0.3, TOP + 1.1, M["conc"]),
      box("parW", X0 - 0.3, Y0, TOP, X0, north_y(NF), TOP + 1.1, M["conc"]),
      box("parE", X1, Y0, TOP, X1 + 0.3, north_y(NF), TOP + 1.1, M["conc"]),
      box("cope", X0 - 0.4, Y0 - 0.4, TOP + 1.1, X1 + 0.4, north_y(NF) + 0.4, TOP + 1.18, M["mull"])]
roof_units = []
for i, x in enumerate((-9.5, -6.5, -3.5)):
    roof_units.append(box(f"ch{i}", x - 1.2, -3.2, TOP + 0.12, x + 1.2, 0.6, TOP + 1.9, M["unit"]))
    for j, yy in enumerate((-2.2, -0.4)):
        roof_units.append(cyl(f"fan{i}{j}", x, yy, TOP + 1.9, TOP + 2.0, 0.7, M["dark"], 24))
for i in range(14):   # 目隠しルーバー
    x = 3.0 + i * 0.5
    roof_units.append(box(f"lv{i}", x, -4.6, TOP + 0.12, x + 0.08, 0.6, TOP + 2.2, M["unit"]))
roof_units.append(box("lvf", 3.0, -4.6, TOP + 2.2, 10.0, 0.6, TOP + 2.28, M["unit"]))
roof_units.append(box("hatch", 11.5, 2.0, TOP + 0.12, 14.0, 4.2, TOP + 2.8, M["conc"]))
add(bevel(merge(pr + roof_units, "roof"), 0.03), SCHED["鉄骨"][1] + 0.5)

# カーテンウォール：階ごとにガラスと方立
ca, cb = SCHED["外装"]
cper = (cb - ca) / NF
for f in range(1, NF + 1):
    z0, z1 = LEV[f - 1] + (0.6 if f == 1 else 0), LEV[f] + 0.12
    yN = north_y(f)
    g = [box(f"gS{f}", X0 - 0.35, Y0 - 0.45, z0, X1 + 0.35, Y0 - 0.35, z1, M["glass"]),
         box(f"gN{f}", X0 - 0.35, yN + 0.35, z0, X1 + 0.35, yN + 0.45, z1, M["glass"]),
         box(f"gW{f}", X0 - 0.45, Y0 - 0.35, z0, X0 - 0.35, yN + 0.35, z1, M["glass"]),
         box(f"gE{f}", X1 + 0.35, Y0 - 0.35, z0, X1 + 0.45, yN + 0.35, z1, M["glass"])]
    ms = []
    nx = int((X1 - X0) / 1.5)
    for i in range(nx + 1):
        x = X0 + i * 1.5
        ms.append(box(f"mS{f}_{i}", x - 0.04, Y0 - 0.6, z0, x + 0.04, Y0 - 0.45, z1, M["mull"]))
        ms.append(box(f"mN{f}_{i}", x - 0.04, yN + 0.45, z0, x + 0.04, yN + 0.6, z1, M["mull"]))
    ny = int((yN - Y0) / 1.5)
    for i in range(ny + 1):
        y = Y0 + i * 1.5
        ms.append(box(f"mW{f}_{i}", X0 - 0.6, y - 0.04, z0, X0 - 0.45, y + 0.04, z1, M["mull"]))
        ms.append(box(f"mE{f}_{i}", X1 + 0.45, y - 0.04, z0, X1 + 0.6, y + 0.04, z1, M["mull"]))
    # 床ごとの横の帯（スパンドレル）
    for side in ((X0 - 0.62, Y0 - 0.62, X1 + 0.62, Y0 - 0.45), (X0 - 0.62, yN + 0.45, X1 + 0.62, yN + 0.62),
                 (X0 - 0.62, Y0 - 0.62, X0 - 0.45, yN + 0.62), (X1 + 0.45, Y0 - 0.62, X1 + 0.62, yN + 0.62)):
        ms.append(box(f"sp{f}", side[0], side[1], z1 - 0.5, side[2], side[3], z1 + 0.1, M["mull"]))
    sd = [box(f"sdS{f}", X0 - 0.47, Y0 - 0.47, z1 - 1.25, X1 + 0.47, Y0 - 0.44, z1 - 0.5, M["span"]),
          box(f"sdN{f}", X0 - 0.47, yN + 0.44, z1 - 1.25, X1 + 0.47, yN + 0.47, z1 - 0.5, M["span"]),
          box(f"sdW{f}", X0 - 0.47, Y0 - 0.47, z1 - 1.25, X0 - 0.44, yN + 0.47, z1 - 0.5, M["span"]),
          box(f"sdE{f}", X1 + 0.44, Y0 - 0.47, z1 - 1.25, X1 + 0.47, yN + 0.47, z1 - 0.5, M["span"])]
    w = ca + cper * (f - 1)
    add(merge(g + sd, f"glass{f}"), w + cper * 0.5)
    add(bevel(merge(ms, f"mull{f}"), 0.012), w + cper * 0.2)

# 1階のエントランスのひさし
add(bevel(box("canopy", -6, Y0 - 4, 3.6, 6, Y0 - 0.6, 3.9, M["conc"]), 0.04), cb)

# 外構：敷地の舗装・縁石・植え込み（外構の工期に入ったら）
fx0_, fy0_, fx1_, fy1_ = SITE
ex = [box("pave", fx0_, fy0_, 0.0, fx1_, fy1_, 0.06, M["pave"]),
      box("walk", fx0_ - 6, fy0_ - 3.2, 0.0, fx1_ + 6, fy0_, 0.12, M["pave"]),
      box("curb", fx0_ - 6, fy0_ - 3.4, 0.0, fx1_ + 6, fy0_ - 3.2, 0.18, M["curb"])]
for (a0, b0, a1, b1) in ((fx0_ + 1, Y1 + 1.2, X1 + 2, fy1_ - 0.8), (fx0_ + 1, Y0 - 1, X0 - 2.5, Y1 + 0.5),
                         (X1 + 2.5, Y0 + 2, fx1_ - 1, Y1 + 0.5)):
    ex.append(box("bed", a0, b0, 0.06, a1, b1, 0.35, M["curb"]))
    ex.append(box("bedg", a0 + 0.15, b0 + 0.15, 0.06, a1 - 0.15, b1 - 0.15, 0.42, M["plant"]))
add(merge(ex, "extern"), SCHED["外構"][0])

# ---------------------------------------------------------------- 仮設：仮囲い・現場事務所・クレーン
fx0, fy0, fx1, fy1 = SITE
fence = []
step = 2.0
for (ax, ay, bx, by) in ((fx0, fy0, fx1, fy0), (fx1, fy0, fx1, fy1), (fx1, fy1, fx0, fy1), (fx0, fy1, fx0, fy0)):
    L = math.hypot(bx - ax, by - ay)
    n = int(L / step)
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n - 0.004
        x0_, y0_ = ax + (bx - ax) * t0, ay + (by - ay) * t0
        x1_, y1_ = ax + (bx - ax) * t1, ay + (by - ay) * t1
        if abs(y0_ - fy0) < 1e-6 and abs(y1_ - fy0) < 1e-6 and -4 < (x0_ + x1_) / 2 < 4:
            continue  # ゲート
        fence.append(box(f"fn{i}", min(x0_, x1_) - 0.05, min(y0_, y1_) - 0.05, 0, max(x0_, x1_) + 0.05, max(y0_, y1_) + 0.05, 3.0, M["fence"]))
FENCE = merge(fence, "fence")
TEMP = [FENCE]
TEMP.append(merge([box("office1", fx0 + 1.5, fy0 + 1.5, 0, fx0 + 9.5, fy0 + 4.5, 2.7, M["fence"]),
                   box("office2", fx0 + 1.5, fy0 + 1.5, 2.8, fx0 + 9.5, fy0 + 4.5, 5.5, M["fence"])], "office"))

# タワークレーン（建物の東側）：格子のマストと三角断面のジブ
CX, CY = X1 + 5.5, 0.0


def strut(name, p, q, r_, m):
    p, q = Vector(p), Vector(q)
    d = q - p
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=r_, depth=d.length, location=(p + q) / 2)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.data.materials.append(m)
    return ob


HW = 1.0
corners = [(CX - HW, CY - HW), (CX + HW, CY - HW), (CX + HW, CY + HW), (CX - HW, CY + HW)]
mast_x = []
SEG = 2.0
for i in range(30):
    z0, z1 = i * SEG, (i + 1) * SEG
    parts = []
    for k in range(4):
        a, b = corners[k], corners[(k + 1) % 4]
        parts.append(strut(f"ch{i}_{k}", (a[0], a[1], z0), (a[0], a[1], z1), 0.09, M["crane"]))
        pa_, pb_ = ((a[0], a[1], z0), (b[0], b[1], z1)) if i % 2 == 0 else ((b[0], b[1], z0), (a[0], a[1], z1))
        parts.append(strut(f"dg{i}_{k}", pa_, pb_, 0.045, M["crane"]))
        parts.append(strut(f"hz{i}_{k}", (a[0], a[1], z1), (b[0], b[1], z1), 0.045, M["crane"]))
    seg = merge(parts, f"mastseg{i}")
    seg["mast"] = 1
    seg["z"] = z0
    mast_x.append(seg)
crane_mast = mast_x[0]
JIB = bpy.data.objects.new("jib", None)
col_main.objects.link(JIB)
jp = []
L_, CL = 30.0, 10.0
for x0_ in np.arange(-CL, L_, 2.0):
    x1_ = x0_ + 2.0
    hgt = 1.6 if x0_ >= 0 else 1.1
    for yy in (-0.7, 0.7):
        jp.append(strut("jc", (x0_, yy, 0), (x1_, yy, 0), 0.08, M["crane"]))
        jp.append(strut("jd", (x0_, yy, 0), ((x0_ + x1_) / 2, 0, hgt), 0.04, M["crane"]))
        jp.append(strut("je", ((x0_ + x1_) / 2, 0, hgt), (x1_, yy, 0), 0.04, M["crane"]))
    jp.append(strut("jt", ((x0_ + x1_) / 2, 0, hgt), ((x0_ + x1_) / 2 + 2.0, 0, hgt), 0.07, M["crane"]))
    jp.append(strut("jh", (x0_, -0.7, 0), (x0_, 0.7, 0), 0.04, M["crane"]))
jp.append(box("cw", -CL, -1.3, -2.0, -CL + 4, 1.3, 0.0, M["conc"]))
jp.append(box("cab", 1.0, 0.8, -2.4, 3.2, 2.6, 0.0, M["dark"]))
jp.append(box("slew", -1.3, -1.3, -0.8, 1.3, 1.3, 0.0, M["crane"]))
for k in range(4):
    a = corners[k]
    jp.append(strut("ap", (a[0] - CX, a[1] - CY, 0), (0, 0, 7.0), 0.08, M["crane"]))
jp.append(strut("tie1", (0, 0, 7.0), (L_ * 0.55, 0, 1.6), 0.03, M["dark"]))
jp.append(strut("tie2", (0, 0, 7.0), (-CL + 1, 0, 1.1), 0.03, M["dark"]))
jo = merge(jp, "jibmesh")
jo.parent = JIB
# 吊り荷（鉄骨の梁）とワイヤー
HOOK = bpy.data.objects.new("hook", None)
col_main.objects.link(HOOK)
HOOK.parent = JIB
wire = box("wire", -0.03, -0.03, -1, 0.03, 0.03, 0, M["dark"])
wire.parent = HOOK
load = box("load", -3, -0.18, -0.4, 3, 0.18, 0.3, M["steel"])
load.parent = HOOK
TEMP += [jo, wire, load]

# ---------------------------------------------------------------- 周りの町（北は低い住宅、南は道路）
rng = np.random.default_rng(3)
town = []
town.append(box("road", -120, fy0 - 11, -0.02, 120, fy0 - 1, 0.0, M["road"]))
for i, x in enumerate(np.arange(-70, 71, 13.0)):
    for j, y in enumerate((fy1 + 6, fy1 + 21, fy1 + 36)):
        if rng.random() < 0.15:
            continue
        w_, d_ = rng.uniform(8, 10.5), rng.uniform(8, 11)
        h_ = rng.choice([6.5, 7.2, 9.5])
        xx, yy = x + rng.uniform(-1, 1), y + rng.uniform(-1, 1)
        town.append(box(f"h{i}_{j}", xx - w_ / 2, yy - d_ / 2, 0, xx + w_ / 2, yy + d_ / 2, h_, M["house"]))
        town.append(box(f"hr{i}_{j}", xx - w_ / 2 - 0.2, yy - d_ / 2 - 0.2, h_, xx + w_ / 2 + 0.2, yy + d_ / 2 + 0.2, h_ + 0.25, M["roof"]))
for x in list(np.arange(-70, -26, 13.0)) + list(np.arange(30, 71, 13.0)):
    for y in (2.0, -12.0 + 14):
        w_, d_, h_ = rng.uniform(9, 12), rng.uniform(9, 13), rng.choice([7.2, 10.5, 13.0])
        town.append(box(f"s{x}_{y}", x - w_ / 2, y - d_ / 2, 0, x + w_ / 2, y + d_ / 2, h_, M["house"]))
for x in np.arange(-70, 71, 14.0):
    w_, d_, h_ = rng.uniform(10, 12), rng.uniform(10, 14), rng.choice([10.0, 13.5, 16.0])
    y = fy0 - 20
    town.append(box(f"sv{x}", x - w_ / 2, y - d_ / 2, 0, x + w_ / 2, y + d_ / 2, h_, M["house"]))
TOWN = merge(town, "town")

trees = []
for i, x in enumerate(np.arange(-16, 17, 8.0)):
    y = fy0 - 0.4 - 0.9
    trees.append(cyl(f"tt{i}", x, y, 0, 2.2, 0.15, M["trunk"], 8))
    for k, (dx, dy, dz, rr) in enumerate(((0, 0, 3.7, 1.6), (0.7, 0.3, 3.2, 1.2), (-0.6, -0.2, 3.3, 1.25), (0.1, 0.4, 4.5, 1.1))):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=rr, location=(x + dx, y + dy, dz))
        s = bpy.context.object
        tx = bpy.data.textures.new(f"leaf{i}{k}", "CLOUDS")
        tx.noise_scale = 0.45
        dm = s.modifiers.new("d", "DISPLACE")
        dm.texture = tx
        dm.strength = 0.35
        bpy.context.view_layer.objects.active = s
        bpy.ops.object.modifier_apply(modifier="d")
        s.data.materials.append(M["tree"])
        trees.append(s)
TREES = merge(trees, "trees")
add(TREES, cb + 1)

# ---------------------------------------------------------------- 地面（影受け）・光・カメラ
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, 0))
GROUND = bpy.context.object
GROUND.name = "ground"
gm = mat("groundmat", srgb("#E9E6DF"), 0.95, cut=False)
GROUND.data.materials.append(gm)

SUN = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
col_main.objects.link(SUN)
SUN.data.angle = math.radians(1.2)


def sun_dir(alt_deg, az_deg):
    """方位角は北=0・東=90。太陽へ向かう単位ベクトル（x=東, y=北）"""
    a, z = math.radians(alt_deg), math.radians(az_deg)
    return Vector((math.cos(a) * math.sin(z), math.cos(a) * math.cos(z), math.sin(a)))


def set_sun(alt, az, strength=4.0):
    d = sun_dir(alt, az)
    SUN.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    SUN.data.energy = strength


world = bpy.data.worlds.new("w")
scn.world = world
world.use_nodes = True
WBG = world.node_tree.nodes["Background"]
WBG.inputs[0].default_value = (*srgb("#DCE3EA"), 1)
WBG.inputs[1].default_value = 0.9

CAM = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
col_main.objects.link(CAM)
scn.camera = CAM


def look(cam, pos, target, lens=None, ortho=None):
    cam.location = pos
    d = Vector(target) - Vector(pos)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho
    else:
        cam.data.type = "PERSP"
        cam.data.lens = lens


r = scn.render
r.engine = "CYCLES"
scn.cycles.device = "GPU"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "METAL"
prefs.get_devices()
for d in prefs.devices:
    d.use = True
scn.cycles.samples = 32
scn.cycles.transparent_max_bounces = 128
scn.cycles.max_bounces = 8
scn.cycles.use_denoising = True
scn.view_settings.view_transform = "AgX"
scn.view_settings.look = "AgX - Medium High Contrast"
r.image_settings.file_format = "PNG"
r.image_settings.color_mode = "RGBA"
r.resolution_percentage = 100


# ---------------------------------------------------------------- 週 → 見た目
def apply_week(w):
    for ob, wk, kind in STAGE:
        on = w >= wk
        ob.hide_render = not on
        if kind == "rise" and on:
            t = clamp01((w - wk) / 0.8)
            ob.scale = (1, 1, max(0.02, t))
        else:
            ob.scale = (1, 1, 1)
    # 仮設は外装が終わるまで
    end = SCHED["外装"][1]
    for o in TEMP:
        o.hide_render = w > end
    # クレーン：マストは建っている最上階 + 9m、ジブは週ごとに回る
    built = 0
    for f in range(1, NF + 1):
        if w >= SCHED["鉄骨"][0] + (SCHED["鉄骨"][1] - SCHED["鉄骨"][0]) / NF * (f - 1):
            built = f
    mh = max(16.0, LEV[built] + 10.0)
    mh = math.ceil(mh / SEG) * SEG
    for m_ in mast_x:
        m_.hide_render = (m_["z"] >= mh) or (w > end)
    JIB.location = (CX, CY, mh)
    ang = math.radians(178 + 22 * math.sin(w * 0.32))
    JIB.rotation_euler = (0, 0, ang)
    HOOK.location = (18 - 4 * math.sin(w * 0.27), 0, 0)
    drop = 6 + 2.5 * math.sin(w * 0.3)
    wire.scale = (1, 1, drop)
    load.location = (0, 0, -drop - 0.3)
    JIB.hide_render = w > end


def sky_reflect(strength=0.09):
    """背景は透明のまま、ガラスに空のグラデーションが映るように空を入れる"""
    sky = world.node_tree.nodes.new("ShaderNodeTexSky")
    sky.sun_elevation = math.radians(38)
    sky.sun_rotation = math.radians(160)
    sky.sun_disc = False
    world.node_tree.links.new(sky.outputs[0], WBG.inputs[0])
    WBG.inputs[1].default_value = strength


def no_use():
    for o in bpy.data.objects:
        if o.get("use"):
            o.hide_render = True


def setup_out(w_, h_, path):
    r.resolution_x, r.resolution_y = w_, h_
    r.filepath = path


def render(path):
    r.filepath = path
    bpy.ops.render.render(write_still=True)


# ---------------------------------------------------------------- モード
OUT = os.path.join(HERE, "frames")
CAM_PROG = dict(pos=(64, -78, 52), target=(1.5, 2, 13.5), lens=50)


def mode_progress(first, last):
    sky_reflect()
    r.film_transparent = True
    GROUND.is_shadow_catcher = True
    TOWN.hide_render = True
    set_sun(38, 160, 4.2)
    look(CAM, **CAM_PROG)
    r.resolution_x, r.resolution_y = 1040, 1200
    os.makedirs(f"{OUT}/progress", exist_ok=True)
    for w in range(first, last + 1):
        apply_week(w)
        no_use()
        render(f"{OUT}/progress/p{w:02d}.png")


def mode_section(first, last, n=24):
    sky_reflect()
    r.film_transparent = True
    GROUND.is_shadow_catcher = True
    TOWN.hide_render = True
    set_sun(38, 160, 4.2)
    look(CAM, **CAM_PROG)
    r.resolution_x, r.resolution_y = 1040, 1200
    apply_week(SCHED["外装"][1] + 2)
    for o in bpy.data.objects:
        if o.get("use"):
            o.hide_render = False
    os.makedirs(f"{OUT}/section", exist_ok=True)
    for i in range(first, last + 1):
        t = i / (n - 1)
        e = t * t * (3 - 2 * t)
        set_cut(X1 + 1.5 - e * (X1 + 1.5 - 0.0))
        render(f"{OUT}/section/s{i:02d}.png")


def lit_glass():
    """明かりのついた階のガラス：映り込みは残し、窓（1.5m）ごとに室内の明るさを変え、天井の照明の帯だけ強く光らせる"""
    m = mat("litglass", srgb("#26303B"), 0.06)
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    bs.inputs["Emission Color"].default_value = (*srgb("#FFD2A0"), 1)
    N = nt.nodes.new
    L = nt.links.new
    tc = N("ShaderNodeTexCoord")
    sc = N("ShaderNodeVectorMath")
    sc.operation = "MULTIPLY"
    sc.inputs[1].default_value = (1 / 1.5, 1 / 1.5, 0)
    fl = N("ShaderNodeVectorMath")
    fl.operation = "FLOOR"
    wn = N("ShaderNodeTexWhiteNoise")
    ramp = N("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "LINEAR"
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.22, (0.03, 0.03, 0.03, 1)
    els[1].position, els[1].color = 0.3, (0.55, 0.55, 0.55, 1)
    e2 = els.new(1.0)
    e2.color = (1.0, 1.0, 1.0, 1)
    L(tc.outputs["Object"], sc.inputs[0])
    L(sc.outputs[0], fl.inputs[0])
    L(fl.outputs[0], wn.inputs["Vector"])
    L(wn.outputs["Value"], ramp.inputs["Fac"])
    # 階の中の高さ（0〜1）：天井の近くに照明の帯
    sz = N("ShaderNodeSeparateXYZ")
    L(tc.outputs["Generated"], sz.inputs[0])
    g1 = N("ShaderNodeMath"); g1.operation = "GREATER_THAN"; g1.inputs[1].default_value = 0.74
    g2 = N("ShaderNodeMath"); g2.operation = "LESS_THAN"; g2.inputs[1].default_value = 0.8
    L(sz.outputs[2], g1.inputs[0]); L(sz.outputs[2], g2.inputs[0])
    strip = N("ShaderNodeMath"); strip.operation = "MULTIPLY"
    L(g1.outputs[0], strip.inputs[0]); L(g2.outputs[0], strip.inputs[1])
    amp = N("ShaderNodeMath"); amp.operation = "MULTIPLY_ADD"
    amp.inputs[1].default_value = 2.2
    amp.inputs[2].default_value = 0.16
    L(strip.outputs[0], amp.inputs[0])
    tot = N("ShaderNodeMath"); tot.operation = "MULTIPLY"
    L(ramp.outputs["Color"], tot.inputs[0]); L(amp.outputs[0], tot.inputs[1])
    L(tot.outputs[0], bs.inputs["Emission Strength"])
    return m


def mode_dusk(first, last, n=12):
    r.film_transparent = False
    TOWN.hide_render = False
    apply_week(SCHED["外装"][1] + 2)
    no_use()
    sky = world.node_tree.nodes.new("ShaderNodeTexSky")
    world.node_tree.links.new(sky.outputs[0], WBG.inputs[0])
    WBG.inputs[1].default_value = 0.35
    sky.sun_elevation = math.radians(-1.0)
    sky.sun_rotation = math.radians(250)
    set_sun(2.0, 250, 1.2)
    SUN.data.color = srgb("#FFB070")
    look(CAM, pos=(26, -21, 1.6), target=(-1, 0, 15.5), lens=21)
    lit = lit_glass()
    r.resolution_x, r.resolution_y = 1040, 1200
    os.makedirs(f"{OUT}/dusk", exist_ok=True)
    order = [3, 6, 1, 8, 4, 2, 7, 5]
    for i in range(first, last + 1):
        k = round(i / (n - 1) * NF)
        for f in range(1, NF + 1):
            g = bpy.data.objects[f"glass{f}"]
            g.data.materials.clear()
            g.data.materials.append(lit if f in order[:k] else M["glass"])
        render(f"{OUT}/dusk/d{i:02d}.png")


def mode_turn(first, last, n=48):
    """完成した建物の周りを一周する（スライドでドラッグして回す）。太陽は固定なので影も回る"""
    sky_reflect()
    r.film_transparent = True
    GROUND.is_shadow_catcher = True
    TOWN.hide_render = True
    set_sun(38, 160, 4.2)
    r.resolution_x, r.resolution_y = 1040, 1200
    apply_week(SCHED["外構"][1])
    no_use()
    px, py, pz = CAM_PROG["pos"]
    tx, ty, tz = CAM_PROG["target"]
    rad = math.hypot(px - tx, py - ty)
    a0 = math.atan2(py - ty, px - tx)
    os.makedirs(f"{OUT}/turn", exist_ok=True)
    for i in range(first, last + 1):
        a = a0 + 2 * math.pi * i / n
        look(CAM, pos=(tx + rad * math.cos(a), ty + rad * math.sin(a), pz), target=(tx, ty, tz), lens=CAM_PROG["lens"])
        render(f"{OUT}/turn/t{i:02d}.png")


def mode_test():
    mode_progress(*[int(a) for a in argv[1:3]] if len(argv) > 2 else (30, 30))


if MODE == "progress":
    mode_progress(int(argv[1]), int(argv[2]))
elif MODE == "section":
    mode_section(int(argv[1]), int(argv[2]))
elif MODE == "turn":
    mode_turn(int(argv[1]), int(argv[2]))
elif MODE == "dusk":
    mode_dusk(int(argv[1]), int(argv[2]))
elif MODE == "lib":
    pass  # shade.py・labels.py から部品として読み込む
elif MODE == "save":
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "blend", "sekou.blend"))
else:
    mode_test()
