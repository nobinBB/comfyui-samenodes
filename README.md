# ComfyUI Same Nodes

ComfyUIのワークフローを強化する、文字列変換、バッチ処理、LoRA管理、自動ダウンロードなどのユーティリティを提供するカスタムノード集です。

## 概要

このカスタムノードパックは、ComfyUIユーザーに必須のツールを提供します：

### テキスト処理
- **Float to String**: 小数点以下の桁数を制御できる精密な浮動小数点から文字列への変換
- **Text Split 3**: テキストを3つの出力に分割（`<!...!>` と `<#...#>` デリミタ対応）
- **Repeat Text Lines**: テキストを指定回数繰り返す

### 画像・プロンプト処理
- **Batch Image Processor**: 効率的なバッチ画像処理
- **Batch Image Compressor**: 画像一括圧縮（PNG: 60-80%削減、JPEG最適化）
- **Image Format Converter**: 画像フォーマット一括変換（PNG/JPEG/WebP/BMP/TIFF）
- **Images to PDF**: 複数画像を1つのPDFに変換
- **Extract Prompt from Image**: 画像メタデータからプロンプトを抽出（ComfyUI形式）
- **A1111 Prompt Splitter**: A1111/SD WebUI画像からポジティブ・ネガティブプロンプトを抽出
- **SD Prompt Saver (Optimized)**: A1111互換メタデータ埋め込み + ロスレス圧縮（PNG/WebP/JPEG対応、20-45%削減）

### LoRA管理
- **LoRA Wildcard Generator**: Civitaiメタデータから自動的にYAMLワイルドカードを生成
- **Civitai LoRA Searcher**: SHA256でCivitai APIを検索（JSONフォルダ一括処理）
- **LoRA to Civitai URL**: LoRA構文からCivitai URLを取得

### Embedding管理
- **Embedding Wildcard Generator**: Embeddingファイルから自動的にYAMLワイルドカードを生成
- **Embedding Path Resolver**: `embedding:name` を `embedding:path/name` に自動解決

### ユーティリティ
- **Get ComfyUI Input Path**: ComfyUIの入力ディレクトリパスを取得
- **Seed Step N**: divisorの倍数ごとにseedを進める（永続カウント、独立インスタンス）

これらのノードは、特にLoRAモデル、Embedding、ワイルドカード、プロンプト、バッチ操作、画像処理、パス管理、シード制御を扱う際に、ComfyUIのワークフローを効率化するよう設計されています。

---

## インストール

### ステップ1: リポジトリをクローン

ComfyUIの `custom_nodes` フォルダに移動して、このリポジトリをクローンします：

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/nobinBB/comfyui-samenodes.git
```

### ステップ2: 依存関係をインストール

必要なPythonパッケージをインストールします：

```bash
cd comfyui-samenodes
pip install -r requirements.txt
```

### ステップ3: 環境設定（Civitai Bulk Downloader用）

Civitai Bulk Downloaderノードを使用する場合：

1. 環境テンプレートをコピー：
   ```bash
   cp .env.example .env
   ```

2. `.env` ファイルを編集してCivitai APIキーを追加（詳細は[Civitai Bulk Downloaderのセットアップ](#civitai-bulk-downloaderのセットアップ)を参照）

### ステップ4: ComfyUIを再起動

ComfyUIを再起動して新しいノードを読み込みます。

---

## ノード一覧

### テキスト処理
- **Float to String** - 浮動小数点を文字列に変換（小数点以下桁数制御）
- **Text Split 3** - テキストを3つの出力に分割
- **Repeat Text Lines** - テキストを指定回数繰り返す
- **A1111 Prompt Splitter** - A1111形式の画像からプロンプトを抽出

### 画像処理
- **Batch Image Processor** - バッチ画像処理
- **Batch Image Compressor** - 画像一括圧縮（PNG: 60-80%削減、JPEG最適化）
- **Image Format Converter** - 画像フォーマット一括変換（PNG/JPEG/WebP/BMP/TIFF）
- **Images to PDF** - 複数画像を1つのPDFに変換
- **Extract Prompt from Image** - ComfyUI形式画像からプロンプトを抽出
- **SD Prompt Saver (Optimized)** - A1111互換メタデータ + ロスレス圧縮（PNG/WebP/JPEG、20-45%削減）

### LoRA管理
- **LoRA Wildcard Generator** - CivitaiメタデータからYAMLワイルドカード生成
- **LoRA Text Dual Input** - LoRAテキストの二重入力
- **LoRA Tag Power Loader Extended** - 拡張LoRAタグパワーローダー
- **Civitai LoRA Searcher** - SHA256でCivitai検索（JSONフォルダ一括）
- **LoRA to Civitai URL** - LoRA構文からCivitai URL取得

### Embedding管理
- **Embedding Wildcard Generator** - EmbeddingファイルからYAMLワイルドカード生成
- **Embedding Path Resolver** - `embedding:name` を `embedding:path/name` に自動解決

### ユーティリティ
- **Get ComfyUI Input Path** - ComfyUIの入力ディレクトリパスを取得
- **Seed Step N** - divisorの倍数ごとにseedを進める（永続カウント）

---

## ノードのドキュメント

### 1. Float to String

浮動小数点値を、小数点以下の桁数を設定可能な文字列形式に変換します。

#### 入力

- **value** (FLOAT): 変換する浮動小数点値
- **decimal_places** (INT): 表示する小数点以下の桁数（0-10）
- **use_decimal_places** (BOOLEAN): 小数点以下の桁数フォーマットを適用するかどうか

#### 出力

- **string** (STRING): 変換された文字列値

#### 使用例

| 入力値 | 小数点以下桁数 | 桁数使用 | 出力 |
|--------|--------------|---------|------|
| 3.14159 | 2 | True | "3.14" |
| 3.14159 | 4 | True | "3.1416" |
| 3.14159 | - | False | "3.14159" |
| 42.0 | 0 | True | "42" |

#### ユースケース

- KSamplerのcfg値をファイル名用の文字列に変換
- denoise値を表示用にフォーマット
- ワークフロー内で読みやすいパラメータラベルを作成

---

### 2. Batch Image Processor

様々なバッチ操作で複数の画像を処理します。

#### 説明

ComfyUIワークフロー内でバッチ画像処理タスクを効率的に処理します。

---

### 3. LoRA Wildcard Generator

CivitaiのJSONメタデータファイルから自動的にYAMLワイルドカードファイルを生成し、整理されたLoRAプロンプトテンプレートを作成します。

#### 入力

- **json_folder** (STRING): Civitaiの `.json` メタデータファイルが含まれるフォルダのパス
- **wildcard_name** (STRING): ワイルドカードの名前（ファイル名およびYAMLのトップレベルキーとして使用）
- **output_folder** (STRING): 生成されたYAMLファイルの出力フォルダパス

#### 出力

- **status** (STRING): 生成の詳細を含むステータスメッセージ
- **entry_count** (INT): 生成されたLoRAエントリの数

#### 機能

- ✅ CivitaiのJSONメタデータから `trainedWords` を抽出
- ✅ ウェイトバリエーション付きのLoRA構文を生成：`{0.4|0.5|0.6|0.7|0.8}`
- ✅ ランダムLoRA選択用の `all-<wildcard_name>` エントリを作成
- ✅ ファイル名から `.metadata` サフィックスを自動削除
- ✅ ワイルドカード展開に適したクォートなしYAMLを出力
- ✅ Impact Wildcardsなどの拡張機能と互換性あり

#### 生成されるYAMLフォーマット

```yaml
koma:
  all-koma:
  - >-
    {__2koma_V3__|__3angles_fingering__|__comic_style_cumshot__}
  2koma_V3:
  - <lora:2koma_V3:{0.4|0.5|0.6|0.7|0.8}>{2koma, two views}
  3angles_fingering:
  - <lora:3angles_fingering:{0.4|0.5|0.6|0.7|0.8}>{3angles_fingering, 1girl, lying, cross-section, fingering}
  comic_style_cumshot:
  - <lora:comic_style_cumshot:{0.4|0.5|0.6|0.7|0.8}>{comic, cumshot, cum}
