---
name: multimodal-bridge
description: Multi-modal understanding bridge — image analysis, document parsing, audio transcription. Use when: (1) analyzing images/screenshots, (2) extracting text from images, (3) reading PDF documents, (4) processing audio files, (5) understanding visual data. Routes to appropriate tools: OpenClaw read tool for images, Python OCR for text extraction, ffmpeg for audio.
version: "1.0.0"
---

# Multimodal Bridge

Routes multi-modal inputs to appropriate processing pipelines.

## Capabilities

| Input | Processing | Tools |
|-------|-----------|-------|
| PNG/JPG images | Direct view via read tool | Built-in read |
| Screenshots | Analysis + text extraction | read + desktop_auto |
| PDF documents | Text extraction | pdftotext / read |
| Audio files | Speech-to-text | whisper / sherpa-onnx |
| Markdown with images | Inline display | read tool |

## Image Analysis Workflow

```
1. Capture context (what are we looking for?)
2. read the image file → OpenClaw built-in image understanding
3. If text extraction needed → use OCR (tesseract / Python)
4. Combine visual + textual understanding
5. Respond with analysis
```

## Document Processing

```bash
# PDF to text
pdftotext document.pdf - | head -200

# Image OCR (Python PIL + pytesseract)
python3 -c "
from PIL import Image
import pytesseract
print(pytesseract.image_to_string(Image.open('scan.png')))
"
```

## Screenshot Analysis Pipeline

```bash
# 1. Take screenshot
python3 scripts/desktop_auto.py screenshot /tmp/screen.png

# 2. Analyze appearance (read tool)
# 3. Find UI elements (find "Login")
# 4. Interact based on findings
```
