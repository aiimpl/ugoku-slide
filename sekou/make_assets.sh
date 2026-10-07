#!/bin/sh
# Blender のコマ（PNG）をスライド用の WebP にする
cd "$(dirname "$0")"
A=../src/assets/sekou
mkdir -p "$A"
for f in frames/progress/p*.png frames/section/s*.png; do
  cwebp -quiet -q 80 -alpha_q 85 -resize 780 900 "$f" -o "$A/$(basename "${f%.png}").webp"
done
for f in frames/dusk/d*.png; do
  cwebp -quiet -q 80 -resize 780 900 "$f" -o "$A/$(basename "${f%.png}").webp"
done
for f in frames/shade/h*.png; do
  cwebp -quiet -q 80 -resize 1050 780 "$f" -o "$A/$(basename "${f%.png}").webp"
done
du -sh "$A"
