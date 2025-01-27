import os
import pymupdf
import json
from openai import OpenAI
from tqdm import tqdm
import logging
from datetime import datetime

if not os.path.exists("logs"):
    os.makedirs("logs")
log_filename = f"logs/redact_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

def load_redaction_specs(file_path):
    """Load redaction specifications from a file."""
    with open(file_path, 'r') as file:
        return file.read().strip()

def redact_pdf(input_folder, intermediate_folder, output_folder, redaction_specs):
    """Redact text in PDF files based on specifications."""
    pdf_files = [f for f in os.listdir(input_folder) if f.endswith(".pdf")]
    for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
        intermediate_path = process_pdf(os.path.join(input_folder, pdf_file), intermediate_folder, redaction_specs)
        tqdm.write(f"Reprocessing: {intermediate_path}")
        process_pdf(intermediate_path, output_folder, redaction_specs)

def get_words_in_span(page, span_bbox, words_of_interest=None):
    """Get words within a specific bounding box on a PDF page."""
    words = page.get_text("words")
    span_words = []

    for word in words:
        word_bbox = pymupdf.Rect(word[:4])
        if span_bbox.intersects(word_bbox):
            if words_of_interest is None or word[4].strip(',"!;') in words_of_interest:
                span_words.append({
                    "word": word[4], 
                    "bbox": word_bbox
                })
    return span_words

def combine_word_bboxes(word_bboxes):
    """Combine multiple word bounding boxes into one."""
    if not word_bboxes:
        return None 

    x0 = min(bbox[0] for bbox in word_bboxes)
    y0 = min(bbox[1] for bbox in word_bboxes)
    x1 = max(bbox[2] for bbox in word_bboxes)
    y1 = max(bbox[3] for bbox in word_bboxes) 

    return pymupdf.Rect(x0, y0, x1, y1)

def specific_granularity_bounding(page, word):
    """Redact a specific word on a PDF page."""
    word_bounding_boxes = page.get_text("words")
    for word_tup in word_bounding_boxes:
        if word in word_tup[4]:
            logger.info(f"Redacting word: '{word}' found in bounding box: {word_tup[:4]}")
            rect = pymupdf.Rect(word_tup[0], word_tup[1], word_tup[2], word_tup[3])
            page.add_redact_annot(rect, fill=(0, 0, 0))

def generic_granularity_bounding(page, phrase):
    """Redact a phrase on a PDF page."""
    text_dict = page.get_text("dict")
    spans_with_positions = []
    reconstructed_text = ""

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
                reconstructed_text += span_text + " "

    reconstructed_text = reconstructed_text.replace("  ", " ")
    start_idx = reconstructed_text.find(phrase)

    if start_idx != -1:
        end_idx = start_idx + len(phrase)
        phrase_bboxes = []
        logger.info(f"Phrase '{phrase}' found on the page at position: ({start_idx}, {end_idx})")

        for span in spans_with_positions:
            if span["start"] < end_idx and span["end"] > start_idx:
                phrase_bboxes.append(span["bbox"])
                logger.info(f"Phrase '{phrase}' overlaps with span: '{reconstructed_text[span['start']:span['end']]}'")

        if phrase_bboxes:
            if len(phrase_bboxes) == 1:
                for bbox in phrase_bboxes:
                    try:
                        words_of_interest = phrase.split()
                        span_word_dict = get_words_in_span(page, pymupdf.Rect(bbox), words_of_interest)
                        final_bbox = combine_word_bboxes([word["bbox"] for word in span_word_dict])
                        if final_bbox:
                            rect = pymupdf.Rect(final_bbox)
                            page.add_redact_annot(rect, fill=(0, 0, 0))
                            logger.info(f"Redacting phrase: '{phrase}' with bounding box: {final_bbox}")
                        else:
                            logger.warning(f"No bounding box found for phrase: '{phrase}'")
                    except Exception as e:
                        logger.error(f"Error processing phrase '{phrase}': {e}")
            else:
                try:
                    x0 = min(bbox[0] for bbox in phrase_bboxes)
                    y0 = min(bbox[1] for bbox in phrase_bboxes)
                    x1 = max(bbox[2] for bbox in phrase_bboxes)
                    y1 = max(bbox[3] for bbox in phrase_bboxes)
                    final_bbox = (x0, y0, x1, y1)

                    rect = pymupdf.Rect(final_bbox)
                    page.add_redact_annot(rect, fill=(0, 0, 0))
                    logger.info(f"Redacting phrase: '{phrase}' with bounding box: {final_bbox}")
                except ValueError as e:
                    logger.error(f"No bounds found for{phrase}': {e}")
    else:
        logger.info(f"Phrase '{phrase}' not found on the page.")

def process_pdf(file_path, output_folder, redaction_specs):
    """Process a PDF file and apply redactions based on specifications."""
    doc = pymupdf.open(file_path)
    try:
        with open("config.json") as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        tqdm.write("Config file not found.")
        logger.error("Config file not found.")
        return
    client = OpenAI(api_key=config["openai"]["api_key"])
    for page_num, page in enumerate(tqdm(doc, desc="Processing Pages")):
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
        logger.info(f"\n_____________________________")
        logger.info(f"| PAGE {page_num + 1} REDACTION RESULTS |")
        logger.info(f"_____________________________\n")
        logger.info(f"Text to be redacted for page {page_num + 1}: {redacted_word_list}\n")
        
        for redacted_word in redacted_word_list:
            if " " not in redacted_word:
                specific_granularity_bounding(page, redacted_word)
            else:
                generic_granularity_bounding(page, redacted_word)
        tqdm.write(f"Applied redactions on page {page_num + 1}")      
        page.apply_redactions()
    
    output_path = os.path.join(output_folder, os.path.basename(file_path))
    doc.save(output_path, deflate=True)
    doc.close()
    tqdm.write(f"Processed and saved: {output_path}")
    return output_path

if __name__ == "__main__":
    INPUT_FOLDER = "./input_pdfs" 
    PARTIALLY_REDACTED_FOLDER = "./partially_redacted_pdfs"
    OUTPUT_FOLDER = "./output_pdfs"
    SPEC_FILE = "./entities_to_redact.txt" 
    PROMPT_FILE = "./prompts/redaction_prompt.txt"

    if not os.path.exists(PARTIALLY_REDACTED_FOLDER):
        os.makedirs(PARTIALLY_REDACTED_FOLDER)

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    specs = load_redaction_specs(SPEC_FILE)

    redact_pdf(INPUT_FOLDER, PARTIALLY_REDACTED_FOLDER, OUTPUT_FOLDER, specs)

    tqdm.write("Redaction completed.")
