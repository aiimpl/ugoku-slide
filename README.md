# 動くスライド（ugoku-slide）

押すと根拠が開き、数字を動かすとその場で再計算される「動くスライド」の雛形集です。
第2弾（51〜62）では、ページをめくっても図形が途切れず次の形へ変形してつながる動きと、回せる立体・表を貼って作り直すグラフを足しました。
どれも **1ファイルで完結する HTML** なので、ダウンロードしてダブルクリックすればブラウザで動きます。全部無料（MIT）。

**一覧と見本 → https://aiimpl.github.io/ugoku-slide/**

## できること

- 雛形は様式も用途も別々。1本ずつ「誰が・どんな場面で使うか」を決めて作っています（一覧ページに書いてあります）
- どの雛形にも入っている動き
  - `→` で要点が順番に出る
  - クリックで根拠・計算式が開く
  - スライダーを動かすと、売上・費用・人数などがその場で計算し直される
  - 切り替えタブ、重みを変えると順位が入れ替わる比較、クイズ、グラフ、コードの段階強調（雛形による）
- 第2弾で増えた動き（全62本の仕組みに入っていて、第1弾の雛形でも使える）
  - `data-morph`：前後のページで同じ名前の要素が、位置・大きさ・色を保ったまま変形してつながる
  - スライダーで数字だけでなく、図形の大きさ・傾き・位置が動く（入力が CSS 変数になる）
  - `data-orbit`：ドラッグで回せる立体・分解図（CSS の 3D。外部の読み込みなし）
  - `data-sheet`：表の数字を直す・Excel でコピーした表を貼ると、グラフと集計が作り直される
  - `.draw`：線が描かれて図が組み上がる
- 発表の道具：全画面、一覧、発表者メモ、別ウィンドウの発表者画面（メモ・次のページ・経過時間）、暗転
- 1280×720 のまま画面に合わせて拡大縮小するので、どのパソコンでもレイアウトが崩れない。スマホはスワイプで送れる
- ブラウザの印刷から PDF に保存すると、1ページ1枚・補足を開いた状態で出る

## 使い方（ターミナル不要）

1. 一覧ページで気に入った雛形の「ダウンロード」を押す（全部まとめた zip もあります）
2. Claude（デスクトップアプリか claude.ai）にファイルをドラッグし、「Claude用の指示をコピー」で写した文を貼って、テーマと数字を書き足して送る
3. 出てきた HTML をプレビューで確かめ、「3枚目の文字を大きく」のように話しかけて直す。できたらダウンロード

各ファイルの先頭コメントに「使える部品と書き方」が入っているので、Claude はそれを読んで同じ作りのまま中身を書き換えます。

### Claude のスキルとして入れる

一覧ページの「Claude 用スキル（zip）」（`docs/ugoku-slide-skill.zip`）を入れると、ファイルを渡さなくても
「動くスライドで、〇〇の資料を作って」と頼むだけで、62種から場面に合う雛形を選んで作ります。

- claude.ai・デスクトップアプリ：Settings → Capabilities でコードの実行をオンにし、Customize → Skills →「＋」→ Upload a skill で zip を選ぶ
- Claude Code：zip を解凍してできた `ugoku-slide` フォルダを `~/.claude/skills/` に置く

中身は SKILL.md（作り方）・雛形62本と一覧（templates/index.json）・部品と決まりの説明（reference/）・崩れを確かめるスクリプト（scripts/check.py）。元は `skill/` にあり、`make build` で zip になります。
自分で直すときも、そのコメントを見ればどの class を付ければ何が動くかが分かります。

## 動作環境

Chrome・Edge・Safari・Firefox の最近の版。外部から読むのは Google Fonts だけで、つながらなくてもパソコンにある書体で表示されます。

## 構成

```
engine/        全スライド共通の仕組み（engine.css・engine.js）と、各ファイル先頭に入る説明（guide.txt）
src/decks/     雛形の元（デザインと中身だけ）。作り方は src/DECKS.md
src/index.html 一覧ページの元
tools/build.py engine と src を合体して docs/ に書き出す（1ファイルで完結する HTML と、まとめた zip）
tools/qa.py    書き出したスライドをブラウザで開いて、エラー・はみ出し・計算を確かめ、画像を撮る
tools/morphqa.py ページ送りの途中のコマを撮る（data-morph の確認用）
skill/         Claude のスキル（SKILL.md と確かめるスクリプト。雛形と説明は build で足される）
docs/          公開しているサイト（GitHub Pages）
```

## 手元で作り直す

```sh
make build   # docs/ を書き出す（Python 3 だけで動く。数秒）
make serve   # http://localhost:8000 で一覧を見る
make check   # docs/ が最新か確かめる

# ブラウザでの確認（任意）
pip install -r requirements-dev.txt && playwright install chromium
make qa      # build/qa/<名前>/ にスライドごとの画像
python3 tools/morphqa.py 51   # build/morph/51_board.png に、ページ送りの途中のコマ
```

雛形を足すときは `src/decks/NN-名前.html` を作って `make build` するだけです。決まりは [src/DECKS.md](src/DECKS.md)。

## 紹介動画

第2弾の紹介動画（26.5秒）は `make video2` で `build/video/ugoku-slide-vol2_26s.mp4` に作ります（台本は `video/make_video2.py`、場面は `video/stages2.py`、BGM は `video/music2.py`）。
以下は第1弾の動画の作り方です。

`make video` で、紹介動画（1920×1080・30fps・26秒・BGM つき）を `build/video/ugoku-slide_26s.mp4` に作ります。
実際のスライドをブラウザで開き、スライダーやクリックを台本どおりに動かしながら1コマずつ撮っています。
撮影中はページの時計（CSS アニメーションと `performance.now`）を約8分の1の速さに落としているので、撮影に時間がかかってもなめらかに仕上がります。
BGM は NumPy で合成しています（`video/music.py`）。場面の切り替わりは、すべて拍に合わせています。

```
video/record.py      ゆっくり撮影して 30fps のコマにする
video/fx.js・fx.css  撮影用のテロップ・カーソル・クリックの演出
video/stages.py      冒頭・早送り・一覧の壁・頼み方・締めの場面（HTML）
video/music.py       BGM（26秒・120BPM）
video/make_video.py  台本（場面の順番と操作）と書き出し
```

## ライセンス

MIT。社内資料・商談・研修・販売物への組み込みまで自由に使えます。スライドの中の会社名・人名・数字はすべて架空のサンプルです。
