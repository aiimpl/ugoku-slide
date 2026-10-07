"""日影のコマ：冬至の東京、真太陽時 8:00〜16:00。測定面は地上4m。

blender -b --factory-startup -P shade.py -- [first last]
規制は 第一種中高層住居専用地域（二）の例：敷地境界から 5〜10m は4時間、10m を超える範囲は2.5時間まで。
地面に重ねる絵（累積の日影時間・規制の線・超えた所の赤）は numpy で計算して、コマごとに作り直す。
"""
import os
import sys
import json
import math

import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
_argv = sys.argv
sys.argv = ["x", "--", "lib"]
from scene import (CAM, LEV, NF, OUT, SB, SCHED, SITE, TAG, TOP, TOWN, TREES, WBG, X0, X1, Y0, Y1,  # noqa: E402
                   apply_week, gm, look, no_use, north_y, r, render, scn, set_sun, srgb, sun_dir)
sys.argv = _argv
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

LAT = 35.68
DEC = -23.44
ZM = 4.0                      # 測定面
T0, T1 = 8.0, 16.0
N_FR = 33                     # 15分ごと
DT = 1 / 60                   # 累積の刻み（1分）
LIM = {"near": 4.0, "far": 2.5}

# 地面の絵の範囲（m）と解像度
EX = (-70.0, 70.0, -40.0, 100.0)
PX = 0.25
NX = int((EX[1] - EX[0]) / PX)
NY = int((EX[3] - EX[2]) / PX)
xs = EX[0] + (np.arange(NX) + 0.5) * PX
ys = EX[2] + (np.arange(NY) + 0.5) * PX
GXX, GYY = np.meshgrid(xs, ys)  # [NY, NX]


def sun_altaz(t):
    phi, dec = math.radians(LAT), math.radians(DEC)
    H = math.radians(15 * (t - 12))
    alt = math.asin(math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(H))
    az_s = math.atan2(math.sin(H), math.cos(H) * math.sin(phi) - math.tan(dec) * math.cos(phi))
    return math.degrees(alt), (math.degrees(az_s) + 180) % 360


# 建物の塊（ガラス面の外側まで）
yN_up = north_y(NF) + 0.6
BOXES = [(X0 - 0.6, Y0 - 0.6, 0.0, X1 + 0.6, Y1 + 0.6, LEV[SB["from"] - 1] + 0.12),
         (X0 - 0.6, Y0 - 0.6, 0.0, X1 + 0.6, yN_up, TOP + 1.1)]


def shadow_mask(t):
    alt, az = sun_altaz(t)
    d = np.array(sun_dir(alt, az))
    hit = np.zeros(GXX.shape, bool)
    P = [GXX, GYY, np.full(GXX.shape, ZM)]
    for b in BOXES:
        lo, hi = b[:3], b[3:]
        tmin = np.zeros(GXX.shape)
        tmax = np.full(GXX.shape, 1e9)
        ok = np.ones(GXX.shape, bool)
        for k in range(3):
            if abs(d[k]) < 1e-9:
                ok &= (P[k] >= lo[k]) & (P[k] <= hi[k])
                continue
            t1 = (lo[k] - P[k]) / d[k]
            t2 = (hi[k] - P[k]) / d[k]
            tmin = np.maximum(tmin, np.minimum(t1, t2))
            tmax = np.minimum(tmax, np.maximum(t1, t2))
        hit |= ok & (tmax >= tmin) & (tmax > 0)
    return hit


# 敷地からの距離（敷地の外側）
sx0, sy0, sx1, sy1 = SITE
dx = np.maximum(np.maximum(sx0 - GXX, GXX - sx1), 0)
dy = np.maximum(np.maximum(sy0 - GYY, GYY - sy1), 0)
DIST = np.hypot(dx, dy)
ZONE_NEAR = (DIST > 5) & (DIST <= 10)
ZONE_FAR = DIST > 10
# 道路（南）は規制の対象外として外す
ZONE_NEAR &= GYY > sy0 - 1
ZONE_FAR &= GYY > sy0 - 1

ts = np.arange(T0, T1 + 1e-6, DT)
CUM = [np.zeros(GXX.shape)]          # CUM[n] = 8:00 から n 分までの日影時間
for t in ts[:-1]:
    CUM.append(CUM[-1] + shadow_mask(t + DT / 2) * DT)
print("sun 8/12/16:", [tuple(round(v, 1) for v in sun_altaz(t)) for t in (8, 12, 16)])


def hours_until(t):
    n = int(round((t - T0) / DT))
    return CUM[max(0, min(n, len(CUM) - 1))]


