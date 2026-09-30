# 動くスライド（ugoku-slide）
#   make build   src/ と engine/ から docs/（公開するサイト）を書き出す
#   make check   docs/ が最新か・Python の書き方の確認
#   make qa      全スライドをブラウザで開いて確かめる（要 playwright、build/qa/ に画像）
#   make og      共有用の画像 docs/og.png を作り直す（要 playwright）
#   make video   紹介動画 build/video/ugoku-slide_26s.mp4（要 playwright・NumPy・ffmpeg、約10分）
#   make video2  第2弾の紹介動画 build/video/ugoku-slide-vol2_26s.mp4（約10分）
#   make serve   http://localhost:8000 で一覧ページを見る

PYTHON ?= python3

.PHONY: build check qa og video video2 serve clean

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

serve: build
	cd docs && $(PYTHON) -m http.server 8000

clean:
	rm -rf build