```

#### 使用例

1. CivitaiからLoRAモデルをダウンロード（`.json` メタデータファイルが付属）
2. すべての `.json` ファイルを1つのフォルダに配置（例：`/models/lora/metadata/`）
3. ComfyUIで、LoRA Wildcard Generatorノードを追加
4. パラメータを設定：
   - `json_folder`: `/models/lora/metadata/`
   - `wildcard_name`: `my_loras`
   - `output_folder`: `/wildcards/`
5. ワークフローを実行
6. 生成されるファイル：`/wildcards/my_loras.yaml`

#### プロンプトでのワイルドカード使用

生成後、プロンプトで使用：

- ランダムLoRA：`__my_loras/all-my_loras__`
- 特定のLoRA：`__my_loras/2koma_V3__`

---

### 4. Civitai Bulk Downloader

テキストファイルにリストされたURLを使用して、CivitaiからLoRAモデルをバッチダウンロードします。API認証と自動リトライ機能付き。

#### 入力

- **txt_file_path** (STRING): CivitaiダウンロードURLを含むテキストファイルのパス（1行に1URL）
- **output_file_path** (STRING): ダウンロードしたLoRAファイルの出力ディレクトリ
- **max_retries** (INT): ファイルごとの最大リトライ回数（デフォルト：3、範囲：1-10）

#### 出力

- **status** (STRING): 各ファイルの成功/失敗ログを含む詳細なステータス
- **summary** (STRING): ダウンロード結果のサマリー（例：「成功: 15/20、失敗: 5/20」）

#### 機能

- ✅ テキストファイルからURLを読み込み（1行に1URL）
- ✅ `.env` 設定によるCivitai API認証
- ✅ 指数バックオフによる自動リトライ（2秒、4秒、8秒、16秒...）
- ✅ 大きなファイルの進行状況追跡（10MBごとに更新）
- ✅ 成功と失敗の詳細ログ
- ✅ Content-Dispositionヘッダーから適切なファイル名を抽出
- ✅ スタンドアロン実行（OUTPUT_NODE有効）

---

#### Civitai Bulk Downloaderのセットアップ

**ステップ1: Civitai APIキーを取得**

1. [Civitai](https://civitai.com/)にアクセスしてログイン
2. アカウント設定に移動：
   - プロフィールアイコンをクリック → **Account Settings**
   - または直接アクセス：https://civitai.com/user/account
3. **API Keys** セクションまでスクロール
4. **Add API Key** をクリック（または既存のキーをコピー）
5. 生成されたAPIキーをコピー（形式：`a1b2c3d4e5f6g7h8i9j0...`）

**ステップ2: .envファイルを設定**

1. `comfyui-samenodes` フォルダ内で `.env.example` を見つける

2. コピーして `.env` を作成：
   ```bash
   cp .env.example .env
   ```

3. テキストエディタで `.env` を開く：
   ```bash
   # Windowsの場合
   notepad .env

   # macOSの場合
   open -e .env

   # Linuxの場合
   nano .env
   ```

4. `your_api_key_here` を実際のAPIキーに置き換える：
   ```
   CIVITAI_API_KEY=a1b2c3d4e5f6g7h8i9j0your_actual_key_here
   ```

5. ファイルを保存

**ステップ3: URLリストファイルを作成**

CivitaiダウンロードURLを含むテキストファイル（例：`lora_urls.txt`）を作成：

```
https://civitai.com/api/download/models/1542418
https://civitai.com/api/download/models/1673776
https://civitai.com/api/download/models/1679497
https://civitai.com/api/download/models/1686801
```

**ダウンロードURLの取得方法：**
1. CivitaiのLoRAモデルページにアクセス
2. **Download** ボタンをクリック
3. ダウンロードリンクを右クリックして **リンクのアドレスをコピー** を選択
4. テキストファイルに貼り付け
5. ダウンロードしたいすべてのモデルについて繰り返す

**ステップ4: ComfyUIでノードを使用**

1. ワークフローに **Civitai Bulk Downloader** ノードを追加
2. パラメータを設定：
   - **txt_file_path**: `/path/to/lora_urls.txt`
   - **output_file_path**: `/models/lora/`（またはお好みのLoRAフォルダ）
   - **max_retries**: `3`（または必要に応じて調整）
3. ワークフローを実行（Queue Prompt）

**ステップ5: 進行状況を監視**

コンソール出力で以下を確認：
- ダウンロード進行状況（10MBごとに更新）
- 各ファイルの成功/失敗ステータス
- カウント付きの最終サマリー

#### コンソール出力例

```
============================================================
Civitai Bulk Downloader
============================================================

Reading URLs from: /home/user/lora_urls.txt
Found 4 URLs to download

Output directory: /models/lora/

[1/4] Processing: https://civitai.com/api/download/models/1542418
  Attempt 1/3...
    Progress: 25.0% (50MB / 200MB)
    Progress: 50.0% (100MB / 200MB)
    Progress: 75.0% (150MB / 200MB)
  ✓ Downloaded: awesome_lora_v1.safetensors (200MB)

[2/4] Processing: https://civitai.com/api/download/models/1673776
  Attempt 1/3...
  ✓ Downloaded: cool_style_lora.safetensors (150MB)

...

