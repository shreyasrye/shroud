import os
import pymupdf
import json
from openai import OpenAI

def load_redaction_specs(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()

def redact_pdf(input_folder, output_folder, redaction_specs):
    for pdf_file in os.listdir(input_folder):
        if pdf_file.endswith(".pdf"):
            process_pdf(os.path.join(input_folder, pdf_file), output_folder, redaction_specs)

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

        page_data = page.get_text("dict")
        bounding_boxes = []
        for block in page_data["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    bounding_boxes.append({
                        "text": span["text"].strip(),
                        "bounding_box": span["bbox"]
                    })

        for word in redacted_words["redactions"]:
            print(f"Checking word: {word}")
            for box in bounding_boxes:
                if word in box["text"]:
                    print(f"Matched '{word}' in text: {box['text']}")
                    print(f"Bounding box: {box['bounding_box']}")
                    rect = pymupdf.Rect(*box["bounding_box"])
                    page.add_redact_annot(rect, fill=(0, 0, 0))
                    
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
