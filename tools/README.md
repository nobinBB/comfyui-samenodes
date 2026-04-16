# 外部圧縮ツール配置フォルダ

このフォルダに圧縮ツールのバイナリを配置してください。

## インストール方法

### Windows

以下の各ツールをダウンロードして、このフォルダに `.exe` ファイルを配置してください。

#### 1. pngquant（推奨）
- **ダウンロード:** https://pngquant.org/
- **ファイル名:** `pngquant.exe`
- **効果:** PNG 30-40%削減（視覚品質95%）

#### 2. oxipng（推奨）
- **ダウンロード:** https://github.com/shssoichiro/oxipng/releases
- **ファイル名:** `oxipng.exe`
- **効果:** PNG 5-10%追加削減（ロスレス）

#### 3. cwebp（オプション）
- **ダウンロード:** https://developers.google.com/speed/webp/download
- **ファイル名:** `cwebp.exe`
- **効果:** WebP 20-40%削減（ロスレス）

#### 4. jpegtran（オプション）
- **ダウンロード:** https://jpegclub.org/jpegtran/
- **ファイル名:** `jpegtran.exe`
- **効果:** JPEG 3-15%削減（ロスレス最適化）

---

### Mac / Linux

Homebrewまたはパッケージマネージャでインストール：

```bash
# Mac
brew install pngquant oxipng webp jpeg-turbo

# Linux (Debian/Ubuntu)
sudo apt install pngquant oxipng webp libjpeg-turbo-progs

# Linux (Fedora)
sudo dnf install pngquant oxipng libwebp-tools libjpeg-turbo-utils
```

---

## 配置後のフォルダ構成

```
tools/
├── README.md           # このファイル
├── .gitkeep
├── pngquant.exe        # PNG減色（30-40%削減）
├── oxipng.exe          # PNG最適化（5-10%削減）
├── cwebp.exe           # WebP圧縮（20-40%削減）
└── jpegtran.exe        # JPEG最適化（3-15%削減）
```

---

## 確認方法

ComfyUIのコンソールに以下のように表示されれば成功です：

```
[SDPromptSaverOptimized] PNG (pngquant 85-95): 1,500,000 B → 900,000 B (-40.0%)
[SDPromptSaverOptimized] PNG (oxipng): 900,000 B → 810,000 B (-10.0%)
[SDPromptSaverOptimized] PNG Total (pngquant+oxipng): 1,500,000 B → 810,000 B (-46.0%)
```

---

## 注意事項

- ツールが見つからない場合、Pillowで自動フォールバックします（圧縮率は下がります）
- **推奨:** 最低でも `pngquant` と `oxipng` をインストールしてください
- 管理者権限は不要です
- システムPATHへの追加も不要です