============================================================
Download Complete!
============================================================
Total: 4 files
Success: 4
Failed: 0
============================================================
```

#### トラブルシューティング

**エラー：「Civitai API key not configured」**
- `.env.example` を `.env` にリネームしたか確認
- `.env` 内で `CIVITAI_API_KEY` が設定されているか確認
- `.env` 編集後にComfyUIを再起動

**エラー：「Text file not found」**
- `txt_file_path` が正しいか確認
- 絶対パスを使用（例：Windowsの場合 `C:/Users/YourName/lora_urls.txt`）

**ダウンロードが繰り返し失敗する場合：**
- インターネット接続を確認
- APIキーが有効か確認
- `max_retries` パラメータを増やす
- 一部のモデルはCivitaiアカウントでNSFWアクセスを有効にする必要がある場合があります

**セキュリティに関する注意：**
- ⚠️ `.env` ファイルをgitにコミットしない（デフォルトで `.gitignore` に含まれています）
- ⚠️ APIキーを公開しない
- ⚠️ APIキーはあなたのCivitaiアカウントへのアクセスを許可します

---

### 5. Extract Prompt from Image

画像メタデータ（PNG info）からポジティブおよびネガティブプロンプトを抽出します。

#### 入力

- **image_path** (STRING): 画像ファイルへのフルパス（例：`/path/to/image.png`）

#### 出力

- **positive** (STRING): 抽出されたポジティブプロンプト
- **negative** (STRING): 抽出されたネガティブプロンプト

#### 機能

- ✅ ComfyUI形式の画像をサポート
- ✅ Automatic1111/SD WebUI形式の画像をサポート
- ✅ メタデータフォーマットを自動検出
- ✅ ポジティブとネガティブの両プロンプトを抽出
- ✅ コンソールに抽出されたプロンプトのプレビューを表示
- ✅ メタデータが見つからない場合は空文字列を返す

#### サポートされる画像形式

**ComfyUI形式：**
- ComfyUIで生成された画像には `prompt` メタデータキーが含まれる
- JSON形式でワークフローとノード情報を含む
- CLIPTextEncodeノードから抽出

**Automatic1111形式：**
- SD WebUI/Automatic1111で生成された画像
- `parameters` メタデータキーを含む
- フォーマット：`positive\nNegative prompt: negative\nSteps: ...`

#### 使用例

1. **Extract Prompt from Image** ノードをワークフローに追加
2. `image_path` 入力に画像ファイルの **フルパス** を入力
   - 例：`C:/Users/YourName/Pictures/output.png`（Windows）
   - 例：`/home/user/images/output.png`（Linux/Mac）
3. **実行** してプロンプトを抽出
4. **出力を接続** してShow Textなど他のノードでプロンプトを表示/使用

**ワークフロー例：**
```
[Extract Prompt from Image]
    image_path: "/path/to/your/image.png"
         ↓ positive
    [Show Text]
         ↓ negative
    [Show Text]
```

**なぜ直接ファイルパスなのか？**
- ComfyUIのLoad Imageノードは画像をテンソルに変換し、メタデータが失われます
- ファイルから直接読み込むことでプロンプトを含むPNG infoチャンクが保持されます

#### ユースケース

- **プロンプト分析**: 生成された画像から成功したプロンプトを研究
- **プロンプト再利用**: お気に入りの画像からプロンプトを抽出して再利用
- **ワークフロー再作成**: 出力画像からワークフローを再構築
- **プロンプトライブラリ**: 効果的なプロンプトのライブラリを構築
- **A/Bテスト**: 異なる画像のプロンプトを比較

#### コンソール出力例

```
============================================================
Extracting Prompt from Image
============================================================

Found metadata keys: ['prompt', 'workflow']
Detected ComfyUI format

============================================================
Extraction Complete
============================================================
Positive prompt length: 523 characters
Negative prompt length: 187 characters
============================================================

Positive preview: 1girl, female assassin (fate/zero), fate (series)
BREAK
official style,
BREAK
(Simple white background:1.4),
BREAK
<lora:Illustrious\必須\detailed hand focus style illustriousXL v1.1>
BREAK
sitting on the floor with her back arched, hands resting...

Negative preview: (multiple girls:1.4),(speech bubble:1.1),poorly drawn hands, poorly drawn feet,ugly, bad feet, bad hands, bad art, ugly artstyle, (bad anatomy:1.1), bad fingers...
```

#### 制限事項

- メタデータを含むPNG画像でのみ動作
- JPEG画像はメタデータを保持しない
- 一部の画像編集ツールはメタデータを削除する場合があります
- プロンプトが見つからない場合、空文字列を返します

---

### 6. A1111 Prompt Splitter (Pos/Neg)

Automatic1111/SD WebUI形式の画像メタデータからポジティブ・ネガティブプロンプトをバッチ処理で抽出します。

#### 入力

- **file_path** (STRING, forceInput): PNG画像ファイルのパス（複数可、リスト対応）
- **debug** (BOOLEAN, optional): デバッグログを有効化（デフォルト：False）

#### 出力

- **positive_prompt_per_image** (STRING list): 各画像のポジティブプロンプトリスト
- **negative_prompt_per_image** (STRING list): 各画像のネガティブプロンプトリスト

#### 機能

- ✅ **バッチ処理対応**: 複数画像を一度に処理
- ✅ **A1111形式サポート**: `parameters` メタデータから自動抽出
- ✅ **入力の柔軟性**: リスト、改行区切り文字列など様々な形式に対応
- ✅ **自動パース**: "Negative prompt:" ラベルを自動検出
- ✅ **設定情報の除去**: Steps、Sampler等の設定行を自動削除
- ✅ **エラーハンドリング**: 存在しないファイルやメタデータなしの画像は空文字列を返す

#### 使用例

```
[String Input] → file_path
    "/path/to/image1.png
     /path/to/image2.png
     /path/to/image3.png"
         ↓
[A1111 Prompt Splitter]
         ↓ positive_prompt_per_image
    ["positive1", "positive2", "positive3"]
         ↓ negative_prompt_per_image
    ["negative1", "negative2", "negative3"]
