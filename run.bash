set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running text redaction..."
python3 redact_text.py

echo "Running image redaction..."
python3 redact_images.py