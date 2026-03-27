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
- **Extract Prompt from Image**: 画像メタデータからプロンプトを抽出（ComfyUI形式）
- **A1111 Prompt Splitter**: A1111/SD WebUI画像からポジティブ・ネガティブプロンプトを抽出

### LoRA管理
- **LoRA Wildcard Generator**: Civitaiメタデータから自動的にYAMLワイルドカードを生成
- **Civitai Bulk Downloader**: CivitaiからLoRAモデルをAPI認証付きでバッチダウンロード

### Embedding管理
- **Embedding Wildcard Generator**: Embeddingファイルから自動的にYAMLワイルドカードを生成
- **Embedding Path Resolver**: `embedding:name` を `embedding:path/name` に自動解決

### ユーティリティ
- **Get ComfyUI Input Path**: ComfyUIの入力ディレクトリパスを取得

これらのノードは、特にLoRAモデル、Embedding、ワイルドカード、プロンプト、バッチ操作、パス管理を扱う際に、ComfyUIのワークフローを効率化するよう設計されています。

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

## プロジェクト構造

```
comfyui-samenodes/
├── __init__.py                      # ノードの初期化と登録
├── float_to_string.py               # Float to Stringノードの実装
├── batch_processor.py               # Batch Image Processorノードの実装
├── lora_wildcard_generator.py       # LoRA Wildcard Generatorノードの実装
├── embedding_wildcard_generator.py  # Embedding Wildcard Generatorノードの実装
├── embedding_path_resolver.py       # Embedding Path Resolverノードの実装
├── civitai_bulk_downloader.py       # Civitai Bulk Downloaderノードの実装
├── extract_prompt_from_image.py     # Extract Prompt from Imageノードの実装
├── prompt_extractor_posneg.py       # A1111 Prompt Splitterノードの実装
├── text_split_3.py                  # Text Split 3ノードの実装
├── repeat_text_lines.py             # Repeat Text Linesノードの実装
├── input_path_node.py               # Get ComfyUI Input Pathノードの実装
├── .env.example                     # Civitai API用の環境変数テンプレート
├── .env                             # 実際の環境変数（gitには含まれません）
├── .gitignore                       # Git ignoreルール（.envを除外）
├── requirements.txt                 # Python依存関係
├── README.md                        # このドキュメントファイル
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
