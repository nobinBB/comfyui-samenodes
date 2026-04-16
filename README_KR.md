# ComfyUI Same Nodes

**Languages / 言語 / 语言 / 언어:**  
🇯🇵 [日本語](README.md) | 🇺🇸 [English](README_EN.md) | 🇨🇳 [简体中文](README_CN.md) | 🇰🇷 [한국어](README_KR.md)

---

문자열 변환, 배치 처리, LoRA 관리 및 자동 다운로드를 위한 필수 유틸리티를 제공하는 ComfyUI 커스텀 노드 모음입니다.

## 개요

이 커스텀 노드 팩은 ComfyUI 사용자를 위한 필수 도구를 제공합니다:

### 텍스트 처리
- **Float to String**: 소수점 제어를 통한 정밀한 부동소수점-문자열 변환
- **Text Split 3**: 텍스트를 3개 출력으로 분할 (`<!...!>` 및 `<#...#>` 구분자 지원)
- **Repeat Text Lines**: 지정된 횟수만큼 텍스트 반복

### 이미지 및 프롬프트 처리
- **Batch Image Processor**: 효율적인 배치 이미지 처리
- **Batch Image Compressor**: 대량 이미지 압축 (PNG: 60-80% 감소, JPEG 최적화)
- **Image Format Converter**: 대량 이미지 포맷 변환 (PNG/JPEG/WebP/BMP/TIFF)
- **Images to PDF**: 여러 이미지를 단일 PDF로 변환
- **Extract Prompt from Image**: 이미지 메타데이터에서 프롬프트 추출 (ComfyUI 형식)
- **A1111 Prompt Splitter**: A1111/SD WebUI 이미지에서 긍정/부정 프롬프트 추출
- **SD Prompt Saver (Optimized)**: A1111 호환 메타데이터 + 무손실 압축 (PNG/WebP/JPEG, 20-50% 감소)

### LoRA 관리
- **LoRA Wildcard Generator**: Civitai 메타데이터에서 YAML 와일드카드 자동 생성
- **Civitai LoRA Searcher**: SHA256으로 Civitai API 검색 (대량 JSON 폴더 처리)
- **LoRA to Civitai URL**: LoRA 구문에서 Civitai URL 가져오기

### Embedding 관리
- **Embedding Wildcard Generator**: Embedding 파일에서 YAML 와일드카드 자동 생성
- **Embedding Path Resolver**: `embedding:name`을 `embedding:path/name`으로 자동 변환

### 유틸리티
- **Get ComfyUI Input Path**: ComfyUI 입력 디렉토리 경로 가져오기
- **Seed Step N**: N 단계마다 시드 증가 (영구 카운터, 독립 인스턴스)

---

## 설치

### 단계 1: 저장소 복제

