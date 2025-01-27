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

*