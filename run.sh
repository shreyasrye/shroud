#!/bin/bash
set -e

echo "Running Redaction..."
python3 redact_text.py

echo "Saving changes to files..."
sync

echo "Redaction process completed successfully!"