ComfyUI의 `custom_nodes` 폴더로 이동하여 이 저장소를 복제합니다:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/nobinBB/comfyui-samenodes.git
```

### 단계 2: 종속성 설치

필요한 Python 패키지를 설치합니다:

```bash
cd comfyui-samenodes
pip install -r requirements.txt
```

### 단계 3: ComfyUI 재시작

새 노드를 로드하려면 ComfyUI를 재시작합니다.

---

## 주요 노드: SD Prompt Saver (Optimized)

### 하이브리드 압축 (외부 도구 + Pillow 폴백)

**외부 도구로 최대 압축 작동, 도구가 설치되지 않은 경우 Pillow로 폴백합니다.**

| 포맷 | 외부 도구 (고압축) | Pillow 폴백 | 압축률 |
|--------|----------------------------------|-----------------|------------------|
| PNG | **pngquant 85-95 + oxipng** | compress_level=9 | **35-50%** → 10-25% |
| WebP | cwebp -lossless | lossless mode | 20-40% → 5-20% |
| JPEG | jpegtran | optimize + progressive | 3-15% → 5-15% |

**PNG 2단계 압축:**
1. pngquant (품질 85-95): 시각적 무손실, 30-40% 감소
2. oxipng (-o 6): 완전 무손실 추가 최적화, 5-10% 추가 감소
3. **총계: 35-50% 감소, 95% 시각적 품질 유지**

### 외부 도구 설치 (선택 사항)

#### **권장 방법: 로컬 `tools` 폴더**

1. **tools 폴더 생성:**
   ```
   ComfyUI/custom_nodes/comfyui-samenodes/tools/
   ```

2. **바이너리 다운로드 및 배치:**
   - **pngquant**: https://pngquant.org/
   - **oxipng**: https://github.com/shssoichiro/oxipng/releases
   - **cwebp**: https://developers.google.com/speed/webp/download
   - **jpegtran**: https://jpegclub.org/jpegtran/

3. **폴더 구조:**
   ```
   tools/
   ├── pngquant.exe    # Windows
   ├── oxipng.exe      # Windows
   ├── cwebp.exe       # Windows
   └── jpegtran.exe    # Windows
   ```

4. **ComfyUI 재시작**

**참고:** 노드는 `./tools/` 폴더 → 시스템 PATH 순으로 우선합니다. 관리자 권한이나 시스템 PATH 설정이 필요하지 않습니다.

#### **대안: 시스템 설치**

**Mac:**
```bash
brew install pngquant oxipng webp jpeg-turbo
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install pngquant oxipng webp libjpeg-turbo-progs
```

**Linux (Fedora):**
```bash
sudo dnf install pngquant oxipng libwebp-tools libjpeg-turbo-utils
```

### 압축 예제

**외부 도구 사용 (PNG → pngquant + oxipng):**
```
[SDPromptSaverOptimized] saved: D:/output/2026-04-15/ComfyUI_153022_1234567_0001.png
[SDPromptSaverOptimized] PNG (pngquant 85-95): 2,453,120 B → 1,471,872 B (-40.0%)
[SDPromptSaverOptimized] PNG (oxipng): 1,471,872 B → 1,324,685 B (-10.0%)
[SDPromptSaverOptimized] PNG Total (pngquant+oxipng): 2,453,120 B → 1,324,685 B (-46.0%)
============================================================
```

**외부 도구 미사용 (PNG → Pillow):**
```
[SDPromptSaverOptimized] saved: D:/output/2026-04-15/ComfyUI_153022_1234567_0001.png
[SDPromptSaverOptimized] PNG (Pillow): 2,453,120 B → 2,103,552 B (-14.2%)
```

---

## 요구 사항

### 시스템 요구 사항
- **Python**: 3.8 이상
- **ComfyUI**: 최신 버전 권장

### Python 종속성

`requirements.txt`를 통해 설치:
- **requests** (≥2.31.0): Civitai 다운로드를 위한 HTTP 라이브러리
- **python-dotenv** (≥1.0.0): API 키를 위한 환경 변수 관리
- **pyyaml** (≥6.0): 와일드카드 생성을 위한 YAML 파일 처리
- **Pillow** (≥9.0.0): 이미지 처리 및 메타데이터 추출
- **piexif** (≥1.1.3): JPEG/WebP EXIF 메타데이터

모든 종속성 설치:
```bash
pip install -r requirements.txt
```

---

## 라이선스

MIT License

Copyright (c) 2024 nobinBB

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

### 파생 및 수정 컴포넌트 귀속

이 프로젝트에는 다음 오픈 소스 프로젝트를 기반으로 한 컴포넌트가 포함되어 있습니다:

#### 1. SD Prompt Saver (Optimized)
- **원본 프로젝트:** [receyuki/comfyui-prompt-reader-node](https://github.com/receyuki/comfyui-prompt-reader-node)
- **원본 저작권:** Copyright (c) 2023 receyuki
- **수정 저작권:** Copyright (c) 2024 nobinBB
- **라이선스:** MIT License
- **파일:** `sd_prompt_saver_optimized.py`
- **주요 변경 사항:**
  - PNG/WebP/JPEG 전체 포맷 지원
  - 하이브리드 압축 (pngquant 85-95 + oxipng, cwebp, jpegtran)
  - 로컬 tools 폴더 지원
  - 35-50% 압축률 (PNG)

#### 2. LoRA Tag Power Loader Extended
- **원본 프로젝트:** LoRA Tag Power Loader
- **수정 저작권:** Copyright (c) 2024 nobinBB
- **라이선스:** MIT License
- **파일:** `lora_tag_power_loader_extended.py`
- **주요 변경 사항:**
  - second_text 입력/출력 추가
  - 원본 기능 완전 보존

#### 3. Text Split 3
- **개념 출처:** NegativeWildcardsProcessor
- **구현 저작권:** Copyright (c) 2024 nobinBB
- **라이선스:** MIT License
- **파일:** `text_split_3.py`
- **설명:** NegativeWildcardsProcessor 개념에서 영감을 받은 독창적인 구현

---

### 기타 컴포넌트

다른 모든 노드(Float to String, Batch Image Compressor, LoRA Wildcard Generator 등)는 nobinBB의 완전한 독창적인 구현입니다.

```
Copyright (c) 2024 nobinBB
License: MIT
```

---

## 지원

문제, 질문 또는 기능 요청이 있는 경우 GitHub 저장소에 이슈를 열어주세요.

**유용한 링크:**
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- [Civitai](https://civitai.com/)
