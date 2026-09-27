# 動くスライド（ugoku-slide）
#   make build   src/ と engine/ から docs/（公開するサイト）を書き出す
#   make check   docs/ が最新か・Python の書き方の確認
#   make qa      全スライドをブラウザで開いて確かめる（要 playwright、build/qa/ に画像）
#   make og      共有用の画像 docs/og.png を作り直す（要 playwright）
#   make serve   http://localhost:8000 で一覧ページを見る

PYTHON ?= python3

.PHONY: build check qa og serve clean

build:
	$(PYTHON) tools/build.py

check:
	$(PYTHON) tools/build.py --check
	$(PYTHON) -m pyflakes tools

qa: build
	$(PYTHON) tools/qa.py

og: build
	$(PYTHON) tools/og.py

serve: build
	cd docs && $(PYTHON) -m http.server 8000

clean:
	rm -rf build
