# 動くスライド（ugoku-slide）
#   make build   src/ と engine/ から docs/（公開するサイト）を書き出す
#   make check   docs/ が最新か・Python の書き方の確認
#   make qa      全スライドをブラウザで開いて確かめる（要 playwright、build/qa/ に画像）
#   make og      共有用の画像 docs/og.png を作り直す（要 playwright）
#   make video   紹介動画 build/video/ugoku-slide_26s.mp4（要 playwright・NumPy・ffmpeg、約10分）
#   make video2  第2弾の紹介動画 build/video/ugoku-slide-vol2_26s.mp4（約10分）
#   make video3  第3弾の紹介動画 build/video/ugoku-slide-vol3_25s.mp4
#   make clips   操作を見せる短い動画 build/video/clip_mark.mp4・clip_demo.mp4
#   make serve   http://localhost:8000 で一覧ページを見る

PYTHON ?= python3

.PHONY: build check qa og video video2 video3 clips serve clean

build:
	$(PYTHON) tools/build.py

check:
	$(PYTHON) tools/build.py --check
	$(PYTHON) -m pyflakes tools video

qa: build
	$(PYTHON) tools/qa.py

og: build
	$(PYTHON) tools/og.py

video: build
	$(PYTHON) video/make_video.py

video2: build
	$(PYTHON) video/make_video2.py

video3: build
	$(PYTHON) video/make_video3.py

clips: build
	$(PYTHON) video/make_clips.py

serve: build
	cd docs && $(PYTHON) -m http.server 8000

clean:
	rm -rf build
