#!/bin/sh
# 全部のコマを書き出す（工程 0〜52週・断面24コマ・夕景12コマ）
cd "$(dirname "$0")"
B="blender -b --factory-startup -P scene.py --"
$B progress 0 52 >/dev/null 2>&1
$B section 0 23 >/dev/null 2>&1
$B dusk 0 11 >/dev/null 2>&1
echo ALLDONE