def line_mask(d, width=0.35, dash=None):
    m = (np.abs(DIST - d) < width / 2) if d > 0 else ((DIST > 0) & (DIST < width))
    m &= GYY > sy0 - 1
    if dash:
        s = (GXX + GYY) % (dash * 2) < dash
        m &= s
    return m


def rgba_for(t):
    H = hours_until(t)
    img = np.zeros(GXX.shape + (4,), np.float32)
    # 累積の日影時間（濃さで）
    a = np.clip(H / 4.0, 0, 1)
    col = np.array(srgb("#6E8296"))
    img[..., :3] = col
    img[..., 3] = np.where(H > 0, 0.06 + a * 0.22, 0)
    over = (ZONE_NEAR & (H > LIM["near"])) | (ZONE_FAR & (H > LIM["far"]))
    red = np.array(srgb("#E03A1E"))
    img[over, :3] = red
    img[over, 3] = 0.78
    # 線：敷地境界（実線）・5m（橙の破線）・10m（赤の破線）
    for m_, c_, a_ in ((line_mask(0, 0.3), srgb("#1B1F24"), 0.9),
                       (line_mask(5, 0.3, 1.2), srgb("#E8590C"), 0.95),
                       (line_mask(10, 0.3, 1.2), srgb("#B3261E"), 0.95)):
        img[m_, :3] = c_
        img[m_, 3] = a_
    return img, H, over


# 地面に重ねる板
bpy.ops.mesh.primitive_plane_add(size=1, location=((EX[0] + EX[1]) / 2, (EX[2] + EX[3]) / 2, 0.02))
PL = bpy.context.object
PL.scale = (EX[1] - EX[0], EX[3] - EX[2], 1)
IMG = bpy.data.images.new("shade", NX, NY, alpha=True, float_buffer=True)
IMG.colorspace_settings.name = "Linear Rec.709"
pm = bpy.data.materials.new("plate")
pm.use_nodes = True
nt = pm.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
o_ = nt.nodes.new("ShaderNodeOutputMaterial")
tx = nt.nodes.new("ShaderNodeTexImage")
tx.image = IMG
tx.interpolation = "Linear"
df = nt.nodes.new("ShaderNodeBsdfPrincipled")
df.inputs["Roughness"].default_value = 1.0
tr = nt.nodes.new("ShaderNodeBsdfTransparent")
mx = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(tx.outputs["Color"], df.inputs["Base Color"])
nt.links.new(tx.outputs["Alpha"], mx.inputs[0])
nt.links.new(tr.outputs[0], mx.inputs[1])
nt.links.new(df.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], o_.inputs[0])
PL.data.materials.append(pm)

# 見せ方：完成した建物、町は隠して平面図のように
apply_week(SCHED["外構"][1] + 1)
no_use()
TOWN.hide_render = True
TREES.hide_render = False
r.film_transparent = False
WBG.inputs[0].default_value = (*srgb("#F4F1EA"), 1)
WBG.inputs[1].default_value = 1.0
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*srgb("#ECE8DF"), 1)
look(CAM, pos=(18, -85, 125), target=(0, 26, 0), ortho=132)
r.resolution_x, r.resolution_y = 1400, 1040
scn.cycles.samples = 40

SHD = f"{OUT}/shade{TAG}"   # 階数ちがいは shade_6F などに分ける
os.makedirs(SHD, exist_ok=True)
first, last = (int(args[0]), int(args[1])) if len(args) >= 2 else (0, N_FR - 1)
info = {"frames": []}
for i in range(first, last + 1):
    t = T0 + (T1 - T0) * i / (N_FR - 1)
    alt, az = sun_altaz(t)
    set_sun(alt, az, 4.5)
    rgba, H, over = rgba_for(t)
    IMG.pixels.foreach_set(rgba.ravel())
    IMG.update()
    render(f"{SHD}/h{i:02d}.png")
    info["frames"].append({"i": i, "t": t, "alt": round(alt, 2), "az": round(az, 2),
                           "over_m2": round(float(over.sum()) * PX * PX, 1),
                           "max_far_h": round(float(H[ZONE_FAR].max()), 2),
                           "max_near_h": round(float(H[ZONE_NEAR].max()), 2)})
    print(info["frames"][-1])
# ラベルを置く位置（画面の割合）
def at(p):
    v = world_to_camera_view(scn, CAM, Vector(p))
    return [round(v.x, 4), round(1 - v.y, 4)]
info["labels"] = {"site": at((sx1 - 6, sy1, 0)), "l5": at((sx1 - 6, sy1 + 5, 0)), "l10": at((sx1 - 6, sy1 + 10, 0)),
                  "north": at((0, sy1 + 30, 0))}
if TAG or (first == 0 and last == N_FR - 1):
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    json.dump(info, open(os.path.join(HERE, "data", f"shade{TAG}.json"), "w"), ensure_ascii=False, indent=1)
