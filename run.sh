#!/bin/bash
set -e

echo "Running text redaction..."
python3 redact_text.py

echo "Running image redaction..."
python3 redact_images.py

echo "Redaction process completed successfully!"