```

#### サポートされるメタデータ形式

**A1111 parameters形式:**
```
1girl, masterpiece, best quality
Negative prompt: bad hands, ugly
Steps: 20, Sampler: DPM++ 2M, CFG scale: 7
```

---

### 7. Embedding Wildcard Generator

Embeddingファイルから自動的にYAMLワイルドカードファイルを生成します。

#### 入力

- **embedding_folder** (STRING): Embeddingファイルが含まれるフォルダのパス
- **wildcard_name** (STRING): ワイルドカードの名前（ファイル名およびYAMLのトップレベルキーとして使用）
- **output_folder** (STRING): 生成されたYAMLファイルの出力フォルダパス

#### 出力

- **status** (STRING): 生成の詳細を含むステータスメッセージ
- **entry_count** (INT): 生成されたEmbeddingエントリの数

#### 機能

- ✅ サポート拡張子: `.pt`, `.safetensors`, `.bin`, `.ckpt`, `.pth`
- ✅ `embedding:name` 構文を自動生成
- ✅ ランダムEmbedding選択用の `all-<wildcard_name>` エントリを作成
- ✅ ワイルドカード展開に適したYAMLフォーマットを出力
- ✅ アルファベット順にソート

#### 生成されるYAMLフォーマット

```yaml
my_embeddings:
  all-my_embeddings:
  - >-
    {__BadDream__|__UnrealisticDream__|__easynegative__}
  BadDream:
  - >-
    embedding:BadDream
  UnrealisticDream:
  - >-
    embedding:UnrealisticDream
  easynegative:
  - >-
    embedding:easynegative
```

#### 使用例

1. Embeddingファイルをフォルダに配置（例：`/models/embeddings/`）
2. ComfyUIで **Embedding Wildcard Generator** ノードを追加
3. パラメータを設定：
   - `embedding_folder`: `/models/embeddings/`
   - `wildcard_name`: `my_embeddings`
   - `output_folder`: `/wildcards/`
4. ワークフローを実行
5. 生成されるファイル：`/wildcards/my_embeddings.yaml`

#### プロンプトでのワイルドカード使用

- ランダムEmbedding：`__my_embeddings/all-my_embeddings__`
- 特定のEmbedding：`__my_embeddings/BadDream__`

---

### 8. Embedding Path Resolver

`embedding:name` を `embedding:subpath/name` に自動解決します。サブフォルダ構造を持つEmbeddingを簡単に使用できます。

#### 入力

- **text** (STRING, multiline): `embedding:name` パターンを含むテキスト

#### 出力

- **text** (STRING): パスが解決されたテキスト

#### 機能

- ✅ **再帰的スキャン**: `models/embeddings` フォルダを再帰的に検索
- ✅ **自動パス解決**: `embedding:name` → `embedding:subpath/name` に変換
- ✅ **拡張子除去**: 出力パスに拡張子を含めない
- ✅ **キャッシング**: フォルダスキャン結果をキャッシュして高速化
- ✅ **ComfyUI統合**: `folder_paths` モジュールを使用してEmbeddingフォルダを自動検出
- ✅ **複数フォルダ対応**: `extra_model_paths.yaml` で設定された追加フォルダもスキャン

#### 処理例

**フォルダ構造:**
```
models/embeddings/
  ├── BadDream.pt
  └── illustrious/
      └── NSFW/
          └── masturbation/
              └── FFF_imminent_masturbation.safetensors
```

**入力テキスト:**
```
1girl, embedding:FFF_imminent_masturbation, masterpiece
```

**出力テキスト:**
```
1girl, embedding:illustrious/NSFW/masturbation/FFF_imminent_masturbation, masterpiece
```

#### 使用例

```
[Text Input]
    "1girl, embedding:BadDream, embedding:FFF_imminent_masturbation"
         ↓
[Embedding Path Resolver]
         ↓
    "1girl, embedding:BadDream, embedding:illustrious/NSFW/masturbation/FFF_imminent_masturbation"
         ↓
[CLIP Text Encode]
```

#### ユースケース

- **複雑なフォルダ構造の簡略化**: サブフォルダのパスを入力する手間を省略
- **ワイルドカードとの連携**: `__embeddings/all-embeddings__` から展開された名前を自動解決
- **プロンプト共有**: 環境依存のパスを気にせず名前だけで共有可能

---

### 9. Text Split 3

テキストを3つの出力に分割します。`<!...!>` と `<#...#>` デリミタを使用してテキストを抽出します。

#### 入力

- **text** (STRING, multiline): 分割するテキスト

#### 出力

- **text_1** (STRING): デリミタを除いた残りのテキスト
- **text_2** (STRING): `<!...!>` で囲まれたテキスト（複数ある場合は結合、末尾にカンマ追加）
- **text_3** (STRING): `<#...#>` で囲まれたテキスト（複数ある場合は結合、末尾にカンマ追加）

#### 機能

- ✅ **複数マーカー対応**: 同じデリミタの複数箇所を自動抽出
- ✅ **自動結合**: 抽出されたテキストをスペース区切りで結合
- ✅ **カンマ追加**: text_2とtext_3が空でない場合、末尾にカンマを追加
- ✅ **クリーンアップ**: 元テキストから抽出部分を削除し、空白を整理

#### 処理例

**入力:**
```
positive prompt <!negative1!> more text <!negative2!> <#extra info#>
```

**出力:**
- **text_1**: `"positive prompt more text"`
- **text_2**: `"negative1 negative2,"`
- **text_3**: `"extra info,"`

#### 使用例

```
[Text Input]
    "1girl, masterpiece <!bad hands, ugly!> <#lora:style:0.8#>"
         ↓
[Text Split 3]
    ├─ text_1: "1girl, masterpiece"
    ├─ text_2: "bad hands, ugly,"
    └─ text_3: "lora:style:0.8,"
         ↓
[CLIP Text Encode (Positive)] ← text_1
[CLIP Text Encode (Negative)] ← text_2
[Extra Processing] ← text_3
```

#### ユースケース

- **プロンプト分離**: 1つのテキストからポジティブ・ネガティブ・その他を分離
- **ワークフロー簡略化**: 複数のテキスト入力ノードを1つにまとめる
- **条件分岐**: 特定のマーカーで囲んだテキストを別処理に回す

---

### 10. Repeat Text Lines

テキストを指定回数繰り返します。シンプルなテキスト繰り返しノードです。

#### 入力

- **text** (STRING, multiline): 繰り返すテキスト
- **count** (INT): 繰り返し回数（範囲：1-999、デフォルト：5）

#### 出力

- **text** (STRING): 改行区切りで繰り返されたテキスト

#### 機能

- ✅ **シンプル**: テキストを指定回数改行区切りで繰り返す
- ✅ **エラーハンドリング**: 無効な入力に対してエラーメッセージを返す

#### 処理例

**入力:**
- text: `"1girl, masterpiece"`
- count: `3`

**出力:**
```
1girl, masterpiece
1girl, masterpiece
1girl, masterpiece
```

#### 使用例

```
[Text Input] → "lora:style:0.7"
[Repeat Text Lines] (count=5)
         ↓
    "lora:style:0.7
     lora:style:0.7
     lora:style:0.7
     lora:style:0.7
     lora:style:0.7"
```

---

### 11. Get ComfyUI Input Path

ComfyUIの入力ディレクトリパスを取得します。画像やファイルの入力パスを動的に取得する際に便利です。

#### 入力

- なし（入力パラメータ不要）

#### 出力

