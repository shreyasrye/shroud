#!/bin/bash
set -e

# Set Tesseract environment variables
export TESSDATA_PREFIX="/usr/local/share/tessdata"
export TESSERACT_CMD="/usr/local/bin/tesseract"

echo "Running Redaction..."
python3 redact_text.py

echo "Saving changes to files..."
sync

echo "Redaction process completed successfully!"
