# Shroud: PDF Redaction

These scripts perform **text and image redaction** on PDFs using AI-powered text detection and PyMuPDF. It consists of two python scripts:
1. `redact_text.py`: Redacts sensitive text based on predefined specifications.
2. `redact_images.py`: Redacts sensitive entities found in images within the PDF.

---

## Features

- **Text Redaction**: Detects and redacts text based on a customizable list of terms or phrases.
- **Image Redaction**: Extracts images, uses AI (GPT-4 Vision) to identify sensitive entities, and redacts the images.

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
For Intel Mac users,

OR

```python
os.environ["TESSDATA_PREFIX"] = "/opt/local/share/tessdata"
os.environ["TESSERACT_CMD"] = "/opt/local/bin/tesseract"
```
for Apple Silicon Mac users.

If you are on **Linux** or **Windows**, update these values:

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
Run the shell script with the appropriate arguments:

For **text-only redaction** (default):
```bash
bash run.sh text
```
For **text and image redaction**:
```bash
bash run.sh text image
```
If necessary, make the script executable before running:
`chmod +x run.sh`

**Folder Structure After Running:**
```bash
./input_pdfs/                # Original PDFs
./output_pdfs/               # Fully redacted PDFs
./partially_redacted_pdfs/   # Text-redacted PDFs (used for images)
```

---