- **input_path** (STRING): ComfyUIの入力ディレクトリの絶対パス

#### 機能

- ✅ **自動パス取得**: ComfyUIの`folder_paths`モジュールから入力ディレクトリを自動取得
- ✅ **設定不要**: パラメータ入力なしで即座に使用可能
- ✅ **クロスプラットフォーム**: Windows/Linux/Mac環境で動作

#### 使用例

```
[Get ComfyUI Input Path]
         ↓ input_path
    "/path/to/ComfyUI/input"
         ↓
[String Concatenate] + "/myimage.png"
         ↓
    "/path/to/ComfyUI/input/myimage.png"
         ↓
[Load Image] or [Other Nodes]
```

#### ユースケース

- **動的パス生成**: 環境に依存しない動的なファイルパス構築
- **ファイル操作**: 入力ディレクトリ内のファイルを自動検索・処理
- **ポータブルワークフロー**: 異なる環境でも動作するワークフロー作成
- **バッチ処理**: 入力フォルダ内の複数ファイルを処理

#### 出力例

**Windows:**
```
C:\ComfyUI\input
```

**Linux/Mac:**
```
/home/user/ComfyUI/input
```

---

### 11. Batch Image Compressor

フォルダ内の画像を一括圧縮します。PNG/JPEG形式のまま、ファイルサイズを大幅に削減します。

#### 入力

- **input_folder** (STRING): 入力フォルダ（サブフォルダ含む）
- **output_folder** (STRING): 出力フォルダ
- **png_mode** (選択): PNG圧縮モード
  - **Lossless**: ロスレス圧縮（20-40%削減）
  - **Quantize (60-80% reduction)**: 量子化（60-80%削減、256色）
- **jpeg_quality** (INT): JPEG品質（1-100、デフォルト: 85）

#### 出力

- **status** (STRING): 各ファイルの圧縮結果
- **summary** (STRING): 全体統計（削減率、処理数）

#### 機能

- ✅ **PNG Quantize**: 60-80% 削減（256色に減色）
- ✅ **PNG Lossless**: 20-40% 削減（最適化のみ）
- ✅ **JPEG最適化**: 品質調整可能
- ✅ **サブフォルダ対応**: フォルダ構造を保持
- ✅ **詳細統計**: 各ファイルと全体の削減率を表示

#### 使用例

```
入力フォルダ: C:/images/
出力フォルダ: C:/images_compressed/
PNG mode: Quantize (60-80% reduction)
JPEG quality: 85

結果:
[1/100] image1.png: 5.23 MB → 1.15 MB (78.0% reduced)
[2/100] image2.jpg: 2.45 MB → 1.89 MB (22.9% reduced)
...
Total reduction: 65.3%
```

---

### 12. Images to PDF

複数の画像を1つのPDFファイルに変換します。

#### 入力

- **input_folder** (STRING): 入力フォルダ
- **output_folder** (STRING): 出力フォルダ
- **include_subfolders** (BOOLEAN): サブフォルダも含める
- **sort_by_filename** (BOOLEAN): ファイル名順にソート（デフォルト: True）
- **quality** (選択): 画質設定
  - **高画質(大きい)**: 高品質（quality: 95）
  - **標準**: 標準品質（quality: 85）
  - **低画質(小さい)**: 低品質（quality: 75）

#### 出力

- **status** (STRING): 処理結果（ページ数、ファイルサイズ）
- **pdf_path** (STRING): 生成されたPDFのフルパス

#### 機能

- ✅ **複数画像を1つのPDFに結合**
- ✅ **サブフォルダ対応**（オプション）
- ✅ **ファイル名順に自動ソート**
- ✅ **画質設定**（高/標準/低）
- ✅ **タイムスタンプ付きファイル名**（`images_20250409_123456.pdf`）
- ✅ **PNG, JPEG, BMP, TIFF, WebP 対応**
- ✅ **RGBA → RGB 自動変換**

#### 使用例

```
入力フォルダ: C:/manga/chapter1/
出力フォルダ: C:/output/
Include subfolders: False
Sort by filename: True
Quality: 高画質(大きい)

結果:
✓ PDF created successfully
Pages: 25
File size: 12.45 MB
Output: images_20250409_143022.pdf
```

---

### 13. Civitai LoRA Searcher

JSONメタデータフォルダからSHA256を読み込み、Civitai APIでLoRAモデルを一括検索します。

#### 入力

- **json_folder** (STRING): JSONメタデータフォルダのパス

#### 出力

- **civitai_urls** (STRING): Civitai.comで見つかったURL一覧（改行区切り）
- **archive_urls** (STRING): Archive フォールバックURL一覧（改行区切り）
- **info** (STRING): 詳細なモデル情報（JSON形式）
- **status** (STRING): 各LoRAの検索結果サマリー

#### 機能

- ✅ **JSONフォルダ一括処理**: サブフォルダを再帰的に検索
- ✅ **Civitai API検索**: SHA256ハッシュでモデルを検索
- ✅ **Archive フォールバック**: 見つからない場合はCivitAI Archive URL
- ✅ **詳細ログ**: 各LoRAの検索結果を表示
- ✅ **API認証**: `.env` ファイルからAPIキー読み込み（オプション）

#### 使用例

```
JSON folder: C:/lora_metadata/

結果:
[1/36] anal_licking
  ✓ Found: https://civitai.com/models/1179259?modelVersionId=1327045
[2/36] bondage_blowjob
  △ Not found on Civitai → Archive: https://civarchive.com/sha256/abc123...

Found on Civitai: 24
Archive Fallback: 12
```

---

### 14. LoRA to Civitai URL

LoRA構文（`<lora:name:weight>`）を解析し、Civitai URLを取得します。

#### 入力

- **lora_syntax** (STRING): LoRA構文（例：`<lora:anal_licking:0.8>`）
- **json_folder** (STRING): JSONメタデータフォルダ
- **lora_folder** (STRING, optional): LoRAファイルフォルダ（SHA256計算用）

#### 出力

- **civitai_url** (STRING): Civitai.comで見つかったURL（改行区切り）
- **archive_url** (STRING): Archive フォールバックURL または エラーメッセージ

#### 機能

- ✅ **LoRA構文解析**: `<lora:name:weight>` から名前を抽出
- ✅ **SHA256取得**: JSONまたはLoRAファイルから取得
- ✅ **サブフォルダ探索**: JSONとLoRAフォルダを再帰的に検索
- ✅ **Civitai API検索**: SHA256でモデルを検索
- ✅ **Archive フォールバック**: 見つからない場合はArchive URL
- ✅ **API認証**: `.env` ファイルからAPIキー読み込み

#### 使用例

