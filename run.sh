#!/bin/bash
set -e

INPUT_FOLDER="./input_pdfs"
OUTPUT_FOLDER="./output_pdfs"
PARTIAL_REDACTED_DIR="./partially_redacted_pdfs"

if [ "$#" -eq 0 ]; then
    RUN_TEXT=true
    RUN_IMAGES=false
elif [ "$#" -eq 1 ] && [ "$1" == "text" ]; then
    RUN_TEXT=true
    RUN_IMAGES=false
elif [ "$#" -eq 1 ] && [ "$1" == "images" ]; then
    echo "Error: 'images' cannot be run alone. Use 'text images' instead."
    exit 1
elif [ "$#" -eq 2 ] && [[ "$1" == "text" && "$2" == "images" ]]; then
    RUN_TEXT=true
    RUN_IMAGES=true
else
    echo "Usage: $0 [text] [images]"
    exit 1
fi

export INPUT_FOLDER
export OUTPUT_FOLDER
export PARTIAL_REDACTED_DIR

if [ "$RUN_TEXT" = true ] && [ "$RUN_IMAGES" = false ]; then
    echo "Running text redaction..."
    python3 redact_text.py "$INPUT_FOLDER" "$OUTPUT_FOLDER"

elif [ "$RUN_TEXT" = true ] && [ "$RUN_IMAGES" = true ]; then
    echo "Ensuring partially redacted folder exists..."
    mkdir -p "$PARTIAL_REDACTED_DIR" 

    echo "Running text redaction (Step 1)..."
    python3 redact_text.py "$INPUT_FOLDER" "$PARTIAL_REDACTED_DIR"

    echo "Running image redaction (Step 2)..."
    python3 redact_images.py "$PARTIAL_REDACTED_DIR" "$OUTPUT_FOLDER"
fi

echo "Saving changes to files..."
sync

echo "Redaction process completed successfully!"
