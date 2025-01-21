import os
import pymupdf
import json
from openai import OpenAI
from difflib import SequenceMatcher as SM

def load_redaction_specs(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()

def redact_pdf(input_folder, output_folder, redaction_specs):
    for pdf_file in os.listdir(input_folder):
        if pdf_file.endswith(".pdf"):
            process_pdf(os.path.join(input_folder, pdf_file), output_folder, redaction_specs)

def extract_bounding_boxes(page):
    bounding_boxes = []
    page_data = page.get_text("dict")
    for block in page_data["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                bounding_boxes.append({
                    "text": span["text"],
                    "bounding_box": span["bbox"]
                })
    return bounding_boxes

def apply_word_level_redactions(page, redacted_word_list):
    """
    Apply word-level redactions using 'words' data from the page.
    """
    word_bounding_boxes = page.get_text("words")
    for redacted_word in redacted_word_list:
        for word_tup in word_bounding_boxes:
            if redacted_word in word_tup[4]:
                print(f"Redacting word: {redacted_word} found in {word_tup[:4]}")
                rect = pymupdf.Rect(word_tup[0], word_tup[1], word_tup[2], word_tup[3])
                page.add_redact_annot(rect, fill=(0, 0, 0))

def apply_span_level_redactions(page, phrases):
    """
    Apply span-level redactions by matching redacted words to spans.
    """
    text_dict = page.get_text("dict")
    spans_with_positions = []
    reconstructed_text = ""

    # Collect spans and maintain position tracking
    for block in text_dict["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                span_start = len(reconstructed_text)
                span_text = span["text"]
                span_end = span_start + len(span_text)
                spans_with_positions.append({
                    "start": span_start,
                    "end": span_end,
                    "bbox": span["bbox"],
                })
                reconstructed_text += span_text + " "  # Add space for separation

    print(f"Reconstructed text: {reconstructed_text}")

    # Iterate through phrases
    for phrase in phrases:
        start_idx = reconstructed_text.find(phrase)
        if start_idx != -1:
            end_idx = start_idx + len(phrase)
            phrase_bboxes = []

            # Match spans that overlap with the phrase
            for span in spans_with_positions:
                if span["start"] < end_idx and span["end"] > start_idx:
                    phrase_bboxes.append(span["bbox"])
                    print(f"Phrase '{phrase}' overlaps with span: '{reconstructed_text[span['start']:span['end']]}'")

            # Combine bounding boxes
            if phrase_bboxes:
                x0 = min(bbox[0] for bbox in phrase_bboxes)
                y0 = min(bbox[1] for bbox in phrase_bboxes)
                x1 = max(bbox[2] for bbox in phrase_bboxes)
                y1 = max(bbox[3] for bbox in phrase_bboxes)

                # Apply redaction
                rect = pymupdf.Rect(x0, y0, x1, y1)
                page.add_redact_annot(rect, fill=(0, 0, 0))
                print(f"Redacting phrase: '{phrase}' with bbox: ({x0}, {y0}, {x1}, {y1})")
        else:
            print(f"Phrase '{phrase}' not found on the page.")


def process_pdf(file_path, output_folder, redaction_specs):
    doc = pymupdf.open(file_path)
    with open("config.json") as config_file:
        config = json.load(config_file)
    client = OpenAI(api_key=config["openai"]["api_key"])
    
    for page_num, page in enumerate(doc):
        page_text = page.get_text("text")
        
        with open(PROMPT_FILE) as prompt_file:
            prompt_template = prompt_file.read()

        prompt = prompt_template.format(
            page_text=page_text,
            redaction_specs=redaction_specs
        )
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a PDF redaction assistant. Your task is to adaptively redact text based on "
                        "the Redaction Specifications. You must follow the instructions strictly and return "
                        "results only in the required JSON format."
                    )
                },
                {"role": "user", "content": prompt},
            ],
            response_format={ "type": "json_object" },
            temperature=0.0
        )

        redacted_words = json.loads(response.choices[0].message.content)
        redacted_word_list = redacted_words["redactions"]
        print(f"Text to be redacted for page {page_num + 1}: {redacted_word_list}")

        if redacted_words["granularity"] == "specific":
            print(f"Applying word-level redactions on page {page_num + 1}")
            apply_word_level_redactions(page, redacted_word_list)
        elif redacted_words["granularity"] == "general":
            # print(f"Extracting bounding boxes for span-level redactions on page {page_num + 1}")
            # bounding_boxes = extract_bounding_boxes(page)
            print(f"Applying span-level redactions on page {page_num + 1}")
            apply_span_level_redactions(page, redacted_word_list)
                    
        page.apply_redactions()
    
    output_path = os.path.join(output_folder, os.path.basename(file_path))
    doc.save(output_path, deflate=True)
    doc.close()
    print(f"Processed and saved: {output_path}")

if __name__ == "__main__":
    INPUT_FOLDER = "./input_pdfs" 
    OUTPUT_FOLDER = "./output_pdfs"  
    SPEC_FILE = "./entities_to_redact.txt" 
    PROMPT_FILE = "./redaction_prompt.txt"

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    specs = load_redaction_specs(SPEC_FILE)

    redact_pdf(INPUT_FOLDER, OUTPUT_FOLDER, specs)

    print("Redaction completed.")