```
LoRA syntax:
<lora:anal_licking:0.8>
<lora:bondage_blowjob:0.7>

JSON folder: C:/lora_metadata/

結果:
Processing: anal_licking
  ✓ Matched: anal_licking.json → SHA256: 9eb9c1a7...
  ✓ Found: https://civitai.com/models/1179259?modelVersionId=1327045

Processing: bondage_blowjob
  ✓ Matched: bondage_blowjob.json → SHA256: abc123...
  △ Archive Fallback: https://civarchive.com/sha256/abc123...
```

---

### 15. Image Format Converter

画像ファイルの拡張子を別の拡張子に一括変換します。同じ拡張子への変換はエラーになります。

#### 入力

- **input_folder** (STRING): 入力フォルダ
- **output_folder** (STRING): 出力フォルダ
- **source_extension** (選択): 元の拡張子
  - `.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`, `.tiff`
- **target_extension** (選択): 変換先の拡張子
  - `.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`, `.tiff`
- **quality** (INT, optional): JPEG/WebP品質（1-100、デフォルト: 85）
- **include_subfolders** (BOOLEAN, optional): サブフォルダも含める

#### 出力

- **status** (STRING): 各ファイルの変換結果
- **file_count** (INT): 変換したファイル数

#### 機能

- ✅ **同じ拡張子チェック**: 元と変換先が同じ場合はエラー
- ✅ **サブフォルダ対応**: フォルダ構造を保持
- ✅ **品質設定**: JPEG/WebP品質調整可能
- ✅ **自動RGB変換**: RGBA → RGB（JPEG/BMP用）
- ✅ **最適化**: PNG圧縮、JPEG最適化

#### エラー例

```
source_extension: .png
target_extension: .png

結果:
✗ Error: Source and target extensions are the same (.png). 
   Cannot convert to the same format.
```

#### 使用例

```
入力フォルダ: C:/images/
出力フォルダ: C:/images_converted/
source_extension: .png
target_extension: .jpg
quality: 85
include_subfolders: False

結果:
[1/50] image1.png → image1.jpg (+15.2%)
[2/50] image2.png → image2.jpg (-22.3%)
[3/50] image3.png → image3.jpg (-18.7%)
...
Converted: 50/50 files (.png → .jpg)
```

---

### 16. Seed Step N

divisorの倍数ごとにseedを進めるノード。各ノードインスタンスごとに独立したカウントを保持し、ComfyUI再起動後も継続します。

#### 入力

- **base_seed** (INT): 基準seed（0 〜 0xffffffffffffffff）
- **divisor** (INT): 何回の実行ごとにseedを+1するか（1以上）
  - 1: 毎回+1
  - 4: 4回ごとに+1
- **increment_amount** (INT): seedを進める量（デフォルト: 1）

#### 出力

- **seed** (INT): `base_seed + (count // divisor) * increment_amount`

#### 機能

- ✅ **永続カウント**: JSONファイルに保存、ComfyUI再起動後も継続
- ✅ **独立インスタンス**: 同じワークフロー内の複数ノードは独立してカウント
- ✅ **リアルタイム表示**: 現在のカウントと次のseedを表示
- ✅ **リセットボタン**: ノード単位でカウントをリセット可能
- ✅ **キャッシュバイパス**: 毎回確実に実行（IS_CHANGEDでNaN返却）

#### UI表示

- **Count**: 現在の実行回数
- **Next seed**: 次回出力予定のseed値
- **Reset Counter**: カウントを0にリセット

#### 計算例

divisor=4, base_seed=1000, increment_amount=1 の場合：

| 実行回数 (count) | 出力 seed | 備考 |
|-----------------|----------|------|
| 0 | 1000 | 1枚目 |
| 1 | 1000 | 2枚目 |
| 2 | 1000 | 3枚目 |
| 3 | 1000 | 4枚目 |
| 4 | 1001 | 5枚目（seed進む） |
| 5 | 1001 | 6枚目 |
| 6 | 1001 | 7枚目 |
| 7 | 1001 | 8枚目 |
| 8 | 1002 | 9枚目（seed進む） |

#### 使用例

```
同じLoRAで4枚ずつ生成し、5枚目でseedを変えたい場合:

base_seed: 1000
divisor: 4
increment_amount: 1

結果:
1〜4枚目: seed 1000
5〜8枚目: seed 1001
9〜12枚目: seed 1002
...
```

#### 独立カウントの保証

- カウントは `unique_id` をキーに管理
- 同じワークフローに2つ配置しても別々にカウント
- カウンターファイル: `ComfyUI/custom_nodes/comfyui-samenodes/seed_step_counters.json`

---

### 17. SD Prompt Saver (Optimized)

A1111互換メタデータを埋め込み、ロスレス圧縮して保存するノード。
PNG/WebP/JPEG全フォーマット対応。`receyuki/comfyui-prompt-reader-node` の `SDPromptSaver` をベースに拡張。

#### 入力

**フォーマット:**
- **extension** (COMBO): 保存形式（`png` / `webp` / `jpg` / `jpeg`、デフォルト: `png`）

**ファイル名・パス設定:**
- **filename** (STRING): ファイル名テンプレート（デフォルト: `ComfyUI_%time_%seed_%counter`）
- **path** (STRING): 保存先パステンプレート（デフォルト: `%date/`）
  - 相対パス: `ComfyUI/output/` からの相対パス
  - 絶対パス: そのまま使用（例: `D:/MyImages/`）
- **date_format** (STRING): `%date` のフォーマット（デフォルト: `%Y-%m-%d`）
- **time_format** (STRING): `%time` のフォーマット（デフォルト: `%H%M%S`）

**生成パラメータ:**
- **model_name** (STRING): モデル名
- **vae_name** (STRING): VAE名
- **seed** (INT): シード値
- **steps** (INT): ステップ数
- **cfg** (FLOAT): CFGスケール
- **sampler_name** (STRING): サンプラー名
- **scheduler** (STRING): スケジューラー名
- **width** / **height** (INT): 画像サイズ
- **positive** (STRING): ポジティブプロンプト
- **negative** (STRING): ネガティブプロンプト
- **lora_name** (STRING): LoRA名

**ハッシュ・メタデータ:**
- **calculate_hash** (BOOLEAN): モデルハッシュ計算（デフォルト: True）
- **resource_hash** (BOOLEAN): LoRAハッシュ計算（デフォルト: True）
- **save_metadata_file** (BOOLEAN): メタデータをTXTファイルにも保存（デフォルト: False）

**圧縮最適化:**
- **jpeg_quality** (INT): JPEG品質（60〜100、デフォルト: 95）
  - 95: 高品質・推奨
  - 85-90: バランス
  - 60-80: 低品質（非推奨）
- **preserve_metadata** (BOOLEAN): メタデータ保持（デフォルト: True、推奨）
  - True: A1111形式メタデータとComfyUIワークフローを保持
  - False: メタデータ削除（SD Prompt Readerで読めなくなる）
