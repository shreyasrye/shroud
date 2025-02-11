# Shroud: PDF Redaction

These scripts perform **text and image redaction** on PDFs using AI-powered text detection and PyMuPDF. It consists of two python scripts:
1. `redact_text.py`: Redacts sensitive text based on predefined specifications.
2. `redact_images.py`: Redacts sensitive text found in images within the PDF.

---

## Features

- **Text Redaction**: Detects and redacts text based on a customizable list of terms or phrases.
- **Image Redaction**: Extracts images, uses AI (GPT-4 Vision) to identify sensitive text, and redacts the images.

---

## Prerequisites

Ensure you have the following installed:
- Python 3.8 or higher
- pip (Python package manager)
- [**Tesseract OCR**](https://github.com/tesseract-ocr/tesseract): Required for redacting text from images and flat PDFs.

To insall the required packages, run:

`./install.sh`

If necessary, make the script executable before running:

`chmod +x install.sh`

---

## Tesseract Configuration
Shroud requires **Tesseract’s trained models (`tessdata`)**.  
By default, the script is configured for **macOS**, using:

```python
os.environ["TESSDATA_PREFIX"] = "/usr/local/share/tessdata"
os.environ["TESSERACT_CMD"] = "/usr/local/bin/tesseract"
```

If you are on **Linux** or **Windows**, update these values accordingly:

* **Linux:** `/usr/share/tesseract-ocr/5/tessdata`
* **Windows:** `C:\Program Files\Tesseract-OCR\tessdata`

To manually override, set the environment variables before running the script:

```bash
export TESSDATA_PREFIX="/path/to/tessdata"
export TESSERACT_CMD="/path/to/tesseract"
```
---

## OpenAI key configuration:
The scripts use a config.json file to store your OpenAI API key. To configure your key, create a file named `config.json` in the root directory with the following format:
```json
{
    "openai": {
        "api_key": "openai-api-key"
    }
}
```
---

## Running
Run the shell script:
`run.sh`

If necessary, make the script executable before running:
`chmod +x run.sh`

---