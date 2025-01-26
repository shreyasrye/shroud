#!/bin/bash
set -e

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "Setting up the project..."

if ! command_exists python3; then
    echo "Python3 is not installed. Please install Python3 and try again."
    exit 1
fi

if ! command_exists pip; then
    echo "pip is not installed. Installing pip..."
    python3 -m ensurepip --upgrade
fi

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Creating necessary folders..."
mkdir -p input_pdfs
mkdir -p partially_redacted_pdfs
mkdir -p output_pdfs
mkdir -p logs

echo "Folders created: input_pdfs/, partially_redacted_pdfs/, output_pdfs/, logs/"

echo "Running text redaction..."
python3 redact_text.py

echo "Running image redaction..."
python3 redact_images.py

echo "Redaction process completed successfully!"