- **show_compression_log** (BOOLEAN): 圧縮率ログ出力（デフォルト: True）

#### 出力

- **FILENAME** (STRING): 保存したファイル名
- **FILE_PATH** (STRING): 保存したフルパス
- **METADATA** (STRING): 埋め込んだA1111形式メタデータ文字列

#### フォーマット別の圧縮方式

**ハイブリッド圧縮: 外部ツール優先 → Pillowフォールバック**

| フォーマット | 外部ツール | Pillowフォールバック | 圧縮率（外部） | 圧縮率（Pillow） |
|-------------|-----------|-------------------|--------------|----------------|
| PNG | **pngquant 85-95 + oxipng** | compress_level=9 | **35-50%** | 10-25% |
| WebP | cwebp -lossless | lossless mode | 20-40% | 5-20% |
| JPEG | jpegtran | optimize + progressive | 3-15% | 5-15% |

**PNG圧縮の詳細:**
- **pngquant (quality 85-95)**: 視覚的にほぼ劣化なし（品質95%）、30-40%削減
- **oxipng (-o 6)**: 完全ロスレス追加最適化、さらに5-10%削減
- **合計**: 35-50%削減、視覚品質95%維持

**WebP/JPEG:**
- 完全ロスレス（画素データ変更なし）
- 外部ツールが無くても**必ず圧縮される**（Pillowで自動フォールバック）
- ツールのインストールはオプション（推奨だが必須ではない）

#### ファイル名テンプレート

使用可能なプレースホルダ:
- `%date` → date_formatでフォーマット（例: `2026-04-15`）
- `%time` → time_formatでフォーマット（例: `153022`）
- `%seed` → seed値（例: `1234567`）
- `%counter` → 連番（5桁ゼロパディング、例: `00001`）
- `%model` → モデル名（拡張子なし）
- `%sampler` → サンプラー名
- `%scheduler` → スケジューラー名
- `%steps` → ステップ数
- `%cfg` → CFG値
- `%width` / `%height` → 画像サイズ

#### A1111形式メタデータ

- PNG: `tEXt` チャンクに `parameters` キーで埋め込み
- WebP/JPEG: EXIFのUserCommentに埋め込み（piexifが必要: `pip install piexif`）
- SD Prompt Reader、Civitai、A1111 WebUIで読み取り可能
- ComfyUIの `prompt` と `workflow` も同時埋め込み（PNG限定、ドラッグ&ドロップ復元対応）

#### ハイブリッド圧縮（外部ツール + Pillowフォールバック）

本ノードは**外部ツールがあれば高圧縮、なくてもPillowで動作**します。

| フォーマット | 外部ツール（高圧縮） | Pillowフォールバック | 圧縮率 |
|-------------|-------------------|-------------------|--------|
| PNG | **pngquant 85-95 + oxipng** | compress_level=9 | **35-50%** → 10-25% |
| WebP | cwebp -lossless | lossless mode | 20-40% → 5-20% |
| JPEG | jpegtran | optimize + progressive | 3-15% → 5-15% |

**PNGの2段階圧縮:**
1. pngquant (quality 85-95): 視覚的にほぼ劣化なし、30-40%削減
2. oxipng (-o 6): ロスレス追加最適化、さらに5-10%削減
3. **合計: 35-50%削減、視覚品質95%維持**

**外部ツールは必須ではありません。** インストールしなくても動作しますが、圧縮率が向上します。

---

#### 外部ツールのインストール方法（オプション）

**本ノードは `tools` フォルダからツールを優先的に読み込みます。**

##### **インストール方法（推奨）**

1. **ツールフォルダを作成:**
   ```
   ComfyUI/custom_nodes/comfyui-samenodes/tools/
   ```

2. **各ツールのバイナリを配置:**
   - Windows: `.exe` ファイル
   - Linux/Mac: 実行可能ファイル

3. **フォルダ構成:**
   ```
   comfyui-samenodes/
   ├── tools/
   │   ├── pngquant.exe    # Windows
   │   ├── oxipng.exe      # Windows
   │   ├── cwebp.exe       # Windows
   │   └── jpegtran.exe    # Windows
   ├── sd_prompt_saver_optimized.py
   └── ...
   ```

**ツールが `tools` フォルダに無い場合、システムPATHから実行を試みます。**

---

##### **必須: piexif（JPEG/WebPメタデータ用）**
```bash
pip install piexif
# または
pip install -r requirements.txt
```

##### **オプション: pngquant + oxipng（PNG圧縮、35-50%削減）**

**pngquantとoxipngの両方をインストールすると最高の圧縮率になります。**

**pngquant（PNG減色、30-40%削減、視覚品質95%）:**

**Windows:**
1. https://pngquant.org/ から最新版をダウンロード
2. `pngquant-windows.zip` を解凍
3. `pngquant.exe` を `ComfyUI/custom_nodes/comfyui-samenodes/tools/` に配置（推奨）
   - または環境変数PATHに追加

**Mac:**
```bash
brew install pngquant
```

**Linux:**
```bash
# Debian/Ubuntu
sudo apt install pngquant

# Fedora
sudo dnf install pngquant
```

---

**oxipng（PNG追加最適化、5-10%追加削減）:**

**Windows:**
1. https://github.com/shssoichiro/oxipng/releases から最新版をダウンロード
2. `oxipng-vX.X.X-x86_64-pc-windows-msvc.zip` を解凍
3. `oxipng.exe` を `ComfyUI/custom_nodes/comfyui-samenodes/tools/` に配置（推奨）
   - または環境変数PATHに追加

**Mac:**
```bash
brew install oxipng
```

**Linux:**
```bash
# Debian/Ubuntu
sudo apt install oxipng

# Fedora
sudo dnf install oxipng

# またはcargoでビルド
cargo install oxipng
```

##### **オプション: cwebp（WebP圧縮、20-40%削減）**

**Windows:**
1. https://developers.google.com/speed/webp/download から最新版をダウンロード
2. `libwebp-X.X.X-windows-x64.zip` を解凍
3. `bin\cwebp.exe` を `ComfyUI/custom_nodes/comfyui-samenodes/tools/` に配置（推奨）
   - または環境変数PATHに追加

**Mac:**
```bash
brew install webp
```

**Linux:**
```bash
# Debian/Ubuntu
sudo apt install webp

# Fedora
sudo dnf install libwebp-tools
```

##### **オプション: jpegtran（JPEG圧縮、3-15%削減）**

**Windows:**
1. https://jpegclub.org/jpegtran/ からダウンロード
   - または https://sourceforge.net/projects/libjpeg-turbo/ から最新版をダウンロード
