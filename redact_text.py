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

def redact_pdf(input_folder, intermediate_folder, output_folder, redaction_specs):
    """Redact text in PDF files based on specifications."""
    pdf_files = [f for f in os.listdir(input_folder) if f.endswith(".pdf")]
    for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
        intermediate_path = process_pdf(os.path.join(input_folder, pdf_file), intermediate_folder, redaction_specs)
        tqdm.write(f"Reprocessing: {intermediate_path}")
        process_pdf(intermediate_path, output_folder, redaction_specs)

def chunk_text_sliding_window(text, max_chunk_size=10):
    """
    Breaks a sentence into overlapping chunks while preserving word order.
    """
    words = text.split()  # Split phrase into words
    if len(words) <= max_chunk_size:
        return [text]  # If phrase is short, return as-is

    chunks = []
    for i in range(0, len(words), max_chunk_size // 2):
        chunk = " ".join(words[i:i + max_chunk_size])
        chunks.append(chunk)
        if i + max_chunk_size >= len(words):\
            break

    return chunks

def bound_phrase(page, phrase):
    """
    Searches for a phrase in a PDF page by breaking it into overlapping chunks.
    """
    normalized_phrase = phrase.replace("“", '"').replace("”", '"')
    chunks = chunk_text_sliding_window(normalized_phrase)

    all_bboxes = []
    
    for chunk in chunks:
        bboxes = page.search_for(chunk)
        if bboxes:
            all_bboxes.extend(bboxes)

    if all_bboxes:
        for bbox in all_bboxes:
            page.add_redact_annot(bbox, fill=(0, 0, 0))
        return all_bboxes
    else:
        logger.warning(f"Phrase '{phrase}' could not be found on the page.")
    return None

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
            bound_phrase(page, redacted_word)

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

    with open(SPEC_FILE, 'r') as file:
        specs = file.read().strip()

    redact_pdf(INPUT_FOLDER, PARTIALLY_REDACTED_FOLDER, OUTPUT_FOLDER, specs)

    tqdm.write("Redaction completed.")
