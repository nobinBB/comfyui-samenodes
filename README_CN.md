# ComfyUI Same Nodes

**Languages / 言語 / 语言 / 언어:**  
🇯🇵 [日本語](README.md) | 🇺🇸 [English](README_EN.md) | 🇨🇳 [简体中文](README_CN.md) | 🇰🇷 [한국어](README_KR.md)

---

ComfyUI 自定义节点集合，提供字符串转换、批处理、LoRA 管理和自动下载等基本功能，增强您的工作流程。

## 概述

此自定义节点包为 ComfyUI 用户提供必要工具：

### 文本处理
- **Float to String**：精确浮点数转字符串（支持小数位控制）
- **Text Split 3**：文本分割为 3 个输出（支持 `<!...!>` 和 `<#...#>` 分隔符）
- **Repeat Text Lines**：重复文本指定次数

### 图像和提示词处理
- **Batch Image Processor**：高效批量图像处理
- **Batch Image Compressor**：批量图像压缩（PNG: 60-80% 缩减，JPEG 优化）
- **Image Format Converter**：批量图像格式转换（PNG/JPEG/WebP/BMP/TIFF）
- **Images to PDF**：多图像转单个 PDF
- **Extract Prompt from Image**：从图像元数据提取提示词（ComfyUI 格式）
- **A1111 Prompt Splitter**：从 A1111/SD WebUI 图像提取正负提示词
- **SD Prompt Saver (Optimized)**：A1111 兼容元数据 + 无损压缩（PNG/WebP/JPEG，20-50% 缩减）

### LoRA 管理
- **LoRA Wildcard Generator**：从 Civitai 元数据自动生成 YAML 通配符
- **Civitai LoRA Searcher**：通过 SHA256 搜索 Civitai API（批量 JSON 文件夹处理）
- **LoRA to Civitai URL**：从 LoRA 语法获取 Civitai URL

### Embedding 管理
- **Embedding Wildcard Generator**：从 Embedding 文件自动生成 YAML 通配符
- **Embedding Path Resolver**：自动解析 `embedding:name` 为 `embedding:path/name`

### 实用工具
- **Get ComfyUI Input Path**：获取 ComfyUI 输入目录路径
- **Seed Step N**：每 N 步递增种子（持久计数器，独立实例）

---

## 安装

### 步骤 1：克隆仓库

