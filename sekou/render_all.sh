#!/bin/sh
# 全部のコマを書き出す（工程53・一周48・断面24・夕景12・日影33）
cd "$(dirname "$0")"
B="blender -b --factory-startup -P"
$B scene.py -- progress 0 52 >/dev/null 2>&1; echo "progress $(date +%H:%M)"
$B scene.py -- turn 0 47 >/dev/null 2>&1; echo "turn $(date +%H:%M)"
$B scene.py -- section 0 23 >/dev/null 2>&1; echo "section $(date +%H:%M)"
$B scene.py -- dusk 0 11 >/dev/null 2>&1; echo "dusk $(date +%H:%M)"
$B shade.py -- 0 32 >/dev/null 2>&1; echo "shade $(date +%H:%M)"
echo ALLDONE
