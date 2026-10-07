"""断面の各階・クレーンなどの、画面上の位置（0〜1）を書き出す。スライドのラベルを置くのに使う。"""
import os
import sys
import json

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = ["x", "--", "lib"]
from scene import CAM, CAM_PROG, LEV, NF, TOP, Y0, look, north_y, r, scn  # noqa: E402
look(CAM, **CAM_PROG)
r.resolution_x, r.resolution_y = 1040, 1200
bpy.context.view_layer.update()
def at(p):
    v = world_to_camera_view(scn, CAM, Vector(p))
    return [round(v.x, 4), round(1 - v.y, 4)]
out = {"floors": [at((0.0, (Y0 + north_y(f)) / 2, (LEV[f - 1] + LEV[f]) / 2)) for f in range(1, NF + 1)],
       "roof": at((0.0, 0, TOP + 1)), "ground": at((0.0, Y0, 0))}
os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
json.dump(out, open(os.path.join(HERE, "data", "labels.json"), "w"), indent=1)
print(out)