导航到 ComfyUI 的 `custom_nodes` 文件夹并克隆此仓库：

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/nobinBB/comfyui-samenodes.git
```

### 步骤 2：安装依赖

安装所需的 Python 包：

```bash
cd comfyui-samenodes
pip install -r requirements.txt
```

### 步骤 3：重启 ComfyUI

重启 ComfyUI 以加载新节点。

---

## 特色节点：SD Prompt Saver (Optimized)

### 混合压缩（外部工具 + Pillow 后备）

**使用外部工具实现最大压缩，若工具未安装则回退到 Pillow。**

| 格式 | 外部工具（高压缩） | Pillow 后备 | 压缩率 |
|--------|----------------------------------|-----------------|------------------|
| PNG | **pngquant 85-95 + oxipng** | compress_level=9 | **35-50%** → 10-25% |
| WebP | cwebp -lossless | lossless mode | 20-40% → 5-20% |
| JPEG | jpegtran | optimize + progressive | 3-15% → 5-15% |

**PNG 两阶段压缩：**
1. pngquant（质量 85-95）：视觉无损，30-40% 缩减
2. oxipng（-o 6）：完全无损额外优化，5-10% 额外缩减
3. **总计：35-50% 缩减，保持 95% 视觉质量**

### 外部工具安装（可选）

#### **推荐方法：本地 `tools` 文件夹**

1. **创建 tools 文件夹：**
   ```
   ComfyUI/custom_nodes/comfyui-samenodes/tools/
   ```

2. **下载并放置二进制文件：**
   - **pngquant**：https://pngquant.org/
   - **oxipng**：https://github.com/shssoichiro/oxipng/releases
   - **cwebp**：https://developers.google.com/speed/webp/download
   - **jpegtran**：https://jpegclub.org/jpegtran/

3. **文件夹结构：**
   ```
   tools/
   ├── pngquant.exe    # Windows
   ├── oxipng.exe      # Windows
   ├── cwebp.exe       # Windows
   └── jpegtran.exe    # Windows
   ```

4. **重启 ComfyUI**

**注意：** 节点优先使用 `./tools/` 文件夹 → 系统 PATH。无需管理员权限或系统 PATH 设置。

#### **替代方法：系统安装**

**Mac：**
```bash
brew install pngquant oxipng webp jpeg-turbo
```

**Linux（Debian/Ubuntu）：**
```bash
sudo apt install pngquant oxipng webp libjpeg-turbo-progs
```

**Linux（Fedora）：**
```bash
sudo dnf install pngquant oxipng libwebp-tools libjpeg-turbo-utils
```

### 压缩示例

**使用外部工具（PNG → pngquant + oxipng）：**
```
[SDPromptSaverOptimized] saved: D:/output/2026-04-15/ComfyUI_153022_1234567_0001.png
[SDPromptSaverOptimized] PNG (pngquant 85-95): 2,453,120 B → 1,471,872 B (-40.0%)
[SDPromptSaverOptimized] PNG (oxipng): 1,471,872 B → 1,324,685 B (-10.0%)
[SDPromptSaverOptimized] PNG Total (pngquant+oxipng): 2,453,120 B → 1,324,685 B (-46.0%)
============================================================
```

**不使用外部工具（PNG → Pillow）：**
```
[SDPromptSaverOptimized] saved: D:/output/2026-04-15/ComfyUI_153022_1234567_0001.png
[SDPromptSaverOptimized] PNG (Pillow): 2,453,120 B → 2,103,552 B (-14.2%)
```

---

## 系统要求

### 系统要求
- **Python**：3.8 或更高版本
- **ComfyUI**：建议使用最新版本

### Python 依赖

通过 `requirements.txt` 安装：
- **requests**（≥2.31.0）：用于 Civitai 下载的 HTTP 库
- **python-dotenv**（≥1.0.0）：API 密钥的环境变量管理
- **pyyaml**（≥6.0）：通配符生成的 YAML 文件处理
- **Pillow**（≥9.0.0）：图像处理和元数据提取
- **piexif**（≥1.1.3）：JPEG/WebP 的 EXIF 元数据

安装所有依赖：
```bash
pip install -r requirements.txt
```

---

## 许可证

MIT License

Copyright (c) 2024 nobinBB

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

### 派生和修改组件归属

本项目包含基于以下开源项目的组件：

#### 1. SD Prompt Saver (Optimized)
- **原始项目：** [receyuki/comfyui-prompt-reader-node](https://github.com/receyuki/comfyui-prompt-reader-node)
- **原始版权：** Copyright (c) 2023 receyuki
- **修改版权：** Copyright (c) 2024 nobinBB
- **许可证：** MIT License
- **文件：** `sd_prompt_saver_optimized.py`
- **主要变更：**
  - PNG/WebP/JPEG 完整格式支持
  - 混合压缩（pngquant 85-95 + oxipng、cwebp、jpegtran）
  - 本地 tools 文件夹支持
  - 35-50% 压缩率（PNG）

#### 2. LoRA Tag Power Loader Extended
- **原始项目：** LoRA Tag Power Loader
- **修改版权：** Copyright (c) 2024 nobinBB
- **许可证：** MIT License
- **文件：** `lora_tag_power_loader_extended.py`
- **主要变更：**
  - 添加了 second_text 输入/输出
  - 完全保留原始功能

#### 3. Text Split 3
- **概念来源：** NegativeWildcardsProcessor
- **实现版权：** Copyright (c) 2024 nobinBB
- **许可证：** MIT License
- **文件：** `text_split_3.py`
- **描述：** 受 NegativeWildcardsProcessor 概念启发的原创实现

---

### 其他组件

所有其他节点（Float to String、Batch Image Compressor、LoRA Wildcard Generator 等）均为 nobinBB 的完全原创实现。

```
Copyright (c) 2024 nobinBB
License: MIT
```

---

## 支持

如有问题、疑问或功能请求，请在 GitHub 仓库上提交 issue。

**有用链接：**
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- [Civitai](https://civitai.com/)