2. `jpegtran.exe` を `ComfyUI/custom_nodes/comfyui-samenodes/tools/` に配置（推奨）
   - または環境変数PATHに追加

**Mac:**
```bash
brew install jpeg-turbo
```

**Linux:**
```bash
# Debian/Ubuntu
sudo apt install libjpeg-turbo-progs

# Fedora
sudo dnf install libjpeg-turbo-utils
```

---

#### インストール確認

```bash
# 各ツールが正しくインストールされているか確認
pngquant --version  # PNG用（推奨）
oxipng --version    # PNG用（推奨）
cwebp -version      # WebP用
jpegtran -v 2>&1 | head -1  # JPEG用
```

**推奨: pngquant + oxipng の両方をインストール**すると、PNG圧縮率が最大35-50%になります。

ツールが見つからない場合でもノードは動作します（Pillowフォールバック）。

#### 圧縮率の目安

AI生成画像での圧縮率（実測値）:

| フォーマット | 外部ツール使用時 | Pillowのみ使用時 |
|-------------|----------------|----------------|
| PNG | **35-50%** (pngquant 85-95 + oxipng) | 10-25% (compress_level=9) |
| WebP | 20-40% (cwebp lossless) | 5-20% (lossless mode) |
| JPEG | 3-15% (jpegtran) | 5-15% (optimize + progressive) |

**外部ツールがある場合の例（PNG → pngquant + oxipng）:**
```
[SDPromptSaverOptimized] saved: D:/output/2026-04-15/ComfyUI_153022_1234567_0001.png
[SDPromptSaverOptimized] PNG (pngquant 85-95): 2,453,120 B → 1,471,872 B (-40.0%)
[SDPromptSaverOptimized] PNG (oxipng): 1,471,872 B → 1,324,685 B (-10.0%)
[SDPromptSaverOptimized] PNG Total (pngquant+oxipng): 2,453,120 B → 1,324,685 B (-46.0%)
============================================================
```

**外部ツールがない場合の例（PNG → Pillow）:**
```
[SDPromptSaverOptimized] saved: D:/output/2026-04-15/ComfyUI_153022_1234567_0001.png
[SDPromptSaverOptimized] PNG (Pillow): 2,453,120 B → 2,103,552 B (-14.2%)
```

#### 使用例

```
ワークフロー例:
1. KSamplerでpositive/negativeプロンプトを使用
2. 生成した画像をSD Prompt Saver (Optimized)に接続
3. パラメータ設定:
   - extension: png (または webp / jpg)
   - filename: "MyArt_%date_%time_%seed"
   - path: "renders/%model/"
   - jpeg_quality: 95 (JPEGの場合)
   - preserve_metadata: True (推奨)
   - show_compression_log: True
4. 実行すると:
   - ファイル保存 + メタデータ埋め込み
   - 自動で圧縮実行（外部ツール → Pillowフォールバック）
   - コンソールに圧縮率とツール名表示
```

#### 注意点

- `preserve_metadata=True` を推奨（FalseだとA1111メタデータも削除される）
- **外部ツールは必須ではない**: インストールしなくても動作（Pillowで自動圧縮）
- **外部ツール推奨**: インストールすると圧縮率が大幅向上（PNG: 20-45%、WebP: 20-40%）
- piexif必須: `pip install piexif` でインストール（JPEG/WebPメタデータ用）
- バッチ画像対応（B次元を1枚ずつ処理、counterは自動インクリメント）
- ファイル名の重複は自動回避（counter自動調整）

#### ライセンス

本ノードは [receyuki/comfyui-prompt-reader-node](https://github.com/receyuki/comfyui-prompt-reader-node) (MIT License) をベースに作成されています。

---

## プロジェクト構造

```
comfyui-samenodes/
├── __init__.py                      # ノードの初期化と登録
├── float_to_string.py               # Float to Stringノードの実装
├── batch_processor.py               # Batch Image Processorノードの実装
├── batch_image_compressor.py        # Batch Image Compressorノードの実装
├── image_format_converter.py        # Image Format Converterノードの実装
├── images_to_pdf.py                 # Images to PDFノードの実装
├── lora_wildcard_generator.py       # LoRA Wildcard Generatorノードの実装
├── lora_to_civitai_url.py           # LoRA to Civitai URLノードの実装
├── civitai_lora_searcher.py         # Civitai LoRA Searcherノードの実装
├── embedding_wildcard_generator.py  # Embedding Wildcard Generatorノードの実装
├── embedding_path_resolver.py       # Embedding Path Resolverノードの実装
├── extract_prompt_from_image.py     # Extract Prompt from Imageノードの実装
├── prompt_extractor_posneg.py       # A1111 Prompt Splitterノードの実装
├── text_split_3.py                  # Text Split 3ノードの実装
├── repeat_text_lines.py             # Repeat Text Linesノードの実装
├── input_path_node.py               # Get ComfyUI Input Pathノードの実装
├── lora_text_dual_input.py          # LoRA Text Dual Inputノードの実装
├── lora_tag_power_loader_extended.py # LoRA Tag Power Loader Extendedノードの実装
├── seed_step_n.py                   # Seed Step Nノードの実装
├── sd_prompt_saver_optimized.py     # SD Prompt Saver (Optimized)ノードの実装
├── .env.example                     # Civitai API用の環境変数テンプレート
├── .env                             # 実際の環境変数（gitには含まれません）
├── .gitignore                       # Git ignoreルール（.envを除外）
├── requirements.txt                 # Python依存関係
├── README.md                        # このドキュメントファイル
├── web/                             # フロントエンドJavaScript
│   └── seed_step_n.js               # Seed Step N UI拡張
└── wildcards/                       # ワイルドカード例フォルダ
    └── clothing.yaml                # 衣服ワイルドカード例
```

---

## 必要要件

### システム要件

- **Python**: 3.8以上
- **ComfyUI**: 最新版を推奨

### Python依存関係

以下のパッケージが `requirements.txt` 経由でインストールされます：

- **requests** (≥2.31.0): Civitaiダウンロード用のHTTPライブラリ
- **python-dotenv** (≥1.0.0): APIキー用の環境変数管理
- **pyyaml** (≥6.0): ワイルドカード生成用のYAMLファイル処理
- **Pillow** (≥9.0.0): 画像処理とメタデータ抽出

すべての依存関係をインストール：
```bash
pip install -r requirements.txt
```

---

## コントリビューション

コントリビューションを歓迎します！イシューやプルリクエストをお気軽に送信してください。

---

## ライセンス

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## サポート

問題、質問、機能リクエストについては、GitHubリポジトリでイシューを開いてください。

**便利なリンク：**
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- [Civitai](https://civitai.com/)
- [Civitai API Documentation](https://github.com/civitai/civitai/wiki/REST-API-Reference)
