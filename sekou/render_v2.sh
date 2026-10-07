#!/bin/sh
# 第4弾の2：図面入りの着工前・分解図・階数ちがいの完成と日影
cd "$(dirname "$0")"
B="blender -b --factory-startup -P"
$B scene.py -- progress 0 8 >/dev/null 2>&1; echo "progress 0-8 $(date +%H:%M)"
$B scene.py -- explode 0 23 >/dev/null 2>&1; echo "explode $(date +%H:%M)"
$B scene.py -- final >/dev/null 2>&1
for n in 6 7; do
  SEKOU_SPEC=spec_${n}F.json SEKOU_TAG=_${n}F $B scene.py -- final >/dev/null 2>&1
  SEKOU_SPEC=spec_${n}F.json SEKOU_TAG=_${n}F $B shade.py -- 32 32 >/dev/null 2>&1
done
echo "vol $(date +%H:%M)"
echo ALLDONE
