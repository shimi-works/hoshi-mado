# ほしまど ― 空にかざす星座早見

スマホを夜空にかざすと、その方向にある星座と星の名前が見えるWebプラネタリウム。単一HTMLファイルで動作し、オフラインでも骨格が動く（外部CDN・サーバー依存なし）。

## 使い方

`index.html` をブラウザで開くだけ。

- **スマホ**: 「スマホをかざして見る」→ センサーと位置情報を許可 → 空にかざすとその方向の星空が表示される
- **PC**: 「ドラッグで見る」→ マウスドラッグで見回し、ホイールでズーム
- 星や星座線をタップすると名前と解説カードが出る
- ⚙設定: 観測地点（現在地/主要都市）、星座線・星名の表示切替、赤いナイトモード、視野角

※ 方位センサーはHTTPSでのみ動く（GitHub Pages等での公開前提）。`file://` やセンサー非対応環境では自動的にドラッグモードになる。

## 収録データ

- 恒星: 4.5等より明るい約1,000星（＋星座線の構成星）。主要星はカタカナ名つき
- 星座: 全88星座の星座線・和名・一言解説

## 開発

```
# データ再生成（HYG・Stellariumのデータを自動DLし index.html に埋め込む）
python tools/build_data.py

# 天文計算のユニットテスト（skyfield基準値と±1°一致を検証）
node tests/astro.test.mjs
```

天文計算（恒星時・赤道→地平座標変換・透視投影）は `index.html` 内の純関数ブロック（`astro` / `projection`）に分離しており、Nodeから抽出してテストする。

## クレジット / ライセンス

- コード: MIT License
- 星データ: [HYG Database v4.1](https://github.com/astronexus/HYG-Database)（CC BY-SA 4.0）
- 星座線: [Stellarium](https://github.com/Stellarium/stellarium) modern skyculture（CC BY-SA 4.0）
- `index.html` に埋め込まれた星・星座線データは上記由来のため CC BY-SA 4.0 を継承する
