# 動くスライド（ugoku-slide）

押すと根拠が開き、数字を動かすと再計算され、めくると図形が次のページへ変形してつながる、スライドの雛形集です。
雛形は 62 種類。どれも **1ファイルで完結する HTML** で、ダブルクリックするとブラウザで動きます。無料・MIT。

**一覧と見本 → https://aiimpl.github.io/ugoku-slide/**

## 使う

1. 一覧ページで雛形を選び「ダウンロード」を押す（全部入りの zip もある）
2. Claude にファイルを渡し、「Claude用の指示をコピー」で写した文にテーマと数字を書き足して送る
3. 出てきた HTML を開いて確かめ、直したい所は `E` で囲んで指示を作り、Claude に貼る

各ファイルの先頭コメントに、使える部品と書き方が入っています。Claude はそれを読んで、同じ作りのまま中身を書き換えます。

### Claude のスキルとして入れる

`docs/ugoku-slide-skill.zip` を入れると、「動くスライドで〇〇の資料を作って」と頼むだけで、62種から雛形を選んで作り、崩れの点検までします。

- claude.ai・デスクトップアプリ：Settings → Capabilities でコードの実行をオン → Customize → Skills →「＋」→ Upload a skill で zip を選ぶ
- Claude Code：zip を解凍し、`ugoku-slide` フォルダを `~/.claude/skills/` に置く

## 発表するときの操作

| キー | 動き |
|---|---|
| `→` `Space` / `←` | 次へ（順に出す部分があれば先にそちら）／戻る |
| 数字 | そのページへ（`12` と打つと12枚目、`Enter` ですぐ） |
| `F` `O` `N` `P` `B` | 全画面・一覧・発表者メモ・発表者画面（別ウィンドウ）・暗転 |
| `D` | 自動デモ。ページを送り、各ページで操作を1つ見せ、最後に一覧で止まる |
| `E` | 囲んで直す。直したい所をドラッグで囲み、どう直すかを書いて「指示をコピー」 |
| `⌘P` / `Ctrl+P` | PDF に保存（1ページ1枚、根拠は開いた状態） |

ファイル名のあとに `?static` を付けて開くと、動きを止めて、順に出す部分も最初から全部出します（確認や印刷用）。

動作環境は Chrome・Edge・Safari・Firefox の最近の版。外から読むのは Google Fonts だけで、ネットが無くても動きます。

## 直す・足す人へ

### 構成

```
engine/          全雛形に共通の仕組み（engine.js・engine.css）と、各ファイルの先頭に入る説明（guide.txt）
src/decks/       雛形の元。1本が1ファイル（デザインと中身だけ）。作り方は src/DECKS.md
src/index.html   一覧ページの元
skill/           Claude のスキル（SKILL.md・利用者向けの決まり・点検スクリプト）
tools/build.py   engine と src を合わせて docs/ に書き出す。スキルの zip もここで作る
tools/qa.py      全雛形をブラウザで開いて点検する（中身は skill/scripts/check.py と同じ）
tools/morphqa.py ページ送りの途中のコマを並べた画像を作る
video/           紹介動画を作る台本・撮影・BGM
docs/            公開しているサイト（GitHub Pages）。手で直さない
```

### 作り直す・確かめる

```sh
make build    # docs/ を書き出す（Python 3 だけで動く）
make check    # docs/ が src と合っているか、Python の書き方
make serve    # http://localhost:8000 で一覧を見る

pip install -r requirements-dev.txt && playwright install chromium
make qa       # 全雛形の点検。画像は build/qa/<名前>/
python3 tools/qa.py --warn 51           # 1本だけ、「要確認」も表示
python3 tools/morphqa.py 51             # build/morph/51_board.png
```

点検の中身：エラー、枠からのはみ出し（直し方つき）、文字の重なり、文字と背景のコントラスト比、下の空き、
動かない計算、根拠を開いたときと表を貼り替えたときの崩れ、見出しの言い回し、変形のつながり。
結果は「問題」（直す）・「要確認」（画像を見て判断）・「情報」の3段です。

### 雛形を足す

`src/decks/NN-名前.html` を作って `make build`。書き方と決まりは [src/DECKS.md](src/DECKS.md)、使える部品は [engine/guide.txt](engine/guide.txt)。
`make qa` で「問題」が0になるまで直し、画像（`build/qa/NN-名前/sheet.png`）を目で見てから出します。

### 紹介動画

```sh
make video2   # 第2弾（26.5秒）→ build/video/ugoku-slide-vol2_26s.mp4
make video    # 第1弾（26秒）  → build/video/ugoku-slide_26s.mp4
make video3   # 第3弾（25秒）  → build/video/ugoku-slide-vol3_25s.mp4
make clips    # 「囲んで直す」「自動デモ」の短い動画 → build/video/clip_mark.mp4・clip_demo.mp4
```

実際のスライドを開き、台本どおりに操作しながら1コマずつ撮ります。BGM は NumPy で合成し、場面の切り替わりを拍にそろえています。

```
video/make_video2.py  第2弾の台本（場面の順番と操作）
video/make_video3.py  第3弾の台本（囲んで直す・自動デモ・点検）
video/stages3.py      第3弾のスライド以外の場面
video/make_clips.py   操作を見せる短い動画の台本
video/stages2.py      スライド以外の場面（62本の壁・スキルに頼む・締め）
video/music2.py       第2弾の BGM
video/record.py       ページの時計を遅くして撮る
video/fx.js・fx.css   撮影用のテロップとカーソル
```

## ライセンス

MIT。社内資料・商談・研修・販売物への組み込みまで自由に使えます。雛形の中の会社名・人名・数字はすべて架空です。
